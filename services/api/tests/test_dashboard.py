# (2026-11-25) @Gomchiiii 팩스·메모리·편지 수와 최근 팩스 대시보드 요약을 확인하는 파일입니다.

from datetime import date, datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app import fax, letter, memory
from app.main import app


client = TestClient(app)


def test_get_dashboard_activity_summary(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(fax, "FAX_DATABASE_PATH", tmp_path / "fax.db")
    monkeypatch.setattr(memory, "MEMORY_DATABASE_PATH", tmp_path / "memory.db")
    monkeypatch.setattr(letter, "LETTER_DATABASE_PATH", tmp_path / "archive.db")
    first_time = datetime(2026, 11, 20, 9, 0, tzinfo=timezone.utc)

    for index in range(6):
        fax.save_fax_event(
            fax.FaxDirection.incoming,
            f"02-1111-111{index}",
            f"팩스 {index}",
            "received",
            first_time + timedelta(days=index),
        )
    memory.save_text_memory(
        memory.TextMemoryInput(
            source_date=date(2000, 5, 10),
            source_text="대시보드 테스트 메모리",
        ),
        parent_age_at_source=20,
        created_at=first_time,
    )
    letter.save_generated_reply("대시보드 테스트 편지", first_time)

    response = client.get("/dashboard/summary")

    assert response.status_code == 200
    assert response.json()["fax_count"] == 6
    assert response.json()["memory_count"] == 1
    assert response.json()["letter_count"] == 1
    assert len(response.json()["recent_faxes"]) == 5
    assert response.json()["recent_faxes"][0]["text"] == "팩스 5"
