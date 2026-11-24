// (2026-11-25) @Gomchiiii React 웹앱을 개발하고 빌드하기 위한 Vite 설정을 정의하는 파일입니다.

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
});

