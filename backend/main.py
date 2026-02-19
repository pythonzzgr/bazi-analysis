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
