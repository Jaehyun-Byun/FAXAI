# (2026-11-25) @Gomchiiii API 상태 확인 엔드포인트가 정상 응답하는지 검증하는 파일입니다.

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_get_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
