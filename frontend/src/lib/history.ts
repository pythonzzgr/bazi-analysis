import type { AnalysisData, AnalyzeRequest } from "./api";

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

const STORAGE_KEY = "saju-history";

export function getHistory(): HistoryEntry[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    return JSON.parse(raw) as HistoryEntry[];
  } catch {
    return [];
  }
}

export function saveHistory(entry: HistoryEntry): void {
  const history = getHistory();
  // 같은 id가 있으면 업데이트, 없으면 앞에 추가
  const idx = history.findIndex((h) => h.id === entry.id);
  if (idx >= 0) {
    history[idx] = entry;
  } else {
    history.unshift(entry);
  }
  // 최대 50개까지만 저장
  const trimmed = history.slice(0, 50);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed));
}

export function updateHistoryMessages(
  id: string,
  messages: Message[]
): void {
  const history = getHistory();
  const entry = history.find((h) => h.id === id);
  if (entry) {
    entry.messages = messages;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
  }
}

export function deleteHistoryEntry(id: string): void {
  const history = getHistory().filter((h) => h.id !== id);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
}

export function clearHistory(): void {
  localStorage.removeItem(STORAGE_KEY);
}
