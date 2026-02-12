// 브라우저에서 직접 백엔드 호출 (Next.js rewrite proxy 타임아웃 문제 회피)
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

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
  analysis: AnalysisData;
  interpretation: string;
}

export interface ChatResponse {
  reply: string;
  session_id: string;
}

export async function analyzeSaju(data: AnalyzeRequest): Promise<AnalyzeResponse> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 180_000); // 3분 타임아웃

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

export async function chatWithAgent(
  sessionId: string,
  message: string
): Promise<ChatResponse> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 120_000); // 2분 타임아웃

  try {
    const res = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, message }),
      signal: controller.signal,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "대화 처리 중 오류가 발생했습니다.");
    }
    return res.json();
  } catch (e) {
    if (e instanceof DOMException && e.name === "AbortError") {
      throw new Error("응답 시간이 초과되었습니다. 다시 시도해주세요.");
    }
    throw e;
  } finally {
    clearTimeout(timeout);
  }
}
