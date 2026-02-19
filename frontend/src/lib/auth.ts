/**
 * 로컬 JSON 기반 인증 시스템
 * localStorage에 계정 정보와 세션을 저장합니다.
 */

export interface User {
  id: string;
  username: string;
  displayName: string;
  passwordHash: string;
  createdAt: string;
}

export interface SessionUser {
  id: string;
  username: string;
  displayName: string;
}

const USERS_KEY = "saju-users";
const SESSION_KEY = "saju-session";

// 간단한 해시 (로컬 전용이므로 보안용이 아닌 난독화 용도)
function simpleHash(str: string): string {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash + char) | 0;
  }
  // 추가 라운드로 해시 강화
  const salt = "saju-destiny-compass";
  for (let i = 0; i < salt.length; i++) {
    const char = salt.charCodeAt(i);
    hash = ((hash << 5) - hash + char) | 0;
  }
  return Math.abs(hash).toString(36) + str.length.toString(36);
}

function getUsers(): User[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(USERS_KEY);
    if (!raw) return [];
    return JSON.parse(raw) as User[];
  } catch {
    return [];
  }
}

function saveUsers(users: User[]): void {
  localStorage.setItem(USERS_KEY, JSON.stringify(users));
}

export function register(
  username: string,
  password: string,
  displayName: string
): { success: boolean; error?: string; user?: SessionUser } {
  const users = getUsers();

  // 유효성 검사
  if (!username.trim() || username.length < 2) {
    return { success: false, error: "아이디는 2자 이상이어야 합니다." };
  }
  if (!password || password.length < 4) {
    return { success: false, error: "비밀번호는 4자 이상이어야 합니다." };
  }
  if (!displayName.trim()) {
    return { success: false, error: "이름을 입력해주세요." };
  }

  // 중복 확인
  if (users.find((u) => u.username === username.trim())) {
    return { success: false, error: "이미 사용 중인 아이디입니다." };
  }

  const newUser: User = {
    id: crypto.randomUUID(),
    username: username.trim(),
    displayName: displayName.trim(),
    passwordHash: simpleHash(password),
    createdAt: new Date().toISOString(),
  };

  users.push(newUser);
  saveUsers(users);

  // 자동 로그인
  const sessionUser: SessionUser = {
    id: newUser.id,
    username: newUser.username,
    displayName: newUser.displayName,
  };
  localStorage.setItem(SESSION_KEY, JSON.stringify(sessionUser));

  return { success: true, user: sessionUser };
}

export function login(
  username: string,
  password: string
): { success: boolean; error?: string; user?: SessionUser } {
  const users = getUsers();

  const user = users.find((u) => u.username === username.trim());
  if (!user) {
    return { success: false, error: "존재하지 않는 아이디입니다." };
  }

  if (user.passwordHash !== simpleHash(password)) {
    return { success: false, error: "비밀번호가 일치하지 않습니다." };
  }

  const sessionUser: SessionUser = {
    id: user.id,
    username: user.username,
    displayName: user.displayName,
  };
  localStorage.setItem(SESSION_KEY, JSON.stringify(sessionUser));

  return { success: true, user: sessionUser };
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
