# (2026-11-25) @Gomchiiii 개발 모드의 테스트·샘플·팩스 상태 시나리오·로컬 DB 초기화 API를 확인하는 파일입니다.

import subprocess

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import dev


development_api = FastAPI()
development_api.include_router(dev.router)
client = TestClient(development_api)


def test_run_allowed_health_suite(monkeypatch) -> None:
    completed_process = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout="1 passed",
        stderr="",
    )
    monkeypatch.setattr(dev.subprocess, "run", lambda *args, **kwargs: completed_process)

    response = client.post("/dev/tests/health")

    assert response.status_code == 200
    assert response.json()["status"] == "passed"
    assert response.json()["output"] == "1 passed"


def test_reject_unknown_test_suite() -> None:
    response = client.post("/dev/tests/unknown")

    assert response.status_code == 422


def test_create_sample_data_only_when_databases_are_empty(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setattr(
        dev.family,
        "FAMILY_DATABASE_PATH",
        tmp_path / "family.db",
    )
    monkeypatch.setattr(
        dev.memory,
        "MEMORY_DATABASE_PATH",
        tmp_path / "memory.db",
    )

    response = client.post("/dev/sample-data")

    assert response.status_code == 200
    assert response.json() == {
        "family_created": True,
        "memories_created": 3,
    }
    assert dev.family.load_family_profile() is not None
    assert len(dev.memory.list_text_memories()) == 3
    assert client.post("/dev/sample-data").status_code == 409


def test_create_all_fax_status_scenarios(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        dev.fax,
        "FAX_DATABASE_PATH",
        tmp_path / "fax.db",
    )

    for event_status in ("received", "mock_sent", "failed"):
        response = client.post(f"/dev/fax-status/{event_status}")
        assert response.status_code == 200
        assert response.json()["status"] == event_status

    assert {event.status for event in dev.fax.list_fax_events()} == {
        "received",
        "mock_sent",
        "failed",
    }
    assert client.post("/dev/fax-status/unknown").status_code == 422


def test_hard_reset_only_deletes_allowed_databases(monkeypatch, tmp_path) -> None:
    family_database = tmp_path / "family.db"
    memory_database = tmp_path / "memory.db"
    archive_database = tmp_path / "archive.db"
    fax_database = tmp_path / "fax.db"
    unrelated_file = tmp_path / "keep.txt"

    for database_path in (
        family_database,
        memory_database,
        archive_database,
        fax_database,
    ):
        database_path.write_bytes(b"temporary database")
    unrelated_file.write_text("keep", encoding="utf-8")

    monkeypatch.setattr(dev, "DEV_DATA_DIRECTORY", tmp_path)
    monkeypatch.setattr(dev.family, "FAMILY_DATABASE_PATH", family_database)
    monkeypatch.setattr(dev.memory, "MEMORY_DATABASE_PATH", memory_database)
    monkeypatch.setattr(dev.letter, "LETTER_DATABASE_PATH", archive_database)
    monkeypatch.setattr(dev.fax, "FAX_DATABASE_PATH", fax_database)

    response = client.delete("/dev/databases")

    assert response.status_code == 200
    assert response.json()["deleted_databases"] == [
        "family.db",
        "memory.db",
        "archive.db",
        "fax.db",
    ]
    assert not family_database.exists()
    assert not memory_database.exists()
    assert not archive_database.exists()
    assert not fax_database.exists()
    assert unrelated_file.exists()
    assert client.delete("/dev/databases").json()["deleted_databases"] == []
