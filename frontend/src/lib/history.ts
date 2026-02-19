/**
 * 히스토리 관리 - DB API 기반
 * 기존 localStorage 방식에서 백엔드 API로 전환
 */

export type { HistoryEntry } from "./api";
export type { AnalyzeRequest } from "./api";

export interface Message {
  role: "user" | "assistant";
  content: string;
}
