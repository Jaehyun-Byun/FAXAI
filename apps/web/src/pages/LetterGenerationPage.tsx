// (2026-11-25) @Gomchiiii 임의 한국어 답장을 생성하고 자동 보관 결과를 보여주는 화면을 정의하는 파일입니다.

import { useState } from "react";

import "./LetterGenerationPage.css";


type GeneratedLetter = {
  id: number;
  content: string;
  generated_at: string;
};

const LETTER_API_URL = "http://127.0.0.1:8000/letters";

export function LetterGenerationPage() {
  const [letter, setLetter] = useState<GeneratedLetter | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  async function generateLetter() {
    setIsGenerating(true);
    setErrorMessage("");

    try {
      const response = await fetch(LETTER_API_URL, { method: "POST" });
      if (!response.ok) {
        throw new Error("편지를 생성하지 못했습니다.");
      }
      setLetter((await response.json()) as GeneratedLetter);
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "편지를 생성하지 못했습니다.",
      );
    } finally {
      setIsGenerating(false);
    }
  }

  return (
    <div className="page letter-generation-page">
      <header className="page-header">
        <p className="eyebrow">LETTER GENERATION</p>
        <h1>편지 생성</h1>
        <p className="description">
          임의의 한국어 답장을 생성하고 보관함 데이터베이스에 자동 저장합니다.
        </p>
      </header>

      <section className="panel letter-generator">
        <div>
          <h2>임의 답장</h2>
          <p>현재는 미리 준비된 문장 중 하나를 무작위로 선택합니다.</p>
        </div>
        <button type="button" disabled={isGenerating} onClick={generateLetter}>
          {isGenerating ? "생성 중..." : "편지 생성"}
        </button>
      </section>

      {errorMessage && <p className="letter-error">{errorMessage}</p>}

      {letter && (
        <section className="panel generated-letter">
          <div className="letter-meta">
            <span>보관 번호 #{letter.id}</span>
            <time dateTime={letter.generated_at}>
              {new Date(letter.generated_at).toLocaleString("ko-KR")}
            </time>
          </div>
          <p>{letter.content}</p>
          <small>생성과 동시에 archive.db에 저장되었습니다.</small>
        </section>
      )}
    </div>
  );
}
