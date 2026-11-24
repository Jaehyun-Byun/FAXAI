# (2026-11-25) @Gomchiiii FAXAI 백엔드에서 실행할 FastAPI 애플리케이션 객체를 생성하는 파일입니다.

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.dashboard import router as dashboard_router
from app.family import router as family_router
from app.fax import router as fax_router, status_router as fax_status_router
from app.fax_macro import router as fax_macro_router
from app.letter import router as letter_router
from app.memory import router as memory_router


app = FastAPI(title="FAXAI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard_router)
app.include_router(family_router)
app.include_router(fax_router)
app.include_router(fax_status_router)
app.include_router(fax_macro_router)
app.include_router(letter_router)
app.include_router(memory_router)

if os.getenv("FAXAI_DEV_MODE") == "1":
    from app.dev import router as dev_router

    app.include_router(dev_router)


@app.get("/health", tags=["system"])
def get_health() -> dict[str, str]:
    return {"status": "ok"}

