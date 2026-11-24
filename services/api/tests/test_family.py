# (2026-11-25) @Gomchiiii 가족 생년월일의 저장·입력 검증·대응 부모 시점 계산을 확인하는 파일입니다.

import sqlite3
from datetime import date

from fastapi.testclient import TestClient

from app import family
from app.main import app


client = TestClient(app)


def test_register_family_profile(monkeypatch, tmp_path) -> None:
    database_path = tmp_path / "family.db"
    monkeypatch.setattr(family, "FAMILY_DATABASE_PATH", database_path)
    monkeypatch.setattr(family, "get_today", lambda: date(2026, 11, 25))

    response = client.put(
        "/family/birth-information",
        json={
            "parent_name": "김부모",
            "parent_birth_date": "1980-05-10",
            "child_name": "김자녀",
            "child_birth_date": "2000-08-20",
        },
    )

    assert response.status_code == 200
    assert response.json()["child_age"] == 26
    assert response.json()["matching_parent_date"] == "2006-05-10"

    stored_response = client.get("/family/birth-information")
    assert stored_response.status_code == 200
    assert stored_response.json()["parent_name"] == "김부모"

    with sqlite3.connect(database_path) as connection:
        stored_profile = connection.execute(
            "SELECT parent_name, child_name FROM family_profile WHERE id = 1"
        ).fetchone()

    assert stored_profile == ("김부모", "김자녀")


def test_reject_parent_birth_date_after_child_birth_date(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setattr(family, "FAMILY_DATABASE_PATH", tmp_path / "family.db")
    monkeypatch.setattr(family, "get_today", lambda: date(2026, 11, 25))

    response = client.put(
        "/family/birth-information",
        json={
            "parent_name": "김부모",
            "parent_birth_date": "2005-05-10",
            "child_name": "김자녀",
            "child_birth_date": "2000-08-20",
        },
    )

    assert response.status_code == 422


def test_reset_family_profile(monkeypatch, tmp_path) -> None:
    database_path = tmp_path / "family.db"
    monkeypatch.setattr(family, "FAMILY_DATABASE_PATH", database_path)

    profile = family.FamilyProfileInput(
        parent_name="김부모",
        parent_birth_date=date(1980, 5, 10),
        child_name="김자녀",
        child_birth_date=date(2000, 8, 20),
    )
    family.save_family_profile(profile, family.datetime.now(family.timezone.utc))

    response = client.delete("/family/birth-information")

    assert response.status_code == 204
    assert client.get("/family/birth-information").status_code == 404
    with sqlite3.connect(database_path) as connection:
        stored_count = connection.execute(
            "SELECT COUNT(*) FROM family_profile"
        ).fetchone()

    assert stored_count == (0,)
