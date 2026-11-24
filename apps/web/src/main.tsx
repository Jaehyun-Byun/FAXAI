// (2026-11-25) @Gomchiiii React 애플리케이션을 브라우저 HTML에 연결하여 실행하는 파일입니다.

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import { App } from "./App";
import "./styles/global.css";
import "./styles/layout.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
);

