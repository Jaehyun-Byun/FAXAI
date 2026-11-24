// (2026-11-25) @Gomchiiii FAXAI 웹 화면의 최상위 React 컴포넌트를 정의하는 파일입니다.

import { Navigate, Route, Routes } from "react-router-dom";

import { AppNavigation } from "./components/AppNavigation";
import { ArchivePage } from "./pages/ArchivePage";
import { DashboardPage } from "./pages/DashboardPage";
import { DataRegistrationPage } from "./pages/DataRegistrationPage";
import { DeveloperPage } from "./pages/DeveloperPage";
import { LetterGenerationPage } from "./pages/LetterGenerationPage";
import { MemoryReviewPage } from "./pages/MemoryReviewPage";
import { TerminalStatusPage } from "./pages/TerminalStatusPage";


export function App() {
  return (
    <div className="app-shell">
      <AppNavigation />
      <main className="app-content">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/data" element={<DataRegistrationPage />} />
          <Route path="/memories" element={<MemoryReviewPage />} />
          <Route path="/letters" element={<LetterGenerationPage />} />
          <Route path="/archive" element={<ArchivePage />} />
          <Route path="/terminal" element={<TerminalStatusPage />} />
          {import.meta.env.DEV && (
            <Route path="/dev" element={<DeveloperPage />} />
          )}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}
