# (2026-11-25) @Gomchiiii FAXAI 백엔드에서 실행할 FastAPI 애플리케이션 객체를 생성하는 파일입니다.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.family import router as family_router


app = FastAPI(title="FAXAI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(family_router)


@app.get("/health", tags=["system"])
def get_health() -> dict[str, str]:
    return {"status": "ok"}

