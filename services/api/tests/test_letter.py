# (2026-11-25) @Gomchiiii 임의 한국어 답장 생성과 archive.db 자동 보관 API를 확인하는 파일입니다.

import sqlite3

from fastapi.testclient import TestClient

from app import letter
from app.main import app


client = TestClient(app)


def test_generate_random_reply_from_allowed_sentences(monkeypatch) -> None:
    expected_reply = letter.RANDOM_REPLIES[0]
    monkeypatch.setattr(
        letter.secrets,
        "choice",
        lambda replies: replies[0],
    )

    assert letter.generate_random_reply() == expected_reply


def test_generate_and_archive_reply(monkeypatch, tmp_path) -> None:
    database_path = tmp_path / "archive.db"
    expected_reply = "테스트용 한국어 답장입니다."
    monkeypatch.setattr(letter, "LETTER_DATABASE_PATH", database_path)
    monkeypatch.setattr(letter, "generate_random_reply", lambda: expected_reply)

    response = client.post("/letters")

    assert response.status_code == 201
    assert response.json()["content"] == expected_reply
    assert response.json()["id"] == 1

    with sqlite3.connect(database_path) as connection:
        stored_letter = connection.execute(
            "SELECT content FROM generated_letter WHERE id = 1"
        ).fetchone()

    assert stored_letter == (expected_reply,)
