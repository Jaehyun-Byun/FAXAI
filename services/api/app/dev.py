# (2026-11-25) @Gomchiiii 로컬 개발 모드에서 pytest·샘플·팩스 상태 시나리오·MVP DB 초기화를 제공하는 API 기능 파일입니다.

import os
import subprocess
import sys
from datetime import date, datetime, timezone
from enum import Enum
from pathlib import Path
from threading import Lock

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app import family, fax, letter, memory


API_ROOT = Path(__file__).resolve().parents[1]
DEV_DATA_DIRECTORY = family.PROJECT_ROOT / "data"
MAX_OUTPUT_LENGTH = 20_000

router = APIRouter(prefix="/dev", tags=["development"])
test_run_lock = Lock()


class TestSuite(str, Enum):
    all = "all"
    dashboard = "dashboard"
    health = "health"
    family = "family"
    fax = "fax"
    letter = "letter"
    memory = "memory"


class FaxStatusScenario(str, Enum):
    received = "received"
    mock_sent = "mock_sent"
    failed = "failed"


TEST_SUITE_TARGETS = {
    TestSuite.all: ["tests"],
    TestSuite.dashboard: ["tests/test_dashboard.py"],
    TestSuite.health: ["tests/test_health.py"],
    TestSuite.family: ["tests/test_family.py"],
    TestSuite.fax: ["tests/test_fax.py", "tests/test_fax_macro.py"],
    TestSuite.letter: ["tests/test_letter.py"],
    TestSuite.memory: ["tests/test_memory.py"],
}


class TestRunResponse(BaseModel):
    suite: TestSuite
    status: str
    exit_code: int
    output: str


class SampleDataResponse(BaseModel):
    family_created: bool
    memories_created: int


class DatabaseResetResponse(BaseModel):
    deleted_databases: list[str]


def run_pytest(suite: TestSuite) -> TestRunResponse:
    command = [
        sys.executable,
        "-m",
        "pytest",
        *TEST_SUITE_TARGETS[suite],
        "-q",
        "-p",
        "no:cacheprovider",
    ]
    environment = os.environ.copy()
    environment["PYTHONUTF8"] = "1"

    try:
        result = subprocess.run(
            command,
            cwd=API_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
            check=False,
            env=environment,
        )
        output = "\n".join(
            part.strip() for part in (result.stdout, result.stderr) if part.strip()
        )
        return TestRunResponse(
            suite=suite,
            status="passed" if result.returncode == 0 else "failed",
            exit_code=result.returncode,
            output=output[-MAX_OUTPUT_LENGTH:],
        )
    except subprocess.TimeoutExpired:
        return TestRunResponse(
            suite=suite,
            status="failed",
            exit_code=124,
            output="테스트 실행 시간이 60초를 초과했습니다.",
        )


@router.post("/tests/{suite}", response_model=TestRunResponse)
def run_test_suite(suite: TestSuite) -> TestRunResponse:
    if not test_run_lock.acquire(blocking=False):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="다른 테스트가 실행 중입니다.",
        )

    try:
        return run_pytest(suite)
    finally:
        test_run_lock.release()


# (2026-11-25) @Gomchiiii 개발 모드에서만 실제 local family.db와 memory.db에 샘플 데이터를 추가하는 함수입니다.
def create_sample_data() -> SampleDataResponse:
    if family.load_family_profile() is not None or memory.list_text_memories():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="기존 가족 또는 메모리 데이터가 있어 샘플을 생성하지 않았습니다.",
        )

    sample_family = family.FamilyProfileInput(
        parent_name="김영희",
        parent_birth_date=date(1970, 5, 15),
        child_name="김민수",
        child_birth_date=date(2000, 9, 10),
    )
    created_at = datetime.now(timezone.utc)
    family.save_family_profile(sample_family, created_at)

    sample_memories = [
        memory.TextMemoryInput(
            source_date=date(1988, 3, 2),
            source_text="고등학교 입학식 날 새로운 친구들을 만났다.",
        ),
        memory.TextMemoryInput(
            source_date=date(1992, 7, 18),
            source_text="처음으로 혼자 기차를 타고 바다에 갔다.",
        ),
        memory.TextMemoryInput(
            source_date=date(1998, 11, 5),
            source_text="가족과 함께 작은 이사를 준비했다.",
        ),
    ]

    for sample_memory in sample_memories:
        parent_age = family.calculate_age(
            sample_family.parent_birth_date,
            sample_memory.source_date,
        )
        memory.save_text_memory(sample_memory, parent_age, created_at)

    return SampleDataResponse(
        family_created=True,
        memories_created=len(sample_memories),
    )


@router.post("/sample-data", response_model=SampleDataResponse)
def seed_sample_data() -> SampleDataResponse:
    return create_sample_data()


# (2026-11-25) @Gomchiiii 단말 상태 화면 검증을 위해 received, mock_sent, failed 팩스 이벤트를 생성하는 개발 전용 함수입니다.
def create_fax_status_scenario(
    event_status: FaxStatusScenario,
) -> fax.FaxEventResponse:
    direction = (
        fax.FaxDirection.incoming
        if event_status == FaxStatusScenario.received
        else fax.FaxDirection.outgoing
    )
    scenario_text = {
        FaxStatusScenario.received: "개발 모드 수신 완료 테스트",
        FaxStatusScenario.mock_sent: "개발 모드 발송 완료 테스트",
        FaxStatusScenario.failed: "개발 모드 발송 실패 테스트",
    }[event_status]
    created_at = datetime.now(timezone.utc)
    event_id = fax.save_fax_event(
        direction=direction,
        remote_number="02-0000-0000",
        text=scenario_text,
        event_status=event_status.value,
        created_at=created_at,
    )
    return fax.FaxEventResponse(
        id=event_id,
        direction=direction,
        remote_number="02-0000-0000",
        text=scenario_text,
        status=event_status.value,
        created_at=created_at,
    )


@router.post("/fax-status/{event_status}", response_model=fax.FaxEventResponse)
def seed_fax_status(
    event_status: FaxStatusScenario,
) -> fax.FaxEventResponse:
    return create_fax_status_scenario(event_status)


# (2026-11-25) @Gomchiiii 개발 모드에서만 family.db, memory.db, archive.db, fax.db를 삭제해 로컬 MVP 데이터를 완전히 초기화하는 함수입니다.
def hard_reset_databases() -> DatabaseResetResponse:
    allowed_directory = DEV_DATA_DIRECTORY.resolve()
    database_paths = (
        family.FAMILY_DATABASE_PATH,
        memory.MEMORY_DATABASE_PATH,
        letter.LETTER_DATABASE_PATH,
        fax.FAX_DATABASE_PATH,
    )
    deleted_databases: list[str] = []

    for database_path in database_paths:
        resolved_path = database_path.resolve()
        if resolved_path.parent != allowed_directory:
            raise RuntimeError("허용된 data 디렉터리 밖의 DB는 삭제할 수 없습니다.")
        if resolved_path.exists():
            if not resolved_path.is_file():
                raise RuntimeError("DB 초기화 대상이 파일이 아닙니다.")
            resolved_path.unlink()
            deleted_databases.append(resolved_path.name)

    return DatabaseResetResponse(deleted_databases=deleted_databases)


@router.delete("/databases", response_model=DatabaseResetResponse)
def reset_databases() -> DatabaseResetResponse:
    return hard_reset_databases()
