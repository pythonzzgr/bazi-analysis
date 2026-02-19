"""
이메일 승인 기반 회원가입 + 역할 관리 + 분석/채팅 히스토리 DB
- DATABASE_URL이 있으면 PostgreSQL, 없으면 SQLite 폴백
- bcrypt로 비밀번호 해싱
- 역할: admin / user+ / user
"""

import os
import json as _json
import sqlite3
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager

import bcrypt

DATABASE_URL = os.getenv("DATABASE_URL", "")
VALID_ROLES = {"admin", "user+", "user"}

_use_pg = bool(DATABASE_URL and DATABASE_URL.startswith("postgres"))

if _use_pg:
    import psycopg2
    import psycopg2.extras


@contextmanager
def _conn():
    if _use_pg:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    else:
        db_path = Path(__file__).parent / "users.db"
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()


def _fetchone(conn, query: str, params: tuple) -> dict | None:
    if _use_pg:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(query, params)
        row = cur.fetchone()
        cur.close()
        return dict(row) if row else None
    else:
        cur = conn.execute(query, params)
        row = cur.fetchone()
        return dict(row) if row else None


def _fetchall(conn, query: str, params: tuple = ()) -> list[dict]:
    if _use_pg:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(query, params)
        rows = cur.fetchall()
        cur.close()
        return [dict(r) for r in rows]
    else:
        cur = conn.execute(query, params)
        return [dict(r) for r in cur.fetchall()]


def _execute(conn, query: str, params: tuple = ()):
    if _use_pg:
        cur = conn.cursor()
        cur.execute(query, params)
        cur.close()
    else:
        conn.execute(query, params)


def _q(sql: str) -> str:
    """SQLite의 ?를 PostgreSQL의 %s로 변환."""
    if _use_pg:
        return sql.replace("?", "%s")
    return sql


# ─────── 테이블 초기화 ───────

