// (2026-11-25) @Gomchiiii 팩스 단말과 송수신 상태를 확인할 화면을 정의하는 파일입니다.

export function TerminalStatusPage() {
  return (
    <div className="page">
      <header className="page-header">
        <p className="eyebrow">TERMINAL STATUS</p>
        <h1>단말 상태</h1>
        <p className="description">팩스 단말과 송수신 상태를 확인하는 화면입니다.</p>
      </header>
      <section className="panel empty-state">
        <strong>단말 상태 기능 구현 예정</strong>
      </section>
    </div>
  );
}
