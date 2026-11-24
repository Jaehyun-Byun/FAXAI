// (2026-11-25) @Gomchiiii 생성된 편지를 조회할 보관함 화면을 정의하는 파일입니다.

import { useEffect, useState } from "react";

import "./ArchivePage.css";


type ArchivedLetterListItem = {
  id: number;
  content_preview: string;
  generated_at: string;
};

type ArchivedLetterDetail = {
  id: number;
  content: string;
  generated_at: string;
};

const LETTER_API_URL = "http://127.0.0.1:8000/letters";

export function ArchivePage() {
  const [letters, setLetters] = useState<ArchivedLetterListItem[]>([]);
  const [selectedLetter, setSelectedLetter] =
    useState<ArchivedLetterDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isDetailLoading, setIsDetailLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  async function loadLetterDetail(letterId: number) {
    setIsDetailLoading(true);
    setErrorMessage("");

    try {
      const response = await fetch(`${LETTER_API_URL}/${letterId}`);
      if (!response.ok) {
        throw new Error("편지 상세 내용을 불러오지 못했습니다.");
      }
      setSelectedLetter((await response.json()) as ArchivedLetterDetail);
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "편지 상세 내용을 불러오지 못했습니다.",
      );
    } finally {
      setIsDetailLoading(false);
    }
  }

  useEffect(() => {
    async function loadArchive() {
      try {
        const response = await fetch(LETTER_API_URL);
        if (!response.ok) {
          throw new Error();
        }

        const archivedLetters =
          (await response.json()) as ArchivedLetterListItem[];
        setLetters(archivedLetters);
        if (archivedLetters.length > 0) {
          await loadLetterDetail(archivedLetters[0].id);
        }
      } catch {
        setErrorMessage("보관된 편지 목록을 불러오지 못했습니다.");
      } finally {
        setIsLoading(false);
      }
    }

    void loadArchive();
  }, []);

  return (
    <div className="page archive-page">
      <header className="page-header">
        <p className="eyebrow">ARCHIVE</p>
        <h1>보관함</h1>
        <p className="description">
          생성된 편지 목록을 살펴보고 전체 내용을 확인합니다.
        </p>
      </header>

      {errorMessage && <p className="archive-error">{errorMessage}</p>}

      {isLoading ? (
        <section className="panel empty-state">보관함을 불러오는 중입니다.</section>
      ) : letters.length === 0 ? (
        <section className="panel empty-state">
          <strong>보관된 편지가 없습니다.</strong>
          <p>편지 생성 화면에서 첫 번째 편지를 만들어 보세요.</p>
        </section>
      ) : (
        <div className="archive-layout">
          <section className="panel archive-list">
            <h2>편지 목록</h2>
            <div className="archive-items">
              {letters.map((letter) => (
                <button
                  className={
                    selectedLetter?.id === letter.id
                      ? "archive-item active"
                      : "archive-item"
                  }
                  type="button"
                  key={letter.id}
                  onClick={() => loadLetterDetail(letter.id)}
                >
                  <span>#{letter.id}</span>
                  <time dateTime={letter.generated_at}>
                    {new Date(letter.generated_at).toLocaleString("ko-KR")}
                  </time>
                  <p>{letter.content_preview}</p>
                </button>
              ))}
            </div>
          </section>

          <section className="panel archive-detail">
            {isDetailLoading ? (
              <p className="detail-loading">편지를 불러오는 중입니다.</p>
            ) : selectedLetter ? (
              <>
                <div className="archive-detail-meta">
                  <strong>보관 번호 #{selectedLetter.id}</strong>
                  <time dateTime={selectedLetter.generated_at}>
                    {new Date(selectedLetter.generated_at).toLocaleString(
                      "ko-KR",
                    )}
                  </time>
                </div>
                <p className="archive-letter-content">
                  {selectedLetter.content}
                </p>
              </>
            ) : (
              <p className="detail-loading">확인할 편지를 선택해 주세요.</p>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
