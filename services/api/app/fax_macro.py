# (2026-11-25) @Gomchiiii Mock 팩스 수신부터 임의 답장 생성·보관·같은 번호 자동 발송까지 연결하는 MVP 워크플로 파일입니다.

from datetime import datetime, timezone

from fastapi import APIRouter, status
from pydantic import BaseModel

from app import fax, letter


router = APIRouter(prefix="/fax/mock", tags=["mock-fax"])


class AutomaticFaxReplyResponse(BaseModel):
    incoming: fax.FaxEventResponse
    reply: fax.FaxEventResponse
    archived_letter_id: int


# (2026-11-25) @Gomchiiii 실제 큐와 Worker를 도입할 때 이 자동응답 워크플로 함수의 구현을 교체합니다.
def process_automatic_reply(
    incoming_fax: fax.IncomingFaxInput,
) -> AutomaticFaxReplyResponse:
    incoming_at = datetime.now(timezone.utc)
    incoming_id = fax.save_fax_event(
        direction=fax.FaxDirection.incoming,
        remote_number=incoming_fax.sender_number,
        text=incoming_fax.text,
        event_status="received",
        created_at=incoming_at,
    )
    incoming_event = fax.FaxEventResponse(
        id=incoming_id,
        direction=fax.FaxDirection.incoming,
        remote_number=incoming_fax.sender_number,
        text=incoming_fax.text,
        status="received",
        created_at=incoming_at,
    )

    reply_text = letter.generate_random_reply()
    reply_at = datetime.now(timezone.utc)
    archived_letter_id = letter.save_generated_reply(reply_text, reply_at)

    try:
        reply_status = fax.send_with_mock_provider(
            incoming_fax.sender_number,
            reply_text,
        )
    except Exception:
        reply_status = "failed"

    reply_id = fax.save_fax_event(
        direction=fax.FaxDirection.outgoing,
        remote_number=incoming_fax.sender_number,
        text=reply_text,
        event_status=reply_status,
        created_at=reply_at,
    )
    reply_event = fax.FaxEventResponse(
        id=reply_id,
        direction=fax.FaxDirection.outgoing,
        remote_number=incoming_fax.sender_number,
        text=reply_text,
        status=reply_status,
        created_at=reply_at,
    )

    return AutomaticFaxReplyResponse(
        incoming=incoming_event,
        reply=reply_event,
        archived_letter_id=archived_letter_id,
    )


@router.post(
    "/incoming",
    response_model=AutomaticFaxReplyResponse,
    status_code=status.HTTP_201_CREATED,
)
def receive_and_reply_to_mock_fax(
    incoming_fax: fax.IncomingFaxInput,
) -> AutomaticFaxReplyResponse:
    return process_automatic_reply(incoming_fax)
