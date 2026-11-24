# FAXAI

로컬 MVP 개발 환경입니다. 아래 명령은 Windows PowerShell 기준입니다.

## 필수 도구

- Node.js 22 이상
- npm
- [uv](https://docs.astral.sh/uv/)

## 최초 설치

프로젝트 루트에서 실행합니다.

```powershell
npm.cmd install
uv venv .venv --python 3.12
uv pip install --python .venv\Scripts\python.exe -r services\api\requirements.txt
```

## 실행

PowerShell 창 두 개를 열어 각각 실행합니다.

웹:

```powershell
npm.cmd run dev:web
```

API:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --app-dir services\api
```

개발 테스트 화면을 사용할 때는 API를 다음처럼 실행합니다.

```powershell
$env:FAXAI_DEV_MODE="1"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --app-dir services\api
```

접속 주소:

- 웹: <http://localhost:5173>
- API 문서: <http://127.0.0.1:8000/docs>
- API 상태 확인: <http://127.0.0.1:8000/health>
- 개발 도구: <http://localhost:5173/dev>

## 웹 빌드

```powershell
npm.cmd run build:web
```

## API 테스트

```powershell
cd services\api
..\..\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
cd ..\..
```

## Swagger API 문서

API 실행 후 <http://127.0.0.1:8000/docs>에 접속합니다. 사용할 API를 펼치고 `Try it out`, `Execute` 순서로 누르면 요청과 응답을 확인할 수 있습니다.

## 데이터 저장 위치

가족 기본정보는 최초 저장 시 `data/family.db`에 생성됩니다. 이 파일은 Git에서 제외됩니다.

## 프로젝트 구조

```text
FAXAI/
├─ apps/web/              # React 웹앱
├─ services/api/app/      # FastAPI 애플리케이션
├─ services/api/tests/    # API 자동 테스트
├─ data/family.db         # 로컬 가족 기본정보 DB
└─ docs/                  # 프로젝트 문서
```

macOS와 Linux에서는 `npm.cmd` 대신 `npm`, `.venv\Scripts\python.exe` 대신 `.venv/bin/python`을 사용합니다.
