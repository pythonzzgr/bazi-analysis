"""
사주팔자 AI 에이전트 - FastAPI 서버
"""

import os
import sys
import uuid
import json
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse, HTMLResponse
from pydantic import BaseModel, Field

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from saju.analyzer import full_analysis, analysis_to_text
from saju.calculator import get_leap_month_for_year
from agent.chat import SajuChatAgent
from rag.embedder import embed_documents, COLLECTION_NAME
from auth import (
    init_db, register_user, login_user, approve_user,
    get_user_role, set_user_role, list_users,
    update_profile, get_user_profile,
    save_analysis, get_user_analyses, get_analysis, delete_analysis,
    save_chat_message, get_chat_messages,
)

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
DATA_DIR = str(Path(__file__).parent.parent / "data")

agent = SajuChatAgent(qdrant_host=QDRANT_HOST, qdrant_port=QDRANT_PORT)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[Server] Starting up...")
    init_db()
    print("[Server] User DB initialized.")
    try:
        from qdrant_client import QdrantClient
        qc = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, timeout=5)
        collections = qc.get_collections().collections
        names = [c.name for c in collections]

        if COLLECTION_NAME not in names:
            print("[Server] Embedding methodology documents into Qdrant...")
            count = embed_documents(DATA_DIR, QDRANT_HOST, QDRANT_PORT)
            print(f"[Server] Embedded {count} chunks.")
        else:
            info = qc.get_collection(COLLECTION_NAME)
            print(f"[Server] Qdrant collection exists with {info.points_count} points.")
    except Exception as e:
        print(f"[Server] Qdrant initialization skipped: {e}")
        print("[Server] The server will work without RAG context.")

    yield
    print("[Server] Shutting down...")


app = FastAPI(
    title="사주팔자 AI 에이전트",
    description="사주팔자를 분석하고 AI가 해석해주는 에이전트 API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:3005",
        "http://localhost:3006",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3005",
        "https://sajugo.shop",
        "https://www.sajugo.shop",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────── Request/Response 모델 ───────

class AnalyzeRequest(BaseModel):
    name: str = Field(..., description="이름")
    year: int = Field(..., description="생년", ge=1900, le=2100)
    month: int = Field(..., description="생월", ge=1, le=12)
    day: int = Field(..., description="생일", ge=1, le=31)
    hour: int = Field(..., description="태어난 시각 (0-23)", ge=0, le=23)
    minute: int = Field(0, description="태어난 분 (0-59)", ge=0, le=59)
    gender: str = Field(..., description="성별 (남/여)")
    is_lunar: bool = Field(False, description="음력 입력 여부")
    is_leap_month: bool = Field(False, description="윤달 여부")
    user_id: str = Field("", description="로그인 사용자 ID (DB 저장용)")


class AnalyzeResponse(BaseModel):
    session_id: str
    analysis_id: str
    analysis: dict


class StreamRequest(BaseModel):
    session_id: str = Field(..., description="세션 ID")
    analysis_id: str = Field("", description="분석 ID (DB 저장용)")


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="세션 ID")
    message: str = Field(..., description="사용자 메시지")
    user_id: str = Field("", description="사용자 ID (권한 확인용)")
    analysis_id: str = Field("", description="분석 ID (DB 저장용)")


class RegisterRequest(BaseModel):
    username: str = Field(..., description="아이디")
    password: str = Field(..., description="비밀번호")
    displayName: str = Field(..., description="표시 이름")


class LoginRequest(BaseModel):
    username: str = Field(..., description="아이디")
    password: str = Field(..., description="비밀번호")


class SetRoleRequest(BaseModel):
    user_id: str = Field(..., description="대상 사용자 ID")
    role: str = Field(..., description="변경할 역할 (admin/user+/user)")


