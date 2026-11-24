# (2026-11-25) @Gomchiiii 팩스·메모리·편지 저장소의 현재 활동 수와 최근 팩스를 조합하는 대시보드 API 파일입니다.

from fastapi import APIRouter
from pydantic import BaseModel

from app import fax, letter, memory


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class DashboardSummaryResponse(BaseModel):
    fax_count: int
    memory_count: int
    letter_count: int
    recent_faxes: list[fax.FaxEventResponse]


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary() -> DashboardSummaryResponse:
    fax_events = fax.list_fax_events()
    memories = memory.list_text_memories()
    letters = letter.list_archived_replies()

    return DashboardSummaryResponse(
        fax_count=len(fax_events),
        memory_count=len(memories),
        letter_count=len(letters),
        recent_faxes=fax_events[:5],
    )
