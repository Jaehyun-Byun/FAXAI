# (2026-11-25) @Gomchiiii 텍스트 메모리의 등록·조회·수정·삭제를 임시 local memory.db로 제공하며 외부 LLM API 연동 시 저장 방식을 교체할 수 있는 MVP 기능 파일입니다.

import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, Response, status
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


def build_text_memory_response(row: tuple) -> TextMemoryResponse:
    return TextMemoryResponse(
        id=row[0],
        source_date=date.fromisoformat(row[1]),
        source_text=row[2],
        parent_age_at_source=row[3],
        created_at=datetime.fromisoformat(row[4]),
    )


# (2026-11-25) @Gomchiiii 외부 LLM API나 다른 저장소로 교체할 때 이 조회 함수의 구현만 변경합니다.
def list_text_memories() -> list[TextMemoryResponse]:
    if not MEMORY_DATABASE_PATH.exists():
        return []

    with sqlite3.connect(MEMORY_DATABASE_PATH) as connection:
        create_text_memory_table(connection)
        rows = connection.execute(
            """
            SELECT id, source_date, source_text, parent_age_at_source, created_at
            FROM text_memory
            ORDER BY source_date DESC, id DESC
            """
        ).fetchall()

    return [build_text_memory_response(row) for row in rows]


# (2026-11-25) @Gomchiiii 외부 LLM API나 다른 저장소로 교체할 때 이 수정 함수의 구현만 변경합니다.
def update_text_memory(
    memory_id: int,
    memory: TextMemoryInput,
    parent_age_at_source: int,
) -> TextMemoryResponse | None:
    if not MEMORY_DATABASE_PATH.exists():
        return None

    with sqlite3.connect(MEMORY_DATABASE_PATH) as connection:
        create_text_memory_table(connection)
        cursor = connection.execute(
            """
            UPDATE text_memory
            SET source_date = ?, source_text = ?, parent_age_at_source = ?
            WHERE id = ?
            """,
            (
                memory.source_date.isoformat(),
                memory.source_text,
                parent_age_at_source,
                memory_id,
            ),
        )
        if cursor.rowcount == 0:
            return None
        row = connection.execute(
            """
            SELECT id, source_date, source_text, parent_age_at_source, created_at
            FROM text_memory
            WHERE id = ?
            """,
            (memory_id,),
        ).fetchone()

    if row is None:
        return None
    return build_text_memory_response(row)


# (2026-11-25) @Gomchiiii 외부 LLM API나 다른 저장소로 교체할 때 이 삭제 함수의 구현만 변경합니다.
def delete_text_memory(memory_id: int) -> bool:
    if not MEMORY_DATABASE_PATH.exists():
        return False

    with sqlite3.connect(MEMORY_DATABASE_PATH) as connection:
        create_text_memory_table(connection)
        cursor = connection.execute(
            "DELETE FROM text_memory WHERE id = ?",
            (memory_id,),
        )

    return cursor.rowcount > 0


def calculate_parent_age_at_source(memory: TextMemoryInput) -> int:
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

    return calculate_age(family_profile.parent_birth_date, memory.source_date)


@router.get("", response_model=list[TextMemoryResponse])
def get_text_memories() -> list[TextMemoryResponse]:
    return list_text_memories()


@router.post("", response_model=TextMemoryResponse, status_code=status.HTTP_201_CREATED)
def register_text_memory(memory: TextMemoryInput) -> TextMemoryResponse:
    parent_age_at_source = calculate_parent_age_at_source(memory)
    created_at = datetime.now(timezone.utc)
    memory_id = save_text_memory(memory, parent_age_at_source, created_at)

    return TextMemoryResponse(
        **memory.model_dump(),
        id=memory_id,
        parent_age_at_source=parent_age_at_source,
        created_at=created_at,
    )


@router.put("/{memory_id}", response_model=TextMemoryResponse)
def edit_text_memory(
    memory_id: int,
    memory: TextMemoryInput,
) -> TextMemoryResponse:
    parent_age_at_source = calculate_parent_age_at_source(memory)
    updated_memory = update_text_memory(
        memory_id,
        memory,
        parent_age_at_source,
    )
    if updated_memory is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="수정할 텍스트 메모리를 찾을 수 없습니다.",
        )
    return updated_memory


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_text_memory(memory_id: int) -> Response:
    if not delete_text_memory(memory_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="삭제할 텍스트 메모리를 찾을 수 없습니다.",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
