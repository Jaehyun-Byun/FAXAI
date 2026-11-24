# (2026-11-25) @Gomchiiii 가족 생년월일을 저장하고 현재 자녀 나이에 대응하는 부모 시점을 계산하는 API 기능을 정의하는 파일입니다.

import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel, Field, field_validator, model_validator


PROJECT_ROOT = Path(__file__).resolve().parents[3]
FAMILY_DATABASE_PATH = PROJECT_ROOT / "data" / "family.db"

router = APIRouter(prefix="/family", tags=["family"])


class FamilyProfileInput(BaseModel):
    parent_name: str = Field(min_length=1, max_length=100)
    parent_birth_date: date
    child_name: str = Field(min_length=1, max_length=100)
    child_birth_date: date

    @field_validator("parent_name", "child_name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        stripped_value = value.strip()
        if not stripped_value:
            raise ValueError("이름을 입력해 주세요.")
        return stripped_value

    @model_validator(mode="after")
    def validate_birth_dates(self) -> "FamilyProfileInput":
        today = get_today()
        if self.parent_birth_date > today or self.child_birth_date > today:
            raise ValueError("생년월일은 오늘 이후일 수 없습니다.")
        if self.parent_birth_date >= self.child_birth_date:
            raise ValueError("부모 생년월일은 자녀 생년월일보다 앞서야 합니다.")
        return self


class FamilyProfileResponse(FamilyProfileInput):
    child_age: int
    matching_parent_date: date
    updated_at: datetime


def get_today() -> date:
    return date.today()


def calculate_age(birth_date: date, today: date) -> int:
    birthday_has_passed = (today.month, today.day) >= (
        birth_date.month,
        birth_date.day,
    )
    return today.year - birth_date.year - (not birthday_has_passed)


def add_years(value: date, years: int) -> date:
    try:
        return value.replace(year=value.year + years)
    except ValueError:
        return value.replace(year=value.year + years, day=28)


def create_family_profile_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS family_profile (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            parent_name TEXT NOT NULL,
            parent_birth_date TEXT NOT NULL,
            child_name TEXT NOT NULL,
            child_birth_date TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )


def save_family_profile(
    profile: FamilyProfileInput,
    updated_at: datetime,
) -> None:
    FAMILY_DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(FAMILY_DATABASE_PATH) as connection:
        create_family_profile_table(connection)
        connection.execute(
            """
            INSERT INTO family_profile (
                id,
                parent_name,
                parent_birth_date,
                child_name,
                child_birth_date,
                updated_at
            ) VALUES (1, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                parent_name = excluded.parent_name,
                parent_birth_date = excluded.parent_birth_date,
                child_name = excluded.child_name,
                child_birth_date = excluded.child_birth_date,
                updated_at = excluded.updated_at
            """,
            (
                profile.parent_name,
                profile.parent_birth_date.isoformat(),
                profile.child_name,
                profile.child_birth_date.isoformat(),
                updated_at.isoformat(),
            ),
        )


def load_family_profile() -> tuple[FamilyProfileInput, datetime] | None:
    if not FAMILY_DATABASE_PATH.exists():
        return None

    with sqlite3.connect(FAMILY_DATABASE_PATH) as connection:
        create_family_profile_table(connection)
        stored_profile = connection.execute(
            """
            SELECT
                parent_name,
                parent_birth_date,
                child_name,
                child_birth_date,
                updated_at
            FROM family_profile
            WHERE id = 1
            """
        ).fetchone()

    if stored_profile is None:
        return None

    profile = FamilyProfileInput(
        parent_name=stored_profile[0],
        parent_birth_date=date.fromisoformat(stored_profile[1]),
        child_name=stored_profile[2],
        child_birth_date=date.fromisoformat(stored_profile[3]),
    )
    return profile, datetime.fromisoformat(stored_profile[4])


def build_family_profile_response(
    profile: FamilyProfileInput,
    updated_at: datetime,
) -> FamilyProfileResponse:
    today = get_today()
    child_age = calculate_age(profile.child_birth_date, today)
    matching_parent_date = add_years(profile.parent_birth_date, child_age)

    return FamilyProfileResponse(
        **profile.model_dump(),
        child_age=child_age,
        matching_parent_date=matching_parent_date,
        updated_at=updated_at,
    )


@router.get("/birth-information", response_model=FamilyProfileResponse)
def get_family_birth_information() -> FamilyProfileResponse:
    stored_profile = load_family_profile()
    if stored_profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="저장된 가족 기본정보가 없습니다.",
        )

    profile, updated_at = stored_profile
    return build_family_profile_response(profile, updated_at)


@router.put("/birth-information", response_model=FamilyProfileResponse)
def register_family_birth_information(
    profile: FamilyProfileInput,
) -> FamilyProfileResponse:
    updated_at = datetime.now(timezone.utc)

    save_family_profile(profile, updated_at)
    return build_family_profile_response(profile, updated_at)


@router.delete(
    "/birth-information",
    status_code=status.HTTP_204_NO_CONTENT,
)
def reset_family_birth_information() -> Response:
    if FAMILY_DATABASE_PATH.exists():
        with sqlite3.connect(FAMILY_DATABASE_PATH) as connection:
            create_family_profile_table(connection)
            connection.execute("DELETE FROM family_profile")

    return Response(status_code=status.HTTP_204_NO_CONTENT)