class DailyFortuneRequest(BaseModel):
    user_id: str = Field(..., description="사용자 ID")
    name: str = Field(..., description="이름")
    year: int = Field(..., ge=1900, le=2100)
    month: int = Field(..., ge=1, le=12)
    day: int = Field(..., ge=1, le=31)
    hour: int = Field(..., ge=0, le=23)
    minute: int = Field(0, ge=0, le=59)
    gender: str = Field(...)
    is_lunar: bool = Field(False)
    is_leap_month: bool = Field(False)


class ProfileUpdateRequest(BaseModel):
    user_id: str = Field(..., description="사용자 ID")
    gender: str | None = None
    birth_year: int | None = None
    birth_month: int | None = None
    birth_day: int | None = None
    birth_hour: int | None = None
    birth_minute: int | None = None
    is_lunar: bool | None = None
    is_leap_month: bool | None = None


def _check_premium(user_id: str):
    role = get_user_role(user_id)
    if role not in ("admin", "user+"):
        raise HTTPException(status_code=403, detail="프리미엄 기능은 후원자(user+) 이상만 이용 가능합니다.")
    return role


# ─────── 인증 API ───────

@app.post("/api/auth/register")
async def api_register(req: RegisterRequest):
    result = register_user(req.username, req.password, req.displayName)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/api/auth/login")
async def api_login(req: LoginRequest):
    result = login_user(req.username, req.password)
    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["error"])
    return result


@app.get("/api/auth/approve/{token}")
async def api_approve(token: str):
    success, user_info = approve_user(token)
    if success and user_info:
        html = f"""\
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0;background:#f1f5f9;">
  <div style="background:white;border-radius:20px;padding:48px;text-align:center;max-width:400px;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
    <div style="width:64px;height:64px;border-radius:50%;background:#10b981;display:flex;align-items:center;justify-content:center;margin:0 auto 20px;">
      <svg width="32" height="32" fill="none" viewBox="0 0 24 24"><path stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg>
    </div>
    <h2 style="color:#1e293b;margin:0 0 8px;">승인 완료</h2>
    <p style="color:#64748b;margin:0 0 4px;font-size:15px;"><b>{user_info['display_name']}</b>님의 가입이 승인되었습니다.</p>
    <p style="color:#94a3b8;font-size:13px;">아이디: {user_info['username']}</p>
  </div>
</body>
</html>"""
        return HTMLResponse(content=html)
    else:
        html = """\
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0;background:#f1f5f9;">
  <div style="background:white;border-radius:20px;padding:48px;text-align:center;max-width:400px;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
    <div style="width:64px;height:64px;border-radius:50%;background:#ef4444;display:flex;align-items:center;justify-content:center;margin:0 auto 20px;">
      <svg width="32" height="32" fill="none" viewBox="0 0 24 24"><path stroke="white" stroke-width="3" stroke-linecap="round" d="M6 18L18 6M6 6l12 12"/></svg>
    </div>
    <h2 style="color:#1e293b;margin:0 0 8px;">유효하지 않은 링크</h2>
    <p style="color:#64748b;font-size:15px;">이미 처리되었거나 잘못된 승인 링크입니다.</p>
  </div>
</body>
</html>"""
        return HTMLResponse(content=html, status_code=400)


# ─────── 프로필 API ───────

@app.put("/api/user/profile")
async def api_update_profile(req: ProfileUpdateRequest):
    data = req.model_dump(exclude={"user_id"}, exclude_none=True)
    if not update_profile(req.user_id, data):
        raise HTTPException(status_code=400, detail="업데이트할 항목이 없습니다.")
    profile = get_user_profile(req.user_id)
    return {"success": True, "user": profile}


@app.get("/api/user/profile/{user_id}")
async def api_get_profile(user_id: str):
    profile = get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return profile


# ─────── 관리자 API ───────

@app.post("/api/admin/set-role")
async def api_set_role(req: SetRoleRequest, request: Request):
    admin_key = request.headers.get("X-Admin-Key", "")
    expected_key = os.getenv("ADMIN_SECRET", "")
    if not expected_key or admin_key != expected_key:
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    if not set_user_role(req.user_id, req.role):
        raise HTTPException(status_code=400, detail="유효하지 않은 사용자 ID 또는 역할입니다.")
    return {"success": True, "message": f"역할이 {req.role}(으)로 변경되었습니다."}


