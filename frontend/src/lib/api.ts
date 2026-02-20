const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000/api";

export interface AnalyzeRequest {
  name: string;
  year: number;
  month: number;
  day: number;
  hour: number;
  minute: number;
  gender: string;
  is_lunar: boolean;
  is_leap_month: boolean;
}

export interface LeapMonthResponse {
  year: number;
  leap_month: number;
}

export async function getLeapMonth(year: number): Promise<LeapMonthResponse> {
  const res = await fetch(`${API_BASE}/leap-month/${year}`);
  if (!res.ok) return { year, leap_month: 0 };
  return res.json();
}

export interface PillarData {
  stem: string;
  branch: string;
  stem_ko: string;
  branch_ko: string;
  ganzi: string;
  ganzi_ko: string;
  stem_element: string;
  branch_element: string;
  stem_polarity: string;
  branch_polarity: string;
  hidden_stems: { stem: string; stem_ko: string; days: number }[];
  nayin: string;
}

export interface AnalysisData {
  eight_characters: {
    name: string;
    gender: string;
    solar_date: string;
    lunar_date: string;
    is_lunar_input: boolean;
    is_leap_month: boolean;
    season: string;
    pillars: {
      year: PillarData;
      month: PillarData;
      day: PillarData;
      time: PillarData;
    };
    day_stem: {
      stem: string;
      stem_ko: string;
      element: string;
      polarity: string;
    };
  };
  element_analysis: {
    element_stats: Record<
      string,
      {
        element: string;
        element_ko: string;
        element_en: string;
        count: number;
        score: number;
        ratio: number;
      }
    >;
    strongest_element: string;
    weakest_element: string;
    missing_elements: string[];
  };
  strength_analysis: {
    strength_status: string;
    strength_level: string;
    analysis: {
      self_support_ratio: number;
      is_deuk_ryeong: boolean;
      is_deuk_ji: boolean;
      is_deuk_se: boolean;
    };
    description: string;
  };
  yong_shin_analysis: {
    yong_shin: string;
    yong_shin_ko: string;
    hee_shin: string;
    hee_shin_ko: string;
    gi_shin: string;
    gi_shin_ko: string;
    selection_method: string;
    selection_reason: string;
    recommendations: {
      lucky_colors: string[];
      lucky_direction: string;
      lucky_numbers: number[];
      career_advice: string;
    };
  };
  fortune_analysis: {
    current_age: number;
    current_da_yun: {
      ganzi: string;
      ganzi_ko: string;
      start_age: number;
      end_age: number;
      score: number;
      rating: string;
    } | null;
    yearly_fortunes: {
      year: number;
      ganzi: string;
      ganzi_ko: string;
      score: number;
      rating: string;
      summary: string;
    }[];
  };
  [key: string]: unknown;
}

export interface AnalyzeResponse {
  session_id: string;
  analysis_id: string;
  analysis: AnalysisData;
}

export async function analyzeSaju(
  data: AnalyzeRequest & { user_id?: string },
): Promise<AnalyzeResponse> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 60_000);

  try {
    const res = await fetch(`${API_BASE}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
      signal: controller.signal,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "분석 중 오류가 발생했습니다.");
    }
    return res.json();
  } catch (e) {
    if (e instanceof DOMException && e.name === "AbortError") {
      throw new Error("분석 시간이 초과되었습니다. 다시 시도해주세요.");
    }
    throw e;
  } finally {
    clearTimeout(timeout);
  }
}

async function processSSEStream(
  res: Response,
  onDelta: (text: string) => void,
): Promise<void> {
  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    while (true) {
      const newlineIdx = buffer.indexOf("\n");
      if (newlineIdx === -1) break;

      const line = buffer.slice(0, newlineIdx);
      buffer = buffer.slice(newlineIdx + 1);

      if (line.startsWith("data: ")) {
        const payload = line.slice(6);
        if (payload === "[DONE]") return;
        try {
          const parsed = JSON.parse(payload);
          if (parsed.error) throw new Error(parsed.error);
          if (parsed.delta) onDelta(parsed.delta);
        } catch (e) {
          if (e instanceof Error && e.message !== "") throw e;
        }
      }
    }
  }
}

export async function streamReading(
  sessionId: string,
  onDelta: (text: string) => void,
  analysisId?: string,
): Promise<void> {
  const res = await fetch(`${API_BASE}/stream/reading`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, analysis_id: analysisId || "" }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "해석 생성 중 오류가 발생했습니다.");
  }
  if (!res.body) throw new Error("스트리밍 응답을 받을 수 없습니다.");
  await processSSEStream(res, onDelta);
}

export async function streamChat(
  sessionId: string,
  message: string,
  onDelta: (text: string) => void,
  userId?: string,
  analysisId?: string,
): Promise<void> {
  const res = await fetch(`${API_BASE}/stream/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      message,
      user_id: userId || "",
      analysis_id: analysisId || "",
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "대화 처리 중 오류가 발생했습니다.");
  }
  if (!res.body) throw new Error("스트리밍 응답을 받을 수 없습니다.");
  await processSSEStream(res, onDelta);
}

export interface DailyFortuneData {
  date: string;
  weekday: string;
  name: string;
  luck_index: number;
  fortune: string;
  love: string;
  work: string;
  health: string;
  lucky_color: string;
  lucky_number: number;
  lucky_item: string;
  warning: string;
}

export async function getDailyFortune(
  data: AnalyzeRequest & { user_id: string },
): Promise<DailyFortuneData> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 60_000);

  try {
    const res = await fetch(`${API_BASE}/daily-fortune`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
      signal: controller.signal,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "운세 생성 중 오류가 발생했습니다.");
    }
    return res.json();
  } catch (e) {
    if (e instanceof DOMException && e.name === "AbortError") {
      throw new Error("요청 시간이 초과되었습니다. 다시 시도해주세요.");
    }
    throw e;
  } finally {
    clearTimeout(timeout);
  }
}

// ─────── 세션 복원 API ───────

export async function restoreSession(
  analysisId: string,
  userId: string,
): Promise<{ session_id: string }> {
  const res = await fetch(`${API_BASE}/session/restore`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ analysis_id: analysisId, user_id: userId }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "세션 복원에 실패했습니다.");
  }
  return res.json();
}

// ─────── 히스토리 API ───────

export interface HistoryEntry {
  id: string;
  name: string;
  request: AnalyzeRequest;
  analysis: AnalysisData;
  messages: { role: string; content: string; createdAt?: string }[];
  createdAt: string;
}

export async function fetchHistory(userId: string): Promise<HistoryEntry[]> {
  try {
    const res = await fetch(`${API_BASE}/history/${userId}`);
    if (!res.ok) return [];
    const data = await res.json();
    return (data.history || []).map((h: HistoryEntry) => ({
      ...h,
      messages: h.messages || [],
    }));
  } catch {
    return [];
  }
}

export async function fetchHistoryDetail(analysisId: string): Promise<HistoryEntry | null> {
  try {
    const res = await fetch(`${API_BASE}/history/detail/${analysisId}`);
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export async function deleteHistoryEntry(analysisId: string, userId: string): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/history/${analysisId}`, {
      method: "DELETE",
      headers: { "X-User-Id": userId },
    });
    return res.ok;
  } catch {
    return false;
  }
}
