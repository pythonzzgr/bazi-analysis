/**
 * 백엔드 API 기반 인증 시스템
 * 회원가입 → 관리자 이메일 승인 → 로그인 가능
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000/api";

export interface SessionUser {
  id: string;
  username: string;
  displayName: string;
}

const SESSION_KEY = "saju-session";

export async function register(
  username: string,
  password: string,
  displayName: string
): Promise<{ success: boolean; error?: string; pendingApproval?: boolean }> {
  try {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password, displayName }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      return { success: false, error: err.detail || "회원가입에 실패했습니다." };
    }

    return { success: true, pendingApproval: true };
  } catch {
    return { success: false, error: "서버에 연결할 수 없습니다." };
  }
}

export async function login(
  username: string,
  password: string
): Promise<{ success: boolean; error?: string; user?: SessionUser }> {
  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      return { success: false, error: err.detail || "로그인에 실패했습니다." };
    }

    const data = await res.json();
    const sessionUser: SessionUser = data.user;
    localStorage.setItem(SESSION_KEY, JSON.stringify(sessionUser));
    return { success: true, user: sessionUser };
  } catch {
    return { success: false, error: "서버에 연결할 수 없습니다." };
  }
}

export function logout(): void {
  localStorage.removeItem(SESSION_KEY);
}

export function getCurrentUser(): SessionUser | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(SESSION_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as SessionUser;
  } catch {
    return null;
  }
}
