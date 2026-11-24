# (2026-11-25) @Gomchiiii Mock 팩스 발송과 송수신 상태 기록·조회를 제공하며 향후 실제 인터넷 팩스 API로 교체할 수 있는 MVP 기능 파일입니다.

import re
import sqlite3
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from fastapi import APIRouter, status
from pydantic import BaseModel, Field, field_validator


PROJECT_ROOT = Path(__file__).resolve().parents[3]
FAX_DATABASE_PATH = PROJECT_ROOT / "data" / "fax.db"
FAX_NUMBER_PATTERN = re.compile(r"^\+?[0-9][0-9 -]*$")

router = APIRouter(prefix="/fax/mock", tags=["mock-fax"])
status_router = APIRouter(prefix="/fax", tags=["fax-status"])


class FaxDirection(str, Enum):
    incoming = "incoming"
    outgoing = "outgoing"


class IncomingFaxInput(BaseModel):
    sender_number: str = Field(min_length=3, max_length=30)
    text: str = Field(min_length=1, max_length=10_000)

    @field_validator("sender_number")
    @classmethod
    def validate_sender_number(cls, value: str) -> str:
        return validate_fax_number(value)

    @field_validator("text")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return validate_fax_text(value)


class OutgoingFaxInput(BaseModel):
    recipient_number: str = Field(min_length=3, max_length=30)
    text: str = Field(min_length=1, max_length=10_000)

    @field_validator("recipient_number")
    @classmethod
    def validate_recipient_number(cls, value: str) -> str:
        return validate_fax_number(value)

    @field_validator("text")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return validate_fax_text(value)


class FaxEventResponse(BaseModel):
    id: int
    direction: FaxDirection
    remote_number: str
    text: str
    status: str
    created_at: datetime


def validate_fax_number(value: str) -> str:
    normalized_value = value.strip()
    if not FAX_NUMBER_PATTERN.fullmatch(normalized_value):
        raise ValueError("팩스 번호 형식을 확인해 주세요.")
    return normalized_value


def validate_fax_text(value: str) -> str:
    normalized_value = value.strip()
    if not normalized_value:
        raise ValueError("팩스 텍스트를 입력해 주세요.")
    return normalized_value


def create_fax_event_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS fax_event (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            direction TEXT NOT NULL,
            remote_number TEXT NOT NULL,
            text TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )


# (2026-11-25) @Gomchiiii 외부 팩스 기록 저장소로 교체할 때 이 이벤트 저장 함수의 구현만 변경합니다.
def save_fax_event(
    direction: FaxDirection,
    remote_number: str,
    text: str,
    event_status: str,
    created_at: datetime,
) -> int:
    FAX_DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(FAX_DATABASE_PATH) as connection:
        create_fax_event_table(connection)
        cursor = connection.execute(
            """
            INSERT INTO fax_event (
                direction,
                remote_number,
                text,
                status,
                created_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                direction.value,
                remote_number,
                text,
                event_status,
                created_at.isoformat(),
            ),
        )
        event_id = cursor.lastrowid

    if event_id is None:
        raise RuntimeError("팩스 이벤트 ID를 만들지 못했습니다.")
    return event_id


def build_fax_event_response(row: tuple) -> FaxEventResponse:
    return FaxEventResponse(
        id=row[0],
        direction=FaxDirection(row[1]),
        remote_number=row[2],
        text=row[3],
        status=row[4],
        created_at=datetime.fromisoformat(row[5]),
    )


# (2026-11-25) @Gomchiiii 외부 팩스 기록 저장소로 교체할 때 이 이벤트 목록 조회 함수의 구현만 변경합니다.
def list_fax_events(limit: int | None = None) -> list[FaxEventResponse]:
    if not FAX_DATABASE_PATH.exists():
        return []

    query = """
        SELECT id, direction, remote_number, text, status, created_at
        FROM fax_event
        ORDER BY created_at DESC, id DESC
    """
    parameters: tuple = ()
    if limit is not None:
        query += " LIMIT ?"
        parameters = (limit,)

    with sqlite3.connect(FAX_DATABASE_PATH) as connection:
        create_fax_event_table(connection)
        rows = connection.execute(query, parameters).fetchall()

    return [build_fax_event_response(row) for row in rows]


# (2026-11-25) @Gomchiiii 실제 인터넷 팩스 API를 연동할 때 이 Mock 발송 함수의 구현만 변경합니다.
def send_with_mock_provider(recipient_number: str, text: str) -> str:
    return "mock_sent"


@router.post(
    "/send",
    response_model=FaxEventResponse,
    status_code=status.HTTP_201_CREATED,
)
def send_mock_fax(outgoing_fax: OutgoingFaxInput) -> FaxEventResponse:
    try:
        provider_status = send_with_mock_provider(
            outgoing_fax.recipient_number,
            outgoing_fax.text,
        )
    except Exception:
        provider_status = "failed"
    created_at = datetime.now(timezone.utc)
    event_id = save_fax_event(
        direction=FaxDirection.outgoing,
        remote_number=outgoing_fax.recipient_number,
        text=outgoing_fax.text,
        event_status=provider_status,
        created_at=created_at,
    )
    return FaxEventResponse(
        id=event_id,
        direction=FaxDirection.outgoing,
        remote_number=outgoing_fax.recipient_number,
        text=outgoing_fax.text,
        status=provider_status,
        created_at=created_at,
    )


@status_router.get("/events", response_model=list[FaxEventResponse])
def get_fax_events() -> list[FaxEventResponse]:
    return list_fax_events()
