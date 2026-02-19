import type { AnalysisData, AnalyzeRequest } from "./api";
import { getCurrentUser } from "./auth";

export interface Message {
  role: "user" | "assistant";
  content: string;
}

export interface HistoryEntry {
  id: string;
  name: string;
  createdAt: string;
  request: AnalyzeRequest;
  analysis: AnalysisData;
  messages: Message[];
  sessionId: string;
}

function getStorageKey(): string {
  const user = getCurrentUser();
  if (user) return `saju-history-${user.id}`;
  return "saju-history";
}

export function getHistory(): HistoryEntry[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(getStorageKey());
    if (!raw) return [];
    return JSON.parse(raw) as HistoryEntry[];
  } catch {
    return [];
  }
}

export function saveHistory(entry: HistoryEntry): void {
  const key = getStorageKey();
  const history = getHistory();
  const idx = history.findIndex((h) => h.id === entry.id);
  if (idx >= 0) {
    history[idx] = entry;
  } else {
    history.unshift(entry);
  }
  const trimmed = history.slice(0, 50);
  localStorage.setItem(key, JSON.stringify(trimmed));
}

export function updateHistoryMessages(
  id: string,
  messages: Message[]
): void {
  const key = getStorageKey();
  const history = getHistory();
  const entry = history.find((h) => h.id === id);
  if (entry) {
    entry.messages = messages;
    localStorage.setItem(key, JSON.stringify(history));
  }
}

export function deleteHistoryEntry(id: string): void {
  const key = getStorageKey();
  const history = getHistory().filter((h) => h.id !== id);
  localStorage.setItem(key, JSON.stringify(history));
}

export function clearHistory(): void {
  localStorage.removeItem(getStorageKey());
}

/**
 * 기존(로그인 전) 히스토리에서 displayName과 일치하는 항목을
 * 현재 로그인된 사용자의 히스토리로 이전합니다.
 * 이미 이전된 항목(같은 id)은 건너뜁니다.
 */
export function migrateMatchingHistory(displayName: string): number {
  if (typeof window === "undefined") return 0;

  const OLD_KEY = "saju-history";
  try {
    const oldRaw = localStorage.getItem(OLD_KEY);
    if (!oldRaw) return 0;

    const oldHistory = JSON.parse(oldRaw) as HistoryEntry[];
    const matching = oldHistory.filter(
      (entry) => entry.name.trim() === displayName.trim()
    );
    if (matching.length === 0) return 0;

    // 현재 사용자 히스토리에 병합
    const userKey = getStorageKey();
    const userHistory = getHistory();
    const existingIds = new Set(userHistory.map((h) => h.id));

    let migrated = 0;
    for (const entry of matching) {
      if (!existingIds.has(entry.id)) {
        userHistory.push(entry);
        migrated++;
      }
    }

    if (migrated > 0) {
      // 날짜순 정렬 (최신 먼저)
      userHistory.sort(
        (a, b) =>
          new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
      );
      const trimmed = userHistory.slice(0, 50);
      localStorage.setItem(userKey, JSON.stringify(trimmed));

      // 이전된 항목은 기존 키에서 제거
      const remaining = oldHistory.filter(
        (entry) => entry.name.trim() !== displayName.trim()
      );
      if (remaining.length > 0) {
        localStorage.setItem(OLD_KEY, JSON.stringify(remaining));
      } else {
        localStorage.removeItem(OLD_KEY);
      }
    }

    return migrated;
  } catch {
    return 0;
  }
}
