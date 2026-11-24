// (2026-11-25) @Gomchiiii 로컬 개발자가 테스트·샘플 생성·Mock 팩스 송수신·MVP DB 초기화를 실행하는 화면을 정의하는 파일입니다.

import { FormEvent, useState } from "react";

import "./DeveloperPage.css";


type TestSuite =
  | "all"
  | "dashboard"
  | "health"
  | "family"
  | "fax"
  | "letter"
  | "memory";

type FaxStatusScenario = "received" | "mock_sent" | "failed";

type TestRunResult = {
  suite: TestSuite;
  status: "passed" | "failed";
  exit_code: number;
  output: string;
};

const TEST_API_URL = "http://127.0.0.1:8000/dev/tests";
const SAMPLE_DATA_API_URL = "http://127.0.0.1:8000/dev/sample-data";
const DATABASE_RESET_API_URL = "http://127.0.0.1:8000/dev/databases";
const MOCK_FAX_INCOMING_API_URL = "http://127.0.0.1:8000/fax/mock/incoming";
const MOCK_FAX_SEND_API_URL = "http://127.0.0.1:8000/fax/mock/send";
const FAX_STATUS_SCENARIO_API_URL = "http://127.0.0.1:8000/dev/fax-status";

const testSuites: Array<{
  id: TestSuite;
  label: string;
  description: string;
}> = [
  { id: "all", label: "전체 테스트", description: "모든 API 테스트 실행" },
  {
    id: "dashboard",
    label: "대시보드",
    description: "test_dashboard.py 실행",
  },
  { id: "health", label: "API 상태", description: "test_health.py 실행" },
  { id: "family", label: "가족 프로필", description: "test_family.py 실행" },
  { id: "fax", label: "Mock 팩스", description: "test_fax.py 실행" },
  { id: "letter", label: "편지 생성", description: "test_letter.py 실행" },
  { id: "memory", label: "메모리", description: "test_memory.py 실행" },
];

