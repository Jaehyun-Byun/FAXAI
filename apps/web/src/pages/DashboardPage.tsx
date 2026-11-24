// (2026-11-25) @Gomchiiii FAXAI의 주요 상태와 활동을 보여줄 대시보드 화면을 정의하는 파일입니다.

export function DashboardPage() {
  return (
    <div className="page">
      <header className="page-header">
        <p className="eyebrow">OVERVIEW</p>
        <h1>대시보드</h1>
        <p className="description">FAXAI의 주요 상태를 확인하는 화면입니다.</p>
      </header>
      <section className="panel empty-state">
        <strong>대시보드 기능 구현 예정</strong>
        <p>이후 기능이 추가되면 주요 활동을 이곳에 요약합니다.</p>
      </section>
    </div>
  );
}
