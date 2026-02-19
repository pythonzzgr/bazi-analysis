"""
이메일 승인 기반 회원가입 시스템
- SQLite로 사용자 관리
- bcrypt로 비밀번호 해싱
- 관리자 이메일 승인 후 로그인 가능
"""

import os
import sqlite3
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from datetime import datetime

import bcrypt

DB_PATH = Path(__file__).parent / "users.db"


def _conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            display_name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            approval_token TEXT,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def register_user(username: str, password: str, display_name: str) -> dict:
    if not username.strip() or len(username.strip()) < 2:
        return {"success": False, "error": "아이디는 2자 이상이어야 합니다."}
    if not password or len(password) < 4:
        return {"success": False, "error": "비밀번호는 4자 이상이어야 합니다."}
    if not display_name.strip():
        return {"success": False, "error": "이름을 입력해주세요."}

    username = username.strip()
    display_name = display_name.strip()

    conn = _conn()
    existing = conn.execute(
        "SELECT id FROM users WHERE username = ?", (username,)
    ).fetchone()
    if existing:
        conn.close()
        return {"success": False, "error": "이미 사용 중인 아이디입니다."}

    user_id = secrets.token_urlsafe(16)
    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    approval_token = secrets.token_urlsafe(32)
    created_at = datetime.now().isoformat()

    conn.execute(
        "INSERT INTO users (id, username, display_name, password_hash, status, approval_token, created_at) "
        "VALUES (?, ?, ?, ?, 'pending', ?, ?)",
        (user_id, username, display_name, pw_hash, approval_token, created_at),
    )
    conn.commit()
    conn.close()

    _send_approval_email(username, display_name, approval_token)

    return {"success": True, "message": "가입 신청이 완료되었습니다. 관리자 승인 후 로그인이 가능합니다."}


def login_user(username: str, password: str) -> dict:
    conn = _conn()
    row = conn.execute(
        "SELECT id, username, display_name, password_hash, status FROM users WHERE username = ?",
        (username.strip(),),
    ).fetchone()
    conn.close()

    if not row:
        return {"success": False, "error": "존재하지 않는 아이디입니다."}

    if not bcrypt.checkpw(password.encode(), row["password_hash"].encode()):
        return {"success": False, "error": "비밀번호가 일치하지 않습니다."}

    if row["status"] == "pending":
        return {"success": False, "error": "관리자의 승인을 기다리고 있습니다. 승인 후 로그인이 가능합니다."}

    if row["status"] == "rejected":
        return {"success": False, "error": "가입이 거절되었습니다."}

    return {
        "success": True,
        "user": {
            "id": row["id"],
            "username": row["username"],
            "displayName": row["display_name"],
        },
    }


def approve_user(token: str) -> tuple[bool, dict | None]:
    conn = _conn()
    row = conn.execute(
        "SELECT id, username, display_name FROM users WHERE approval_token = ? AND status = 'pending'",
        (token,),
    ).fetchone()

    if not row:
        conn.close()
        return False, None

    conn.execute(
        "UPDATE users SET status = 'approved', approval_token = NULL WHERE approval_token = ?",
        (token,),
    )
    conn.commit()
    conn.close()
    return True, {"username": row["username"], "display_name": row["display_name"]}


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
      <tr>
        <td style="padding: 8px 0; color: #64748b; font-size: 14px;">이름</td>
        <td style="padding: 8px 0; color: #1e293b; font-size: 14px; font-weight: 600;">{display_name}</td>
      </tr>
      <tr>
        <td style="padding: 8px 0; color: #64748b; font-size: 14px;">아이디</td>
        <td style="padding: 8px 0; color: #1e293b; font-size: 14px; font-weight: 600;">{username}</td>
      </tr>
      <tr>
        <td style="padding: 8px 0; color: #64748b; font-size: 14px;">신청 시각</td>
        <td style="padding: 8px 0; color: #1e293b; font-size: 14px;">{now}</td>
      </tr>
    </table>
    <a href="{approve_link}"
       style="display: inline-block; padding: 14px 32px; background: #137FEC; color: white;
              text-decoration: none; border-radius: 10px; font-weight: 700; font-size: 15px;">
      승인하기
    </a>
    <p style="color: #94a3b8; font-size: 12px; margin-top: 24px;">
      이 링크를 클릭하면 해당 사용자의 가입이 승인됩니다.
    </p>
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
