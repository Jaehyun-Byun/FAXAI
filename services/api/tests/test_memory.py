# (2026-11-25) @Gomchiiii 텍스트 메모리 API의 등록·목록·수정·삭제와 입력 검증을 확인하는 파일입니다.

import sqlite3
from datetime import date, datetime, timezone

from fastapi.testclient import TestClient

from app import family, memory
from app.main import app


client = TestClient(app)


def save_test_family_profile(monkeypatch, database_path) -> None:
    monkeypatch.setattr(family, "FAMILY_DATABASE_PATH", database_path)
    profile = family.FamilyProfileInput(
        parent_name="김부모",
        parent_birth_date=date(1980, 5, 10),
        child_name="김자녀",
        child_birth_date=date(2000, 8, 20),
    )
    family.save_family_profile(profile, datetime.now(timezone.utc))


def test_register_text_memory(monkeypatch, tmp_path) -> None:
    memory_database_path = tmp_path / "memory.db"
    save_test_family_profile(monkeypatch, tmp_path / "family.db")
    monkeypatch.setattr(memory, "MEMORY_DATABASE_PATH", memory_database_path)
    monkeypatch.setattr(memory, "get_today", lambda: date(2026, 11, 25))

    response = client.post(
        "/memories",
        json={
            "source_date": "2000-05-10",
            "source_text": "스무 살 생일에 처음으로 혼자 여행을 갔다.",
        },
    )

    assert response.status_code == 201
    assert response.json()["parent_age_at_source"] == 20

    with sqlite3.connect(memory_database_path) as connection:
        stored_memory = connection.execute(
            "SELECT source_date, source_text FROM text_memory"
        ).fetchone()

    assert stored_memory == (
        "2000-05-10",
        "스무 살 생일에 처음으로 혼자 여행을 갔다.",
    )


def test_require_family_profile_before_memory(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(family, "FAMILY_DATABASE_PATH", tmp_path / "family.db")
    monkeypatch.setattr(memory, "MEMORY_DATABASE_PATH", tmp_path / "memory.db")

    response = client.post(
        "/memories",
        json={
            "source_date": "2000-05-10",
            "source_text": "저장되지 않아야 하는 기록",
        },
    )

    assert response.status_code == 409


def test_reject_memory_before_parent_birth(monkeypatch, tmp_path) -> None:
    save_test_family_profile(monkeypatch, tmp_path / "family.db")
    monkeypatch.setattr(memory, "MEMORY_DATABASE_PATH", tmp_path / "memory.db")

    response = client.post(
        "/memories",
        json={
            "source_date": "1979-05-10",
            "source_text": "부모 생년월일보다 앞선 기록",
        },
    )

    assert response.status_code == 422


def test_list_text_memories_newest_first(monkeypatch, tmp_path) -> None:
    save_test_family_profile(monkeypatch, tmp_path / "family.db")
    monkeypatch.setattr(memory, "MEMORY_DATABASE_PATH", tmp_path / "memory.db")

    for source_date, source_text in [
        ("1999-05-10", "열아홉 살의 기록"),
        ("2001-05-10", "스물한 살의 기록"),
    ]:
        client.post(
            "/memories",
            json={"source_date": source_date, "source_text": source_text},
        )

    response = client.get("/memories")

    assert response.status_code == 200
    assert [item["source_text"] for item in response.json()] == [
        "스물한 살의 기록",
        "열아홉 살의 기록",
    ]


def test_edit_text_memory(monkeypatch, tmp_path) -> None:
    save_test_family_profile(monkeypatch, tmp_path / "family.db")
    monkeypatch.setattr(memory, "MEMORY_DATABASE_PATH", tmp_path / "memory.db")

    created_response = client.post(
        "/memories",
        json={"source_date": "2000-05-10", "source_text": "수정 전 기록"},
    )
    memory_id = created_response.json()["id"]

    response = client.put(
        f"/memories/{memory_id}",
        json={"source_date": "2001-05-10", "source_text": "수정 후 기록"},
    )

    assert response.status_code == 200
    assert response.json()["source_text"] == "수정 후 기록"
    assert response.json()["parent_age_at_source"] == 21


def test_delete_text_memory(monkeypatch, tmp_path) -> None:
    save_test_family_profile(monkeypatch, tmp_path / "family.db")
    monkeypatch.setattr(memory, "MEMORY_DATABASE_PATH", tmp_path / "memory.db")

    created_response = client.post(
        "/memories",
        json={"source_date": "2000-05-10", "source_text": "삭제할 기록"},
    )
    memory_id = created_response.json()["id"]

    response = client.delete(f"/memories/{memory_id}")

    assert response.status_code == 204
    assert client.get("/memories").json() == []
    assert client.delete(f"/memories/{memory_id}").status_code == 404
