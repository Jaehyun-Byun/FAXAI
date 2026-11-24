// (2026-11-25) @Gomchiiii 가족 기본정보와 자료를 등록하는 화면을 정의하는 파일입니다.

import { FormEvent, useEffect, useRef, useState } from "react";

import "./DataRegistrationPage.css";


type FamilyProfile = {
  parent_name: string;
  parent_birth_date: string;
  child_name: string;
  child_birth_date: string;
  child_age: number;
  matching_parent_date: string;
};

const FAMILY_API_URL = "http://127.0.0.1:8000/family/birth-information";

export function DataRegistrationPage() {
  const formRef = useRef<HTMLFormElement>(null);
  const [profile, setProfile] = useState<FamilyProfile | null>(null);
  const [message, setMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    async function loadFamilyProfile() {
      try {
        const response = await fetch(FAMILY_API_URL);
        if (response.status === 404) {
          return;
        }
        if (!response.ok) {
          throw new Error();
        }

        const savedProfile = (await response.json()) as FamilyProfile;
        const form = formRef.current;
        if (form) {
          (form.elements.namedItem("parentName") as HTMLInputElement).value =
            savedProfile.parent_name;
          (
            form.elements.namedItem("parentBirthDate") as HTMLInputElement
          ).value = savedProfile.parent_birth_date;
          (form.elements.namedItem("childName") as HTMLInputElement).value =
            savedProfile.child_name;
          (
            form.elements.namedItem("childBirthDate") as HTMLInputElement
          ).value = savedProfile.child_birth_date;
        }
        setProfile(savedProfile);
        setMessage("저장된 가족 기본정보를 불러왔습니다.");
      } catch {
        setMessage("저장된 가족 기본정보를 불러오지 못했습니다.");
      }
    }

    void loadFamilyProfile();
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const isUpdating = profile !== null;
    setIsSubmitting(true);
    setMessage("");

    const formData = new FormData(event.currentTarget);
    const requestBody = {
      parent_name: formData.get("parentName"),
      parent_birth_date: formData.get("parentBirthDate"),
      child_name: formData.get("childName"),
      child_birth_date: formData.get("childBirthDate"),
    };

    try {
      const response = await fetch(FAMILY_API_URL, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error("입력한 생년월일을 확인해 주세요.");
      }

      const savedProfile = (await response.json()) as FamilyProfile;
      setProfile(savedProfile);
      setIsEditing(false);
      setMessage(
        isUpdating
          ? "가족 기본정보를 수정했습니다."
          : "가족 기본정보를 저장했습니다.",
      );
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : "정보를 저장하지 못했습니다.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleEdit() {
    const shouldEdit = window.confirm("가족 기본정보를 수정하시겠습니까?");
    if (shouldEdit) {
      setIsEditing(true);
      setMessage("수정할 내용을 입력해 주세요.");
    }
  }

  async function handleReset() {
    const shouldReset = window.confirm(
      "저장된 가족 기본정보를 초기화하시겠습니까?",
    );
    if (!shouldReset) {
      return;
    }

    setIsResetting(true);
    setMessage("");

    try {
      const response = await fetch(FAMILY_API_URL, { method: "DELETE" });

      if (!response.ok) {
        throw new Error("가족 기본정보를 초기화하지 못했습니다.");
      }

      formRef.current?.reset();
      setProfile(null);
      setIsEditing(false);
      setMessage("가족 기본정보를 초기화했습니다.");
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "가족 기본정보를 초기화하지 못했습니다.",
      );
    } finally {
      setIsResetting(false);
    }
  }

  return (
    <div className="page data-registration-page">
      <header className="page-header">
        <p className="eyebrow">DATA REGISTRATION</p>
        <h1>자료 등록</h1>
        <p className="description">
          부모와 자녀의 정보를 저장하고 두 사람이 같은 나이인 시점을
          계산합니다.
        </p>
      </header>

      <section className="panel">
        <h2>가족 기본정보</h2>
        <form ref={formRef} onSubmit={handleSubmit}>
          <fieldset>
            <legend>부모 정보</legend>
            <label>
              이름
              <input
                name="parentName"
                type="text"
                required
                maxLength={100}
                disabled={profile !== null && !isEditing}
              />
            </label>
            <label>
              생년월일
              <input
                name="parentBirthDate"
                type="date"
                required
                disabled={profile !== null && !isEditing}
              />
            </label>
          </fieldset>

          <fieldset>
            <legend>자녀 정보</legend>
            <label>
              이름
              <input
                name="childName"
                type="text"
                required
                maxLength={100}
                disabled={profile !== null && !isEditing}
              />
            </label>
            <label>
              생년월일
              <input
                name="childBirthDate"
                type="date"
                required
                disabled={profile !== null && !isEditing}
              />
            </label>
          </fieldset>

          <div className="actions">
            {profile !== null && !isEditing ? (
              <button
                type="button"
                disabled={isResetting}
                onClick={handleEdit}
              >
                가족 정보 수정
              </button>
            ) : (
              <button type="submit" disabled={isSubmitting || isResetting}>
                {isSubmitting
                  ? "저장 중..."
                  : profile === null
                    ? "저장하고 계산하기"
                    : "수정 내용 저장"}
              </button>
            )}
            <button
              className="secondary-button"
              type="button"
              disabled={isSubmitting || isResetting}
              onClick={handleReset}
            >
              {isResetting ? "초기화 중..." : "가족 정보 초기화"}
            </button>
          </div>
        </form>

        {message && <p className="message">{message}</p>}

        {profile && (
          <div className="result">
            <p>
              현재 {profile.child_name}의 나이는{" "}
              <strong>만 {profile.child_age}세</strong>입니다.
            </p>
            <p>
              {profile.parent_name}가 같은 나이였던 시점은{" "}
              <strong>{profile.matching_parent_date}</strong>입니다.
            </p>
          </div>
        )}
      </section>
    </div>
  );
}
