// (2026-11-25) @Gomchiiii FAXAI의 여섯 화면으로 이동하는 공통 탐색 메뉴를 정의하는 파일입니다.

import { NavLink } from "react-router-dom";

import "./AppNavigation.css";


const navigationItems = [
  { to: "/", label: "대시보드", end: true },
  { to: "/data", label: "자료 등록" },
  { to: "/memories", label: "메모리 검토" },
  { to: "/letters", label: "편지 생성" },
  { to: "/archive", label: "보관함" },
  { to: "/terminal", label: "단말 상태" },
];

export function AppNavigation() {
  return (
    <aside className="app-navigation">
      <div className="brand">
        <span className="brand-mark">F</span>
        <div>
          <strong>FAXAI</strong>
          <small>LOCAL DEMO</small>
        </div>
      </div>

      <nav aria-label="주요 화면">
        <ul>
          {navigationItems.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  isActive ? "navigation-link active" : "navigation-link"
                }
              >
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
}
