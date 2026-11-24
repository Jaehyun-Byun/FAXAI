// (2026-11-25) @Gomchiiii 팩스 단말과 송수신 상태를 확인할 화면을 정의하는 파일입니다.

import { useEffect, useState } from "react";

import "./TerminalStatusPage.css";


type FaxEvent = {
  id: number;
  direction: "incoming" | "outgoing";
  remote_number: string;
  text: string;
  status: "received" | "mock_sent" | "failed";
  created_at: string;
};

const FAX_EVENTS_API_URL = "http://127.0.0.1:8000/fax/events";

const statusLabels = {
  received: "수신 완료",
  mock_sent: "발송 완료",
  failed: "발송 실패",
};

export function TerminalStatusPage() {
  const [events, setEvents] = useState<FaxEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    async function loadFaxEvents() {
      try {
        const response = await fetch(FAX_EVENTS_API_URL);
        if (!response.ok) {
          throw new Error();
        }
        setEvents((await response.json()) as FaxEvent[]);
      } catch {
        setErrorMessage("팩스 송수신 상태를 불러오지 못했습니다.");
      } finally {
        setIsLoading(false);
      }
    }

    void loadFaxEvents();
  }, []);

  return (
    <div className="page terminal-status-page">
      <header className="page-header">
        <p className="eyebrow">TERMINAL STATUS</p>
        <h1>단말 상태</h1>
        <p className="description">
          Mock 팩스의 수신·발송·실패 기록을 최신순으로 확인합니다.
        </p>
      </header>

      {errorMessage && <p className="fax-status-error">{errorMessage}</p>}

      {isLoading ? (
        <section className="panel empty-state">팩스 기록을 불러오는 중입니다.</section>
      ) : events.length === 0 ? (
        <section className="panel empty-state">
          <strong>팩스 송수신 기록이 없습니다.</strong>
          <p>Mock 팩스 API를 실행하면 이곳에 상태가 표시됩니다.</p>
        </section>
      ) : (
        <div className="fax-event-list">
          {events.map((event) => (
            <article className="panel fax-event" key={event.id}>
              <div className="fax-event-heading">
                <div>
                  <strong>
                    {event.direction === "incoming" ? "수신" : "발송"} #{event.id}
                  </strong>
                  <span>{event.remote_number}</span>
                </div>
                <span className={`fax-status ${event.status}`}>
                  {statusLabels[event.status]}
                </span>
              </div>
              <p>{event.text}</p>
              <time dateTime={event.created_at}>
                {new Date(event.created_at).toLocaleString("ko-KR")}
              </time>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
