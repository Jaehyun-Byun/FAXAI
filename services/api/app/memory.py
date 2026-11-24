# (2026-11-25) @Gomchiiii 텍스트 메모리를 임시 로컬 memory.db에 저장하며 외부 LLM API 연동 시 저장 방식을 교체하거나 제거할 수 있는 MVP 기능 파일입니다.

import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from app.family import calculate_age, load_family_profile


PROJECT_ROOT = Path(__file__).resolve().parents[3]
MEMORY_DATABASE_PATH = PROJECT_ROOT / "data" / "memory.db"

router = APIRouter(prefix="/memories", tags=["memories"])


class TextMemoryInput(BaseModel):
    source_date: date
    source_text: str = Field(min_length=1, max_length=10_000)

    @field_validator("source_date")
    @classmethod
    def validate_source_date(cls, value: date) -> date:
        if value > get_today():
            raise ValueError("기록 날짜는 오늘 이후일 수 없습니다.")
        return value

    @field_validator("source_text")
    @classmethod
    def strip_source_text(cls, value: str) -> str:
        stripped_value = value.strip()
        if not stripped_value:
            raise ValueError("텍스트 내용을 입력해 주세요.")
        return stripped_value


class TextMemoryResponse(TextMemoryInput):
    id: int
    parent_age_at_source: int
    created_at: datetime


def get_today() -> date:
    return date.today()


def create_text_memory_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS text_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_date TEXT NOT NULL,
            source_text TEXT NOT NULL,
            parent_age_at_source INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )


# (2026-11-25) @Gomchiiii 외부 LLM API나 다른 저장소로 교체할 때 이 저장 함수의 구현만 변경합니다.
def save_text_memory(
    memory: TextMemoryInput,
    parent_age_at_source: int,
    created_at: datetime,
) -> int:
    MEMORY_DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(MEMORY_DATABASE_PATH) as connection:
        create_text_memory_table(connection)
        cursor = connection.execute(
            """
            INSERT INTO text_memory (
                source_date,
                source_text,
                parent_age_at_source,
                created_at
            ) VALUES (?, ?, ?, ?)
            """,
            (
                memory.source_date.isoformat(),
                memory.source_text,
                parent_age_at_source,
                created_at.isoformat(),
            ),
        )
        memory_id = cursor.lastrowid

    if memory_id is None:
        raise RuntimeError("텍스트 메모리 ID를 생성하지 못했습니다.")
    return memory_id


@router.post("", response_model=TextMemoryResponse, status_code=status.HTTP_201_CREATED)
def register_text_memory(memory: TextMemoryInput) -> TextMemoryResponse:
    stored_family_profile = load_family_profile()
    if stored_family_profile is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="가족 기본정보를 먼저 저장해 주세요.",
        )

    family_profile, _ = stored_family_profile
    if memory.source_date < family_profile.parent_birth_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="기록 날짜는 부모 생년월일보다 앞설 수 없습니다.",
        )

    parent_age_at_source = calculate_age(
        family_profile.parent_birth_date,
        memory.source_date,
    )
    created_at = datetime.now(timezone.utc)
    memory_id = save_text_memory(memory, parent_age_at_source, created_at)

    return TextMemoryResponse(
        **memory.model_dump(),
        id=memory_id,
        parent_age_at_source=parent_age_at_source,
        created_at=created_at,
    )
