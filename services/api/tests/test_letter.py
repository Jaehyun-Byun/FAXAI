# (2026-11-25) @Gomchiiii 임의 한국어 답장의 생성·자동 보관·목록·상세 조회 API를 확인하는 파일입니다.

import sqlite3
from datetime import datetime, timezone

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


def test_list_archived_replies_newest_first(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        letter,
        "LETTER_DATABASE_PATH",
        tmp_path / "archive.db",
    )
    letter.save_generated_reply(
        "먼저 생성된 편지",
        datetime(2026, 11, 24, 9, 0, tzinfo=timezone.utc),
    )
    letter.save_generated_reply(
        "나중에 생성된 편지",
        datetime(2026, 11, 25, 9, 0, tzinfo=timezone.utc),
    )

    response = client.get("/letters")

    assert response.status_code == 200
    assert [item["content_preview"] for item in response.json()] == [
        "나중에 생성된 편지",
        "먼저 생성된 편지",
    ]


def test_get_archived_reply_detail(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        letter,
        "LETTER_DATABASE_PATH",
        tmp_path / "archive.db",
    )
    letter_id = letter.save_generated_reply(
        "상세 조회할 편지",
        datetime(2026, 11, 25, 9, 0, tzinfo=timezone.utc),
    )

    response = client.get(f"/letters/{letter_id}")

    assert response.status_code == 200
    assert response.json()["content"] == "상세 조회할 편지"
    assert client.get("/letters/9999").status_code == 404
