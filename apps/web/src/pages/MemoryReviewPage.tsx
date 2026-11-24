// (2026-11-25) @Gomchiiii 등록된 메모리를 확인하고 관리할 화면을 정의하는 파일입니다.

import { FormEvent, useEffect, useState } from "react";

import "./MemoryReviewPage.css";


type TextMemory = {
  id: number;
  source_date: string;
  source_text: string;
  parent_age_at_source: number;
  created_at: string;
};

const MEMORY_API_URL = "http://127.0.0.1:8000/memories";

export function MemoryReviewPage() {
  const [memories, setMemories] = useState<TextMemory[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editDate, setEditDate] = useState("");
  const [editText, setEditText] = useState("");
  const [busyId, setBusyId] = useState<number | null>(null);

  useEffect(() => {
    async function loadMemories() {
      try {
        const response = await fetch(MEMORY_API_URL);
        if (!response.ok) {
          throw new Error();
        }
        setMemories((await response.json()) as TextMemory[]);
      } catch {
        setErrorMessage("등록된 메모리를 불러오지 못했습니다.");
      } finally {
        setIsLoading(false);
      }
    }

    void loadMemories();
  }, []);

  function startEditing(memory: TextMemory) {
    setEditingId(memory.id);
    setEditDate(memory.source_date);
    setEditText(memory.source_text);
    setErrorMessage("");
  }

  function cancelEditing() {
    setEditingId(null);
    setEditDate("");
    setEditText("");
  }

  async function handleEditSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (editingId === null) {
      return;
    }

    setBusyId(editingId);
    setErrorMessage("");

    try {
      const response = await fetch(`${MEMORY_API_URL}/${editingId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source_date: editDate,
          source_text: editText,
        }),
      });

      if (response.status === 409) {
        throw new Error("가족 기본정보를 먼저 저장해 주세요.");
      }
      if (!response.ok) {
        throw new Error("수정할 날짜와 텍스트 내용을 확인해 주세요.");
      }

      const updatedMemory = (await response.json()) as TextMemory;
      setMemories((currentMemories) =>
        currentMemories
          .map((memory) =>
            memory.id === updatedMemory.id ? updatedMemory : memory,
          )
          .sort((left, right) =>
            right.source_date.localeCompare(left.source_date),
          ),
      );
      cancelEditing();
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "메모리를 수정하지 못했습니다.",
      );
    } finally {
      setBusyId(null);
    }
  }

  async function handleDelete(memory: TextMemory) {
    const shouldDelete = window.confirm(
      `${memory.source_date} 메모리를 삭제하시겠습니까?`,
    );
    if (!shouldDelete) {
      return;
    }

    setBusyId(memory.id);
    setErrorMessage("");

    try {
      const response = await fetch(`${MEMORY_API_URL}/${memory.id}`, {
        method: "DELETE",
      });
      if (!response.ok) {
        throw new Error("메모리를 삭제하지 못했습니다.");
      }

      setMemories((currentMemories) =>
        currentMemories.filter((item) => item.id !== memory.id),
      );
      if (editingId === memory.id) {
        cancelEditing();
      }
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "메모리를 삭제하지 못했습니다.",
      );
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="page memory-review-page">
      <header className="page-header">
        <p className="eyebrow">MEMORY REVIEW</p>
        <h1>메모리 검토</h1>
        <p className="description">
          등록된 텍스트 메모리를 확인하고 수정하거나 삭제합니다.
        </p>
      </header>

      {errorMessage && <p className="memory-error">{errorMessage}</p>}

      {isLoading ? (
        <section className="panel empty-state">메모리를 불러오는 중입니다.</section>
      ) : memories.length === 0 ? (
        <section className="panel empty-state">
          <strong>등록된 메모리가 없습니다.</strong>
          <p>자료 등록 화면에서 첫 번째 텍스트 메모리를 저장해 보세요.</p>
        </section>
      ) : (
        <div className="memory-list">
          {memories.map((memory) => (
            <article className="panel memory-card" key={memory.id}>
              {editingId === memory.id ? (
                <form className="memory-edit-form" onSubmit={handleEditSubmit}>
                  <label>
                    기록 날짜
                    <input
                      type="date"
                      required
                      value={editDate}
                      onChange={(event) => setEditDate(event.target.value)}
                    />
                  </label>
                  <label>
                    텍스트 내용
                    <textarea
                      required
                      maxLength={10000}
                      rows={7}
                      value={editText}
                      onChange={(event) => setEditText(event.target.value)}
                    />
                  </label>
                  <div className="memory-actions">
                    <button type="submit" disabled={busyId === memory.id}>
                      {busyId === memory.id ? "저장 중..." : "수정 내용 저장"}
                    </button>
                    <button
                      className="secondary-button"
                      type="button"
                      disabled={busyId === memory.id}
                      onClick={cancelEditing}
                    >
                      취소
                    </button>
                  </div>
                </form>
              ) : (
                <>
                  <div className="memory-meta">
                    <time dateTime={memory.source_date}>{memory.source_date}</time>
                    <span>부모 만 {memory.parent_age_at_source}세</span>
                  </div>
                  <p className="memory-text">{memory.source_text}</p>
                  <div className="memory-actions">
                    <button
                      type="button"
                      disabled={busyId === memory.id}
                      onClick={() => startEditing(memory)}
                    >
                      수정
                    </button>
                    <button
                      className="danger-button"
                      type="button"
                      disabled={busyId === memory.id}
                      onClick={() => handleDelete(memory)}
                    >
                      {busyId === memory.id ? "처리 중..." : "삭제"}
                    </button>
                  </div>
                </>
              )}
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
