# (2026-11-25) @Gomchiiii 개발 모드의 테스트 실행과 샘플 데이터 생성 API를 확인하는 파일입니다.

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