export function DeveloperPage() {
  const [runningSuite, setRunningSuite] = useState<TestSuite | null>(null);
  const [result, setResult] = useState<TestRunResult | null>(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [isCreatingSample, setIsCreatingSample] = useState(false);
  const [sampleMessage, setSampleMessage] = useState("");
  const [isHardResetting, setIsHardResetting] = useState(false);
  const [resetMessage, setResetMessage] = useState("");
  const [receiveNumber, setReceiveNumber] = useState("02-1234-5678");
  const [receiveText, setReceiveText] = useState("오늘 잘 지내고 있니?");
  const [sendNumber, setSendNumber] = useState("02-1234-5678");
  const [sendText, setSendText] = useState("오늘도 좋은 하루 보내렴.");
  const [isReceivingFax, setIsReceivingFax] = useState(false);
  const [isSendingFax, setIsSendingFax] = useState(false);
  const [runningFaxScenario, setRunningFaxScenario] =
    useState<FaxStatusScenario | null>(null);
  const [faxMessage, setFaxMessage] = useState("");

  const isFaxBusy =
    isReceivingFax || isSendingFax || runningFaxScenario !== null;

  async function runTestSuite(suite: TestSuite) {
    setRunningSuite(suite);
    setResult(null);
    setErrorMessage("");

    try {
      const response = await fetch(`${TEST_API_URL}/${suite}`, {
        method: "POST",
      });
      if (response.status === 404) {
        throw new Error("API 서버를 FAXAI_DEV_MODE=1로 실행해 주세요.");
      }
      if (response.status === 409) {
        throw new Error("다른 테스트가 실행 중입니다.");
      }
      if (!response.ok) {
        throw new Error("테스트를 실행하지 못했습니다.");
      }

      setResult((await response.json()) as TestRunResult);
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "테스트를 실행하지 못했습니다.",
      );
    } finally {
      setRunningSuite(null);
    }
  }

  async function createSampleData() {
    setIsCreatingSample(true);
    setSampleMessage("");
    setErrorMessage("");

    try {
      const response = await fetch(SAMPLE_DATA_API_URL, { method: "POST" });
      if (response.status === 404) {
        throw new Error("API 서버를 FAXAI_DEV_MODE=1로 실행해 주세요.");
      }
      if (response.status === 409) {
        throw new Error("기존 데이터가 있어 샘플 데이터를 생성하지 않았습니다.");
      }
      if (!response.ok) {
        throw new Error("샘플 데이터를 생성하지 못했습니다.");
      }

      const created = (await response.json()) as {
        memories_created: number;
      };
      setSampleMessage(
        `샘플 가족과 메모리 ${created.memories_created}개를 생성했습니다.`,
      );
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "샘플 데이터를 생성하지 못했습니다.",
      );
    } finally {
      setIsCreatingSample(false);
    }
  }

  async function hardResetDatabases() {
    const shouldReset = window.confirm(
      "family.db, memory.db, archive.db, fax.db를 모두 삭제합니다. 이 작업은 복구할 수 없습니다. 계속하시겠습니까?",
    );
    if (!shouldReset) {
      return;
    }

    setIsHardResetting(true);
    setResetMessage("");
    setSampleMessage("");
    setErrorMessage("");

    try {
      const response = await fetch(DATABASE_RESET_API_URL, {
        method: "DELETE",
      });
      if (response.status === 404) {
        throw new Error("API 서버를 FAXAI_DEV_MODE=1로 실행해 주세요.");
      }
      if (!response.ok) {
        throw new Error("로컬 DB를 초기화하지 못했습니다.");
      }

      const resetResult = (await response.json()) as {
        deleted_databases: string[];
      };
      setResetMessage(
        resetResult.deleted_databases.length > 0
          ? `${resetResult.deleted_databases.join(", ")}를 삭제했습니다.`
          : "초기화할 DB 파일이 없습니다.",
      );
      setResult(null);
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "로컬 DB를 초기화하지 못했습니다.",
      );
    } finally {
      setIsHardResetting(false);
    }
  }

  async function receiveMockFax(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsReceivingFax(true);
    setFaxMessage("");
    setErrorMessage("");

    try {
      const response = await fetch(MOCK_FAX_INCOMING_API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          sender_number: receiveNumber,
          text: receiveText,
        }),
      });
      if (!response.ok) {
        throw new Error("Mock 팩스 수신을 실행하지 못했습니다.");
      }

      const result = (await response.json()) as {
        incoming: { id: number; status: string };
        reply: { id: number; status: string };
      };
      setFaxMessage(
        `수신 #${result.incoming.id} ${result.incoming.status}, 자동 회신 #${result.reply.id} ${result.reply.status}`,
      );
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Mock 팩스 수신을 실행하지 못했습니다.",
      );
    } finally {
      setIsReceivingFax(false);
    }
  }

  async function sendMockFax(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSendingFax(true);
    setFaxMessage("");
    setErrorMessage("");

    try {
      const response = await fetch(MOCK_FAX_SEND_API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          recipient_number: sendNumber,
          text: sendText,
        }),
      });
      if (!response.ok) {
        throw new Error("Mock 팩스 발신을 실행하지 못했습니다.");
      }

      const result = (await response.json()) as {
        id: number;
        status: string;
      };
      setFaxMessage(`발신 #${result.id} ${result.status}`);
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Mock 팩스 발신을 실행하지 못했습니다.",
      );
    } finally {
      setIsSendingFax(false);
    }
  }

  async function createFaxStatusScenario(eventStatus: FaxStatusScenario) {
    setRunningFaxScenario(eventStatus);
    setFaxMessage("");
    setErrorMessage("");

    try {
      const response = await fetch(
        `${FAX_STATUS_SCENARIO_API_URL}/${eventStatus}`,
        { method: "POST" },
      );
      if (response.status === 404) {
        throw new Error("API 서버를 FAXAI_DEV_MODE=1로 실행해 주세요.");
      }
      if (!response.ok) {
        throw new Error("팩스 상태 시나리오를 생성하지 못했습니다.");
      }

      const result = (await response.json()) as {
        id: number;
        status: string;
      };
      setFaxMessage(`상태 이벤트 #${result.id} ${result.status} 생성 완료`);
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "팩스 상태 시나리오를 생성하지 못했습니다.",
      );
    } finally {
      setRunningFaxScenario(null);
    }
  }

  return (
    <div className="page developer-page">
      <header className="page-header">
        <p className="eyebrow">DEVELOPMENT ONLY</p>
        <h1>개발 도구</h1>
        <p className="description">
          허용된 API 테스트를 선택해 실행하고 결과를 확인합니다.
        </p>
      </header>

      <section className="panel dev-test-list">
        {testSuites.map((suite) => (
          <div className="dev-test-item" key={suite.id}>
            <div>
              <strong>{suite.label}</strong>
              <p>{suite.description}</p>
            </div>
            <button
              type="button"
              disabled={runningSuite !== null || isHardResetting || isFaxBusy}
              onClick={() => runTestSuite(suite.id)}
            >
              {runningSuite === suite.id ? "실행 중..." : "실행"}
            </button>
          </div>
        ))}
      </section>

      <section className="panel dev-sample-data">
        <div>
          <h2>샘플 데이터</h2>
          <p>
            데이터베이스가 비어 있을 때 샘플 가족과 텍스트 메모리 3개를
            생성합니다.
          </p>
        </div>
        <button
          type="button"
          disabled={
            isCreatingSample ||
            runningSuite !== null ||
            isHardResetting ||
            isFaxBusy
          }
          onClick={createSampleData}
        >
          {isCreatingSample ? "생성 중..." : "샘플 데이터 생성"}
        </button>
      </section>

      {sampleMessage && <p className="dev-success">{sampleMessage}</p>}

      <section className="dev-fax-grid">
        <form className="panel dev-fax-form" onSubmit={receiveMockFax}>
          <div>
            <h2>Mock 팩스 수신</h2>
            <p>가짜 수신 웹훅과 같은 번호 자동 회신을 실행합니다.</p>
          </div>
          <label>
            발신 번호
            <input
              type="text"
              required
              value={receiveNumber}
              onChange={(event) => setReceiveNumber(event.target.value)}
            />
          </label>
          <label>
            수신 텍스트
            <textarea
              required
              rows={4}
              maxLength={10000}
              value={receiveText}
              onChange={(event) => setReceiveText(event.target.value)}
            />
          </label>
          <button type="submit" disabled={isFaxBusy || isHardResetting}>
            {isReceivingFax ? "수신 중..." : "팩스 수신 실행"}
          </button>
        </form>

        <form className="panel dev-fax-form" onSubmit={sendMockFax}>
          <div>
            <h2>Mock 팩스 발신</h2>
            <p>Mock Provider를 통해 지정한 번호로 발신합니다.</p>
          </div>
          <label>
            수신 번호
            <input
              type="text"
              required
              value={sendNumber}
              onChange={(event) => setSendNumber(event.target.value)}
            />
          </label>
          <label>
            발송 텍스트
            <textarea
              required
              rows={4}
              maxLength={10000}
              value={sendText}
              onChange={(event) => setSendText(event.target.value)}
            />
          </label>
          <button type="submit" disabled={isFaxBusy || isHardResetting}>
            {isSendingFax ? "발신 중..." : "팩스 발신 실행"}
          </button>
        </form>
      </section>

      {faxMessage && <p className="dev-success">{faxMessage}</p>}

      <section className="panel dev-fax-scenarios">
        <div>
          <h2>단말 상태 시나리오</h2>
          <p>
            단말 상태 화면에서 확인할 수신 완료·발송 완료·발송 실패 이벤트를
            생성합니다.
          </p>
        </div>
        <div className="scenario-buttons">
          <button
            type="button"
            disabled={isFaxBusy || isHardResetting}
            onClick={() => createFaxStatusScenario("received")}
          >
            {runningFaxScenario === "received" ? "생성 중..." : "수신 완료"}
          </button>
          <button
            type="button"
            disabled={isFaxBusy || isHardResetting}
            onClick={() => createFaxStatusScenario("mock_sent")}
          >
            {runningFaxScenario === "mock_sent" ? "생성 중..." : "발송 완료"}
          </button>
          <button
            className="status-failed-button"
            type="button"
            disabled={isFaxBusy || isHardResetting}
            onClick={() => createFaxStatusScenario("failed")}
          >
            {runningFaxScenario === "failed" ? "생성 중..." : "발송 실패"}
          </button>
        </div>
      </section>

      <section className="panel dev-danger-zone">
        <div>
          <h2>하드 리셋</h2>
          <p>
            가족·메모리·편지·팩스 DB를 모두 삭제합니다. 삭제한 데이터는
            복구할 수 없습니다.
          </p>
        </div>
        <button
          className="danger-button"
          type="button"
          disabled={
            isHardResetting ||
            isCreatingSample ||
            runningSuite !== null ||
            isFaxBusy
          }
          onClick={hardResetDatabases}
        >
          {isHardResetting ? "초기화 중..." : "모든 DB 초기화"}
        </button>
      </section>

      {resetMessage && <p className="dev-success">{resetMessage}</p>}

      {errorMessage && <p className="dev-error">{errorMessage}</p>}

      {result && (
        <section className="panel dev-result">
          <div className="dev-result-header">
            <h2>실행 결과</h2>
            <span className={`test-status ${result.status}`}>
              {result.status === "passed" ? "통과" : "실패"}
            </span>
          </div>
          <pre>{result.output || `종료 코드: ${result.exit_code}`}</pre>
        </section>
      )}
    </div>
  );
}
