# (2026-11-25) @Gomchiiii 로컬 개발 모드에서 허용된 pytest 테스트를 실행하고 빈 로컬 DB에 샘플 데이터를 생성하는 API 기능을 정의하는 파일입니다.

import os
import subprocess
import sys
from datetime import date, datetime, timezone
from enum import Enum
from pathlib import Path
from threading import Lock

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app import family, memory


API_ROOT = Path(__file__).resolve().parents[1]
MAX_OUTPUT_LENGTH = 20_000

router = APIRouter(prefix="/dev", tags=["development"])
test_run_lock = Lock()


class TestSuite(str, Enum):
    all = "all"
    health = "health"
    family = "family"
    memory = "memory"


TEST_SUITE_TARGETS = {
    TestSuite.all: ["tests"],
    TestSuite.health: ["tests/test_health.py"],
    TestSuite.family: ["tests/test_family.py"],
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
