// (2026-11-25) @Gomchiiii FAXAI의 주요 상태와 활동을 보여줄 대시보드 화면을 정의하는 파일입니다.

import { useEffect, useState } from "react";

import "./DashboardPage.css";


type RecentFax = {
  id: number;
  direction: "incoming" | "outgoing";
  remote_number: string;
  text: string;
  status: string;
  created_at: string;
};

type DashboardSummary = {
  fax_count: number;
  memory_count: number;
  letter_count: number;
  recent_faxes: RecentFax[];
};

const DASHBOARD_API_URL = "http://127.0.0.1:8000/dashboard/summary";

export function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    async function loadDashboardSummary() {
      try {
        const response = await fetch(DASHBOARD_API_URL);
        if (!response.ok) {
          throw new Error();
        }
        setSummary((await response.json()) as DashboardSummary);
      } catch {
        setErrorMessage("대시보드 요약을 불러오지 못했습니다.");
      }
    }

    void loadDashboardSummary();
  }, []);

  return (
    <div className="page dashboard-page">
      <header className="page-header">
        <p className="eyebrow">OVERVIEW</p>
        <h1>대시보드</h1>
        <p className="description">
          FAXAI의 저장 자료와 최근 팩스 활동을 확인합니다.
        </p>
      </header>

      {errorMessage && <p className="dashboard-error">{errorMessage}</p>}

      {summary ? (
        <>
          <section className="summary-grid">
            <article className="panel summary-card">
              <span>팩스 이벤트</span>
              <strong>{summary.fax_count}</strong>
            </article>
            <article className="panel summary-card">
              <span>메모리</span>
              <strong>{summary.memory_count}</strong>
            </article>
            <article className="panel summary-card">
              <span>보관 편지</span>
              <strong>{summary.letter_count}</strong>
            </article>
          </section>

          <section className="panel recent-faxes">
            <h2>최근 팩스</h2>
            {summary.recent_faxes.length === 0 ? (
              <p className="dashboard-empty">최근 팩스 활동이 없습니다.</p>
            ) : (
              <div className="recent-fax-list">
                {summary.recent_faxes.map((fax) => (
                  <div className="recent-fax-item" key={fax.id}>
                    <div>
                      <strong>
                        {fax.direction === "incoming" ? "수신" : "발송"}
                      </strong>
                      <span>{fax.remote_number}</span>
                    </div>
                    <p>{fax.text}</p>
                    <time dateTime={fax.created_at}>
                      {new Date(fax.created_at).toLocaleString("ko-KR")}
                    </time>
                  </div>
                ))}
              </div>
            )}
          </section>
        </>
      ) : (
        !errorMessage && (
          <section className="panel empty-state">
            대시보드 요약을 불러오는 중입니다.
          </section>
        )
      )}
    </div>
  );
}
