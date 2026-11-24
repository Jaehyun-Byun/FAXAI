# (2026-11-25) @Gomchiiii Mock 팩스 발송·입력 검증·이벤트 목록과 fax.db 기록을 확인하는 파일입니다.

import sqlite3

from fastapi.testclient import TestClient

from app import fax
from app.main import app


client = TestClient(app)


def test_send_fax_through_mock_provider(monkeypatch, tmp_path) -> None:
    database_path = tmp_path / "fax.db"
    monkeypatch.setattr(fax, "FAX_DATABASE_PATH", database_path)
    monkeypatch.setattr(
        fax,
        "send_with_mock_provider",
        lambda recipient_number, text: "mock_sent",
    )

    response = client.post(
        "/fax/mock/send",
        json={
            "recipient_number": "+82-2-1234-5678",
            "text": "오늘도 좋은 하루 보내렴.",
        },
    )

    assert response.status_code == 201
    assert response.json()["direction"] == "outgoing"
    assert response.json()["status"] == "mock_sent"

    with sqlite3.connect(database_path) as connection:
        stored_event = connection.execute(
            "SELECT direction, remote_number, text, status FROM fax_event"
        ).fetchone()

    assert stored_event == (
        "outgoing",
        "+82-2-1234-5678",
        "오늘도 좋은 하루 보내렴.",
        "mock_sent",
    )

    list_response = client.get("/fax/events")
    assert list_response.status_code == 200
    assert list_response.json()[0]["direction"] == "outgoing"


def test_reject_invalid_fax_input(monkeypatch, tmp_path) -> None:
    database_path = tmp_path / "fax.db"
    monkeypatch.setattr(fax, "FAX_DATABASE_PATH", database_path)

    invalid_number_response = client.post(
        "/fax/mock/incoming",
        json={"sender_number": "not-a-number", "text": "내용"},
    )
    empty_text_response = client.post(
        "/fax/mock/send",
        json={"recipient_number": "02-1234-5678", "text": "   "},
    )

    assert invalid_number_response.status_code == 422
    assert empty_text_response.status_code == 422
    assert not database_path.exists()
