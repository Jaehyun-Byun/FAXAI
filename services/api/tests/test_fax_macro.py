# (2026-11-25) @Gomchiiii Mock 팩스 수신부터 임의 답장 보관·자동 발송·실패 기록까지 확인하는 파일입니다.

import sqlite3

from fastapi.testclient import TestClient

from app import fax, letter
from app.main import app


client = TestClient(app)


def test_automatically_reply_to_incoming_fax(monkeypatch, tmp_path) -> None:
    fax_database = tmp_path / "fax.db"
    archive_database = tmp_path / "archive.db"
    expected_reply = "자동으로 생성한 테스트 답장"
    monkeypatch.setattr(fax, "FAX_DATABASE_PATH", fax_database)
    monkeypatch.setattr(letter, "LETTER_DATABASE_PATH", archive_database)
    monkeypatch.setattr(letter, "generate_random_reply", lambda: expected_reply)
    monkeypatch.setattr(
        fax,
        "send_with_mock_provider",
        lambda recipient_number, text: "mock_sent",
    )

    response = client.post(
        "/fax/mock/incoming",
        json={
            "sender_number": "+82-2-1234-5678",
            "text": "오늘 잘 지내고 있니?",
        },
    )

    assert response.status_code == 201
    assert response.json()["incoming"]["status"] == "received"
    assert response.json()["reply"]["remote_number"] == "+82-2-1234-5678"
    assert response.json()["reply"]["status"] == "mock_sent"
    assert response.json()["archived_letter_id"] == 1

    with sqlite3.connect(fax_database) as connection:
        fax_events = connection.execute(
            "SELECT direction, remote_number, text, status FROM fax_event ORDER BY id"
        ).fetchall()
    with sqlite3.connect(archive_database) as connection:
        archived_reply = connection.execute(
            "SELECT content FROM generated_letter WHERE id = 1"
        ).fetchone()

    assert fax_events == [
        ("incoming", "+82-2-1234-5678", "오늘 잘 지내고 있니?", "received"),
        ("outgoing", "+82-2-1234-5678", expected_reply, "mock_sent"),
    ]
    assert archived_reply == (expected_reply,)


def test_record_failed_automatic_reply(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(fax, "FAX_DATABASE_PATH", tmp_path / "fax.db")
    monkeypatch.setattr(letter, "LETTER_DATABASE_PATH", tmp_path / "archive.db")
    monkeypatch.setattr(letter, "generate_random_reply", lambda: "실패 기록용 답장")

    def fail_to_send(recipient_number: str, text: str) -> str:
        raise RuntimeError("Mock provider failure")

    monkeypatch.setattr(fax, "send_with_mock_provider", fail_to_send)

    response = client.post(
        "/fax/mock/incoming",
        json={"sender_number": "02-1234-5678", "text": "수신 내용"},
    )

    assert response.status_code == 201
    assert response.json()["reply"]["status"] == "failed"
    assert fax.list_fax_events()[0].status == "failed"