@app.get("/api/admin/users")
async def api_list_users(request: Request):
    admin_key = request.headers.get("X-Admin-Key", "")
    expected_key = os.getenv("ADMIN_SECRET", "")
    if not expected_key or admin_key != expected_key:
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    return {"users": list_users()}


# ─────── 사주 분석 ───────

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "saju-agent"}


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    try:
        result = full_analysis(
            name=request.name,
            year=request.year,
            month=request.month,
            day=request.day,
            hour=request.hour,
            minute=request.minute,
            gender=request.gender,
            is_lunar=request.is_lunar,
            is_leap_month=request.is_leap_month,
        )

        text = analysis_to_text(result)
        session_id = str(uuid.uuid4())
        analysis_id = str(uuid.uuid4())
        agent.create_session(session_id, text, result)

        if request.user_id:
            req_data = {
                "name": request.name, "year": request.year, "month": request.month,
                "day": request.day, "hour": request.hour, "minute": request.minute,
                "gender": request.gender, "is_lunar": request.is_lunar, "is_leap_month": request.is_leap_month,
            }
            save_analysis(analysis_id, request.user_id, request.name, req_data, result)

        return AnalyzeResponse(session_id=session_id, analysis_id=analysis_id, analysis=result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분석 중 오류: {str(e)}")


def _sse_event(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.post("/api/stream/reading")
async def stream_reading(request: StreamRequest):
    if not agent.has_session(request.session_id):
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    analysis_id = request.analysis_id

    def generate():
        try:
            full_response = []
            for chunk in agent.get_initial_reading_stream(request.session_id):
                full_response.append(chunk)
                yield _sse_event({"delta": chunk})

            if analysis_id:
                save_chat_message(analysis_id, "assistant", "".join(full_response))

            yield "data: [DONE]\n\n"
        except Exception as e:
            yield _sse_event({"error": str(e)})

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/api/stream/chat")
async def stream_chat(request: ChatRequest):
    _check_premium(request.user_id)
    if not agent.has_session(request.session_id):
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    analysis_id = request.analysis_id

    def generate():
        try:
            if analysis_id:
                save_chat_message(analysis_id, "user", request.message)

            full_response = []
            for chunk in agent.chat_stream(request.session_id, request.message):
                full_response.append(chunk)
                yield _sse_event({"delta": chunk})

            if analysis_id:
                save_chat_message(analysis_id, "assistant", "".join(full_response))

            yield "data: [DONE]\n\n"
        except Exception as e:
            yield _sse_event({"error": str(e)})

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ─────── 히스토리 API ───────

@app.get("/api/history/{user_id}")
async def api_get_history(user_id: str):
    return {"history": get_user_analyses(user_id)}


@app.get("/api/history/detail/{analysis_id}")
async def api_get_history_detail(analysis_id: str):
    entry = get_analysis(analysis_id)
    if not entry:
        raise HTTPException(status_code=404, detail="분석 기록을 찾을 수 없습니다.")
    messages = get_chat_messages(analysis_id)
    entry["messages"] = messages
    return entry


@app.delete("/api/history/{analysis_id}")
async def api_delete_history(analysis_id: str, request: Request):
    user_id = request.headers.get("X-User-Id", "")
    if not user_id:
        raise HTTPException(status_code=400, detail="사용자 ID가 필요합니다.")
    if not delete_analysis(analysis_id, user_id):
        raise HTTPException(status_code=404, detail="삭제할 기록을 찾을 수 없거나 권한이 없습니다.")
    return {"success": True}


@app.get("/api/leap-month/{year}")
async def leap_month(year: int):
    leap = get_leap_month_for_year(year)
    return {"year": year, "leap_month": leap}


@app.post("/api/embed")
async def embed_docs():
    try:
        count = await asyncio.to_thread(
            embed_documents, DATA_DIR, QDRANT_HOST, QDRANT_PORT
        )
        return {"status": "ok", "embedded_chunks": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"임베딩 오류: {str(e)}")


# ─────── 오늘의 운세 (user+ / admin 전용) ───────

@app.post("/api/daily-fortune")
async def daily_fortune(request: DailyFortuneRequest):
    _check_premium(request.user_id)

    try:
        result = full_analysis(
            name=request.name,
            year=request.year,
            month=request.month,
            day=request.day,
            hour=request.hour,
            minute=request.minute,
            gender=request.gender,
            is_lunar=request.is_lunar,
            is_leap_month=request.is_leap_month,
        )
        text = analysis_to_text(result)
        fortune = agent.generate_daily_fortune(text, request.name, request.gender)
        return fortune
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"운세 생성 중 오류: {str(e)}")


# ─────── 공유 페이지 (서버 렌더링) ───────

import zlib
import base64

def _decode_share_data(encoded: str) -> dict | None:
    try:
        padded = encoded + "=" * (-len(encoded) % 4)
        raw = base64.urlsafe_b64decode(padded)
        decompressed = zlib.decompress(raw)
        return json.loads(decompressed)
    except Exception:
        return None


def _render_share_html(data: dict) -> str:
    share_type = data.get("type", "analysis")
    title = data.get("title", "사주 분석 결과")
    app_url = os.getenv("APP_URL", "https://sajugo.shop")

    css = """
    * { margin:0; padding:0; box-sizing:border-box; }
    body { font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; background:#f1f5f9; color:#1e293b; min-height:100vh; }
    .wrap { max-width:480px; margin:0 auto; padding:24px 16px 40px; }
    .card { background:white; border-radius:20px; padding:24px; margin-bottom:16px; box-shadow:0 1px 3px rgba(0,0,0,0.06); border:1px solid #e2e8f0; }
    .badge { display:inline-block; padding:4px 12px; border-radius:99px; font-size:11px; font-weight:700; }
    .pillars { display:grid; grid-template-columns:repeat(4,1fr); gap:8px; margin:16px 0; }
    .pillar { text-align:center; }
    .pillar-label { font-size:10px; color:#94a3b8; text-transform:uppercase; letter-spacing:0.1em; font-weight:600; margin-bottom:6px; }
    .pillar-cell { height:48px; display:flex; align-items:center; justify-content:center; font-size:20px; font-weight:700; border-radius:12px; background:#f8fafc; border:1px solid #e2e8f0; margin-bottom:4px; }
    .el-bar { display:flex; align-items:center; gap:12px; padding:8px 0; }
    .el-name { width:50px; font-size:13px; font-weight:600; }
    .el-track { flex:1; height:8px; background:#f1f5f9; border-radius:99px; overflow:hidden; }
    .el-fill { height:100%; border-radius:99px; }
    .el-pct { width:36px; text-align:right; font-size:12px; font-weight:700; }
    .el-wood { background:#10b981; } .el-fire { background:#ef4444; } .el-earth { background:#f59e0b; } .el-metal { background:#94a3b8; } .el-water { background:#3b82f6; }
    .msg { margin-bottom:12px; }
    .msg-bot { background:#f8fafc; border:1px solid #e2e8f0; border-radius:16px 16px 16px 4px; padding:14px; font-size:14px; line-height:1.8; color:#334155; }
    .msg-user { background:#137FEC; color:white; border-radius:16px 16px 4px 16px; padding:14px; font-size:14px; line-height:1.6; margin-left:auto; max-width:85%; }
    .luck-circle { width:80px; height:80px; position:relative; }
    .luck-num { position:absolute; inset:0; display:flex; align-items:center; justify-content:center; font-size:22px; font-weight:900; }
    .fortune-row { display:flex; gap:12px; align-items:flex-start; padding:12px 0; border-bottom:1px solid #f1f5f9; }
    .fortune-icon { width:32px; height:32px; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:16px; flex-shrink:0; }
    .fortune-text { font-size:14px; color:#475569; line-height:1.6; }
    .fortune-label { font-size:11px; font-weight:700; margin-bottom:2px; }
    .lucky-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; text-align:center; padding:12px 0; }
    .lucky-item { font-size:14px; font-weight:700; color:#1e293b; }
    .lucky-sub { font-size:10px; color:#94a3b8; margin-bottom:4px; }
    .cta { display:block; text-align:center; padding:14px; background:#137FEC; color:white; text-decoration:none; border-radius:14px; font-weight:700; font-size:15px; margin-top:8px; }
    .footer { text-align:center; padding:16px 0; font-size:12px; color:#94a3b8; }
    h2 { font-size:17px; margin-bottom:12px; }
    """

    body = ""

    if share_type == "analysis":
        p = data.get("pillars", {})
        el = data.get("elements", [])
        reading = data.get("reading", "")

        pillar_html = ""
        for label, key in [("시주","time"),("일주","day"),("월주","month"),("연주","year")]:
            pi = p.get(key, {})
            pillar_html += f"""<div class="pillar">
                <div class="pillar-label">{label}</div>
                <div class="pillar-cell">{pi.get('stem','')}</div>
                <div class="pillar-cell">{pi.get('branch','')}</div>
            </div>"""

        el_html = ""
        el_class_map = {"목":"el-wood","화":"el-fire","토":"el-earth","금":"el-metal","수":"el-water"}
        for e in el:
            cls = el_class_map.get(e.get("name",""), "el-wood")
            el_html += f"""<div class="el-bar">
                <span class="el-name">{e.get('name','')} ({e.get('hanja','')})</span>
                <div class="el-track"><div class="el-fill {cls}" style="width:{e.get('ratio',0)}%"></div></div>
                <span class="el-pct">{e.get('ratio',0)}%</span>
            </div>"""

        reading_html = reading.replace("\n\n", "</p><p style='margin-top:12px;'>").replace("\n", "<br>")

        body = f"""
        <div class="card">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:4px;">
                <span class="badge" style="background:#EFF6FF;color:#137FEC;">Day Master: {data.get('dayMaster','')}</span>
                <span style="font-size:12px;color:#94a3b8;">{data.get('strength','')}</span>
            </div>
            <h1 style="font-size:22px;font-weight:800;margin:8px 0 4px;">{title}</h1>
            <p style="font-size:13px;color:#64748b;">용신: {data.get('yongShin','')}</p>
            <div class="pillars">{pillar_html}</div>
        </div>
        <div class="card">
            <h2>오행 분포</h2>
            {el_html}
        </div>
        <div class="card">
            <h2>상세 해석</h2>
            <div style="font-size:14px;line-height:1.8;color:#334155;"><p>{reading_html}</p></div>
        </div>"""

    elif share_type == "fortune":
        f = data.get("fortune", {})
        luck = f.get("luck_index", 50)
        stroke_len = (luck / 100) * 213.6

        fortune_items = []
        if f.get("love"): fortune_items.append(("💕","#ec4899","연애/대인관계",f["love"]))
        if f.get("work"): fortune_items.append(("💼","#3b82f6","직업/학업",f["work"]))
        if f.get("health"): fortune_items.append(("🏃","#10b981","건강",f["health"]))
        if f.get("warning"): fortune_items.append(("⚠️","#ef4444","주의사항",f["warning"]))

        items_html = ""
        for icon, color, label, text in fortune_items:
            items_html += f"""<div class="fortune-row">
                <div class="fortune-icon" style="background:{color}15;">{icon}</div>
                <div><div class="fortune-label" style="color:{color};">{label}</div><div class="fortune-text">{text}</div></div>
            </div>"""

        lucky_html = ""
        if f.get("lucky_color"):
            lucky_html += f'<div><div class="lucky-sub">행운 색상</div><div class="lucky-item">{f["lucky_color"]}</div></div>'
        if f.get("lucky_number"):
            lucky_html += f'<div><div class="lucky-sub">행운 숫자</div><div class="lucky-item">{f["lucky_number"]}</div></div>'
        if f.get("lucky_item"):
            lucky_html += f'<div><div class="lucky-sub">행운 아이템</div><div class="lucky-item">{f["lucky_item"]}</div></div>'

        luck_color = "#10b981" if luck >= 80 else "#3b82f6" if luck >= 60 else "#f59e0b" if luck >= 40 else "#ef4444"

        body = f"""
        <div class="card">
            <p style="font-size:12px;color:#94a3b8;margin-bottom:4px;">{f.get('date','')} {f.get('weekday','')}요일</p>
            <h1 style="font-size:20px;font-weight:800;margin-bottom:16px;">{title}</h1>
            <div style="display:flex;align-items:center;gap:16px;margin-bottom:16px;">
                <div class="luck-circle">
                    <svg width="80" height="80" style="transform:rotate(-90deg);" viewBox="0 0 80 80">
                        <circle cx="40" cy="40" r="34" fill="none" stroke="#f1f5f9" stroke-width="8"/>
                        <circle cx="40" cy="40" r="34" fill="none" stroke="{luck_color}" stroke-width="8" stroke-linecap="round" stroke-dasharray="{stroke_len} 213.6"/>
                    </svg>
                    <div class="luck-num" style="color:{luck_color};">{luck}</div>
                </div>
                <div style="flex:1;font-size:14px;color:#475569;line-height:1.6;">{f.get('fortune','')}</div>
            </div>
            {items_html}
        </div>
        <div class="card">
            <div style="font-size:11px;color:#94a3b8;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:12px;">Today's Lucky</div>
            <div class="lucky-grid">{lucky_html}</div>
        </div>"""

    elif share_type == "chat":
        msgs = data.get("messages", [])
        msgs_html = ""
        for m in msgs:
            if m.get("role") == "user":
                msgs_html += f'<div class="msg"><div class="msg-user">{m.get("content","")}</div></div>'
            else:
                content = m.get("content","").replace("\n\n","</p><p style='margin-top:8px;'>").replace("\n","<br>")
                msgs_html += f'<div class="msg"><div class="msg-bot"><p>{content}</p></div></div>'

        body = f"""
        <div class="card">
            <h1 style="font-size:20px;font-weight:800;margin-bottom:4px;">{title}</h1>
            <p style="font-size:13px;color:#64748b;">{data.get('subtitle','사주 분석 대화')}</p>
        </div>
        <div class="card">
            <h2>대화 내역</h2>
            {msgs_html}
        </div>"""

    og_desc = data.get("ogDescription", "사주 분석 결과를 확인해보세요.")

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} - 사주고</title>
<meta property="og:title" content="{title} - 사주고">
<meta property="og:description" content="{og_desc}">
<meta property="og:type" content="website">
<style>{css}</style>
</head>
<body>
<div class="wrap">
{body}
<a href="{app_url}" class="cta">사주고에서 나도 사주보기</a>
<div class="footer">사주고 (sajugo.shop) - AI 사주 분석 서비스</div>
</div>
</body>
</html>"""


@app.get("/share")
async def share_page(d: str = ""):
    if not d:
        raise HTTPException(status_code=400, detail="공유 데이터가 없습니다.")
    data = _decode_share_data(d)
    if not data:
        raise HTTPException(status_code=400, detail="잘못된 공유 링크입니다.")
    html = _render_share_html(data)
    return HTMLResponse(content=html)


# ─────── 프론트엔드 정적 파일 서빙 ───────
STATIC_DIR = Path(__file__).parent / "static"


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    if not STATIC_DIR.exists():
        raise HTTPException(status_code=404, detail="Frontend not built. Run build.sh first.")

    file_path = (STATIC_DIR / full_path).resolve()
    if file_path.is_relative_to(STATIC_DIR.resolve()) and file_path.is_file():
        return FileResponse(file_path)

    index = STATIC_DIR / "index.html"
    if index.is_file():
        return FileResponse(index)

    raise HTTPException(status_code=404)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "5000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
