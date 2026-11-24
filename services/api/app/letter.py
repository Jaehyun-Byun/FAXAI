# (2026-11-25) @Gomchiiii 임의 한국어 답장의 생성·보관·목록·상세 조회를 제공하며 향후 LLM API와 저장소를 교체할 수 있는 MVP 기능 파일입니다.

import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel


PROJECT_ROOT = Path(__file__).resolve().parents[3]
LETTER_DATABASE_PATH = PROJECT_ROOT / "data" / "archive.db"

router = APIRouter(prefix="/letters", tags=["letters"])

RANDOM_REPLIES = (
    "오늘 하루도 네가 웃을 일이 많았으면 좋겠다.",
    "서두르지 않아도 괜찮으니 네 속도로 걸어가렴.",
    "힘든 일이 있었다면 오늘은 조금 쉬어도 괜찮다.",
    "작은 기쁨 하나가 네 하루를 따뜻하게 해주길 바란다.",
    "언제나 네 편이 있다는 것을 잊지 않았으면 좋겠다.",
    "오늘의 경험도 언젠가 너에게 좋은 이야기가 될 거야.",
    "밥 잘 챙겨 먹고 몸과 마음을 모두 아껴주렴.",
    "네가 선택한 길을 믿고 한 걸음씩 나아가면 좋겠다.",
)


class GeneratedLetterResponse(BaseModel):
    id: int
    content: str
    generated_at: datetime


class ArchivedLetterListItem(BaseModel):
    id: int
    content_preview: str
    generated_at: datetime


# (2026-11-25) @Gomchiiii 외부 LLM API를 연동할 때 이 임의 문장 생성 함수의 구현만 변경합니다.
def generate_random_reply() -> str:
    return secrets.choice(RANDOM_REPLIES)


def create_letter_archive_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS generated_letter (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            generated_at TEXT NOT NULL
        )
        """
    )


# (2026-11-25) @Gomchiiii 외부 보관 저장소로 교체할 때 이 편지 저장 함수의 구현만 변경합니다.
def save_generated_reply(content: str, generated_at: datetime) -> int:
    LETTER_DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(LETTER_DATABASE_PATH) as connection:
        create_letter_archive_table(connection)
        cursor = connection.execute(
            """
            INSERT INTO generated_letter (content, generated_at)
            VALUES (?, ?)
            """,
            (content, generated_at.isoformat()),
        )
        letter_id = cursor.lastrowid

    if letter_id is None:
        raise RuntimeError("생성된 편지 ID를 만들지 못했습니다.")
    return letter_id


# (2026-11-25) @Gomchiiii 외부 보관 저장소로 교체할 때 이 편지 목록 조회 함수의 구현만 변경합니다.
def list_archived_replies() -> list[ArchivedLetterListItem]:
    if not LETTER_DATABASE_PATH.exists():
        return []

    with sqlite3.connect(LETTER_DATABASE_PATH) as connection:
        create_letter_archive_table(connection)
        rows = connection.execute(
            """
            SELECT id, content, generated_at
            FROM generated_letter
            ORDER BY generated_at DESC, id DESC
            """
        ).fetchall()

    return [
        ArchivedLetterListItem(
            id=row[0],
            content_preview=(
                row[1] if len(row[1]) <= 80 else f"{row[1][:80]}…"
            ),
            generated_at=datetime.fromisoformat(row[2]),
        )
        for row in rows
    ]


# (2026-11-25) @Gomchiiii 외부 보관 저장소로 교체할 때 이 편지 상세 조회 함수의 구현만 변경합니다.
def get_archived_reply(letter_id: int) -> GeneratedLetterResponse | None:
    if not LETTER_DATABASE_PATH.exists():
        return None

    with sqlite3.connect(LETTER_DATABASE_PATH) as connection:
        create_letter_archive_table(connection)
        row = connection.execute(
            """
            SELECT id, content, generated_at
            FROM generated_letter
            WHERE id = ?
            """,
            (letter_id,),
        ).fetchone()

    if row is None:
        return None
    return GeneratedLetterResponse(
        id=row[0],
        content=row[1],
        generated_at=datetime.fromisoformat(row[2]),
    )


@router.get("", response_model=list[ArchivedLetterListItem])
def get_archived_replies() -> list[ArchivedLetterListItem]:
    return list_archived_replies()


@router.get("/{letter_id}", response_model=GeneratedLetterResponse)
def get_archived_reply_detail(letter_id: int) -> GeneratedLetterResponse:
    archived_reply = get_archived_reply(letter_id)
    if archived_reply is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="보관된 편지를 찾을 수 없습니다.",
        )
    return archived_reply


@router.post("", response_model=GeneratedLetterResponse, status_code=status.HTTP_201_CREATED)
def generate_and_archive_reply() -> GeneratedLetterResponse:
    content = generate_random_reply()
    generated_at = datetime.now(timezone.utc)
    letter_id = save_generated_reply(content, generated_at)

    return GeneratedLetterResponse(
        id=letter_id,
        content=content,
        generated_at=generated_at,
    )