def init_db():
    with _conn() as conn:
        _execute(conn, """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                gender TEXT,
                birth_year INTEGER,
                birth_month INTEGER,
                birth_day INTEGER,
                birth_hour INTEGER,
                birth_minute INTEGER,
                is_lunar BOOLEAN DEFAULT FALSE,
                is_leap_month BOOLEAN DEFAULT FALSE,
                role TEXT NOT NULL DEFAULT 'user',
                status TEXT NOT NULL DEFAULT 'pending',
                approval_token TEXT,
                subscription_expires_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        _execute(conn, """
            CREATE TABLE IF NOT EXISTS analyses (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                request_data TEXT NOT NULL,
                analysis_data TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        _execute(conn, """
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """) if not _use_pg else _execute(conn, """
            CREATE TABLE IF NOT EXISTS chat_messages (
                id BIGSERIAL PRIMARY KEY,
                analysis_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        # 기존 users 테이블 마이그레이션 (컬럼 없으면 추가)
        if _use_pg:
            for col, default in [
                ("gender", "NULL"),
                ("birth_year", "NULL"),
                ("birth_month", "NULL"),
                ("birth_day", "NULL"),
                ("birth_hour", "NULL"),
                ("birth_minute", "NULL"),
                ("is_lunar", "FALSE"),
                ("is_leap_month", "FALSE"),
                ("subscription_expires_at", "NULL"),
                ("updated_at", "NULL"),
            ]:
                try:
                    typ = "BOOLEAN" if col.startswith("is_l") else "TEXT" if col in ("gender", "subscription_expires_at", "updated_at") else "INTEGER"
                    _execute(conn, f"ALTER TABLE users ADD COLUMN {col} {typ} DEFAULT {default}")
                except Exception:
                    pass
        else:
            existing = {r["name"] for r in _fetchall(conn, "PRAGMA table_info(users)")}
            migrations = [
                ("gender", "TEXT"), ("birth_year", "INTEGER"), ("birth_month", "INTEGER"),
                ("birth_day", "INTEGER"), ("birth_hour", "INTEGER"), ("birth_minute", "INTEGER"),
                ("is_lunar", "BOOLEAN DEFAULT 0"), ("is_leap_month", "BOOLEAN DEFAULT 0"),
                ("subscription_expires_at", "TEXT"), ("updated_at", "TEXT"),
            ]
            for col, typ in migrations:
                if col not in existing:
                    _execute(conn, f"ALTER TABLE users ADD COLUMN {col} {typ}")

    db_type = "PostgreSQL" if _use_pg else "SQLite"
    print(f"[Auth] {db_type} 초기화 완료 (users, analyses, chat_messages)")


# ─────── 사용자 인증 ───────

def register_user(username: str, password: str, display_name: str) -> dict:
    if not username.strip() or len(username.strip()) < 2:
        return {"success": False, "error": "아이디는 2자 이상이어야 합니다."}
    if not password or len(password) < 4:
        return {"success": False, "error": "비밀번호는 4자 이상이어야 합니다."}
    if not display_name.strip():
        return {"success": False, "error": "이름을 입력해주세요."}

    username = username.strip()
    display_name = display_name.strip()
    now = datetime.now().isoformat()

    with _conn() as conn:
        existing = _fetchone(conn, _q("SELECT id FROM users WHERE username = ?"), (username,))
        if existing:
            return {"success": False, "error": "이미 사용 중인 아이디입니다."}

        user_id = secrets.token_urlsafe(16)
        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        approval_token = secrets.token_urlsafe(32)

        _execute(
            conn,
            _q("INSERT INTO users (id, username, display_name, password_hash, role, status, approval_token, created_at, updated_at) "
               "VALUES (?, ?, ?, ?, 'user', 'pending', ?, ?, ?)"),
            (user_id, username, display_name, pw_hash, approval_token, now, now),
        )

    _send_approval_email(username, display_name, approval_token)
    return {"success": True, "message": "가입 신청이 완료되었습니다. 관리자 승인 후 로그인이 가능합니다."}


def login_user(username: str, password: str) -> dict:
    with _conn() as conn:
        row = _fetchone(
            conn,
            _q("SELECT id, username, display_name, password_hash, role, status, "
               "gender, birth_year, birth_month, birth_day, birth_hour, birth_minute, "
               "is_lunar, is_leap_month, subscription_expires_at FROM users WHERE username = ?"),
            (username.strip(),),
        )

    if not row:
        return {"success": False, "error": "존재하지 않는 아이디입니다."}

    if not bcrypt.checkpw(password.encode(), row["password_hash"].encode()):
        return {"success": False, "error": "비밀번호가 일치하지 않습니다."}

    if row["status"] == "pending":
        return {"success": False, "error": "관리자의 승인을 기다리고 있습니다. 승인 후 로그인이 가능합니다."}

    if row["status"] == "rejected":
        return {"success": False, "error": "가입이 거절되었습니다."}

    role = row["role"]
    # user+ 구독 만료 체크
    if role == "user+" and row["subscription_expires_at"]:
        try:
            expires = datetime.fromisoformat(row["subscription_expires_at"])
            if expires < datetime.now():
                role = "user"
                with _conn() as conn:
                    _execute(conn, _q("UPDATE users SET role = 'user' WHERE id = ?"), (row["id"],))
        except (ValueError, TypeError):
            pass

    return {
        "success": True,
        "user": {
            "id": row["id"],
            "username": row["username"],
            "displayName": row["display_name"],
            "role": role,
            "gender": row["gender"],
            "birthYear": row["birth_year"],
            "birthMonth": row["birth_month"],
            "birthDay": row["birth_day"],
            "birthHour": row["birth_hour"],
            "birthMinute": row["birth_minute"],
            "isLunar": bool(row["is_lunar"]),
            "isLeapMonth": bool(row["is_leap_month"]),
        },
    }


def approve_user(token: str) -> tuple[bool, dict | None]:
    with _conn() as conn:
        row = _fetchone(
            conn,
            _q("SELECT id, username, display_name FROM users WHERE approval_token = ? AND status = 'pending'"),
            (token,),
        )
        if not row:
            return False, None

        _execute(
            conn,
            _q("UPDATE users SET status = 'approved', approval_token = NULL WHERE approval_token = ?"),
            (token,),
        )

    return True, {"username": row["username"], "display_name": row["display_name"]}


# ─────── 프로필 관리 ───────

def update_profile(user_id: str, data: dict) -> bool:
    allowed = {"gender", "birth_year", "birth_month", "birth_day", "birth_hour", "birth_minute", "is_lunar", "is_leap_month"}
    updates = {k: v for k, v in data.items() if k in allowed and v is not None}
    if not updates:
        return False

    now = datetime.now().isoformat()
    set_clauses = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [now, user_id]

    with _conn() as conn:
        _execute(conn, _q(f"UPDATE users SET {set_clauses}, updated_at = ? WHERE id = ?"), tuple(values))
    return True


def get_user_profile(user_id: str) -> dict | None:
    with _conn() as conn:
        row = _fetchone(
            conn,
            _q("SELECT id, username, display_name, role, gender, birth_year, birth_month, birth_day, "
               "birth_hour, birth_minute, is_lunar, is_leap_month, subscription_expires_at FROM users WHERE id = ?"),
            (user_id,),
        )
    if not row:
        return None
    return {
        "id": row["id"],
        "username": row["username"],
        "displayName": row["display_name"],
        "role": row["role"],
        "gender": row["gender"],
        "birthYear": row["birth_year"],
        "birthMonth": row["birth_month"],
        "birthDay": row["birth_day"],
        "birthHour": row["birth_hour"],
        "birthMinute": row["birth_minute"],
        "isLunar": bool(row["is_lunar"]) if row["is_lunar"] is not None else False,
        "isLeapMonth": bool(row["is_leap_month"]) if row["is_leap_month"] is not None else False,
        "subscriptionExpiresAt": row["subscription_expires_at"],
    }


# ─────── 역할 관리 ───────

def get_user_role(user_id: str) -> str | None:
    with _conn() as conn:
        row = _fetchone(conn, _q("SELECT role FROM users WHERE id = ?"), (user_id,))
    return row["role"] if row else None


def set_user_role(user_id: str, role: str) -> bool:
    if role not in VALID_ROLES:
        return False
    with _conn() as conn:
        _execute(conn, _q("UPDATE users SET role = ?, updated_at = ? WHERE id = ?"),
                 (role, datetime.now().isoformat(), user_id))
    return True


def list_users() -> list[dict]:
    with _conn() as conn:
        rows = _fetchall(
            conn,
            "SELECT id, username, display_name, role, status, created_at FROM users ORDER BY created_at DESC",
        )
    return [
        {
            "id": r["id"],
            "username": r["username"],
            "displayName": r["display_name"],
            "role": r["role"],
            "status": r["status"],
            "createdAt": r["created_at"],
        }
        for r in rows
    ]


# ─────── 분석 히스토리 ───────

def save_analysis(analysis_id: str, user_id: str, name: str, request_data: dict, analysis_data: dict) -> None:
    now = datetime.now().isoformat()
    with _conn() as conn:
        _execute(
            conn,
            _q("INSERT INTO analyses (id, user_id, name, request_data, analysis_data, created_at) "
               "VALUES (?, ?, ?, ?, ?, ?)"),
            (analysis_id, user_id, name, _json.dumps(request_data, ensure_ascii=False),
             _json.dumps(analysis_data, ensure_ascii=False), now),
        )


def get_user_analyses(user_id: str, limit: int = 50) -> list[dict]:
    with _conn() as conn:
        rows = _fetchall(
            conn,
            _q("SELECT id, name, request_data, analysis_data, created_at FROM analyses "
               "WHERE user_id = ? ORDER BY created_at DESC LIMIT ?"),
            (user_id, limit),
        )
    result = []
    for r in rows:
        req = _json.loads(r["request_data"]) if isinstance(r["request_data"], str) else r["request_data"]
        ana = _json.loads(r["analysis_data"]) if isinstance(r["analysis_data"], str) else r["analysis_data"]
        result.append({
            "id": r["id"],
            "name": r["name"],
            "request": req,
            "analysis": ana,
            "createdAt": r["created_at"],
        })
    return result


def get_analysis(analysis_id: str) -> dict | None:
    with _conn() as conn:
        r = _fetchone(conn, _q("SELECT id, user_id, name, request_data, analysis_data, created_at FROM analyses WHERE id = ?"), (analysis_id,))
    if not r:
        return None
    req = _json.loads(r["request_data"]) if isinstance(r["request_data"], str) else r["request_data"]
    ana = _json.loads(r["analysis_data"]) if isinstance(r["analysis_data"], str) else r["analysis_data"]
    return {
        "id": r["id"],
        "userId": r["user_id"],
        "name": r["name"],
        "request": req,
        "analysis": ana,
        "createdAt": r["created_at"],
    }


def delete_analysis(analysis_id: str, user_id: str) -> bool:
    with _conn() as conn:
        row = _fetchone(conn, _q("SELECT id FROM analyses WHERE id = ? AND user_id = ?"), (analysis_id, user_id))
        if not row:
            return False
        _execute(conn, _q("DELETE FROM chat_messages WHERE analysis_id = ?"), (analysis_id,))
        _execute(conn, _q("DELETE FROM analyses WHERE id = ?"), (analysis_id,))
    return True


# ─────── 채팅 메시지 ───────

def save_chat_message(analysis_id: str, role: str, content: str) -> None:
    now = datetime.now().isoformat()
    with _conn() as conn:
        _execute(
            conn,
            _q("INSERT INTO chat_messages (analysis_id, role, content, created_at) VALUES (?, ?, ?, ?)"),
            (analysis_id, role, content, now),
        )


def get_chat_messages(analysis_id: str) -> list[dict]:
    with _conn() as conn:
        rows = _fetchall(
            conn,
            _q("SELECT role, content, created_at FROM chat_messages WHERE analysis_id = ? ORDER BY created_at ASC"),
            (analysis_id,),
        )
    return [{"role": r["role"], "content": r["content"], "createdAt": r["created_at"]} for r in rows]


# ─────── 이메일 ───────

def _send_approval_email(username: str, display_name: str, token: str):
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    admin_email = os.getenv("ADMIN_EMAIL")
    app_url = os.getenv("APP_URL", "http://localhost:5000")

    if not all([smtp_host, smtp_user, smtp_pass, admin_email]):
        print(f"[Auth] SMTP 미설정. 승인 토큰({username}): {token}")
        print(f"[Auth] 수동 승인 URL: {app_url}/api/auth/approve/{token}")
        return

    approve_link = f"{app_url}/api/auth/approve/{token}"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[사주 분석] 새 회원가입 승인 요청 - {display_name}"
    msg["From"] = smtp_user
    msg["To"] = admin_email

    html = f"""\
<html>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 480px; margin: 0 auto; padding: 24px;">
  <div style="background: #f8fafc; border-radius: 16px; padding: 32px; border: 1px solid #e2e8f0;">
    <h2 style="color: #1e293b; margin: 0 0 24px 0; font-size: 20px;">새 회원가입 승인 요청</h2>
    <table style="width: 100%; border-collapse: collapse; margin-bottom: 24px;">
      <tr><td style="padding:8px 0;color:#64748b;font-size:14px;">이름</td><td style="padding:8px 0;color:#1e293b;font-size:14px;font-weight:600;">{display_name}</td></tr>
      <tr><td style="padding:8px 0;color:#64748b;font-size:14px;">아이디</td><td style="padding:8px 0;color:#1e293b;font-size:14px;font-weight:600;">{username}</td></tr>
      <tr><td style="padding:8px 0;color:#64748b;font-size:14px;">신청 시각</td><td style="padding:8px 0;color:#1e293b;font-size:14px;">{now}</td></tr>
    </table>
    <a href="{approve_link}" style="display:inline-block;padding:14px 32px;background:#137FEC;color:white;text-decoration:none;border-radius:10px;font-weight:700;font-size:15px;">승인하기</a>
    <p style="color:#94a3b8;font-size:12px;margin-top:24px;">이 링크를 클릭하면 해당 사용자의 가입이 승인됩니다.</p>
  </div>
</body>
</html>"""

    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        print(f"[Auth] 승인 요청 이메일 발송 완료: {username}")
    except Exception as e:
        print(f"[Auth] 이메일 발송 실패: {e}")
        print(f"[Auth] 수동 승인 URL: {app_url}/api/auth/approve/{token}")
