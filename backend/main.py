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

# backend/ 디렉토리를 sys.path에 추가 (직접 실행 시 import 해결)
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel, Field

# .env 로드
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from saju.analyzer import full_analysis, analysis_to_text
from saju.calculator import get_leap_month_for_year
from agent.chat import SajuChatAgent
from rag.embedder import embed_documents, COLLECTION_NAME

# ─────── 설정 ───────
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
DATA_DIR = str(Path(__file__).parent.parent / "data")

# ─────── 전역 에이전트 ───────
agent = SajuChatAgent(qdrant_host=QDRANT_HOST, qdrant_port=QDRANT_PORT)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """서버 시작 시 Qdrant 임베딩 초기화"""
    print("[Server] Starting up...")
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

# CORS 설정
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
    is_leap_month: bool = Field(False, description="윤달(閏月) 여부")


class AnalyzeResponse(BaseModel):
    session_id: str
    analysis: dict


class StreamRequest(BaseModel):
    session_id: str = Field(..., description="세션 ID")


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="세션 ID")
    message: str = Field(..., description="사용자 메시지")


# ─────── API 엔드포인트 ───────

@app.get("/api/health")
async def health_check():
    """헬스체크"""
    return {"status": "ok", "service": "saju-agent"}


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    """사주 분석을 수행하고 세션을 생성합니다. AI 해석은 /api/stream/reading으로 별도 스트리밍합니다."""
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
        agent.create_session(session_id, text, result)

        return AnalyzeResponse(session_id=session_id, analysis=result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분석 중 오류: {str(e)}")


def _sse_event(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.post("/api/stream/reading")
async def stream_reading(request: StreamRequest):
    """첫 사주 해석을 SSE 스트리밍으로 반환합니다."""
    if not agent.has_session(request.session_id):
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    def generate():
        try:
            for chunk in agent.get_initial_reading_stream(request.session_id):
                yield _sse_event({"delta": chunk})
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
    """후속 대화를 SSE 스트리밍으로 반환합니다."""
    if not agent.has_session(request.session_id):
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    def generate():
        try:
            for chunk in agent.chat_stream(request.session_id, request.message):
                yield _sse_event({"delta": chunk})
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield _sse_event({"error": str(e)})

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/leap-month/{year}")
async def leap_month(year: int):
    """해당 음력 연도의 윤달 정보를 반환합니다."""
    leap = get_leap_month_for_year(year)
    return {"year": year, "leap_month": leap}


@app.post("/api/embed")
async def embed_docs():
    """수동으로 문서 임베딩을 트리거합니다."""
    try:
        count = await asyncio.to_thread(
            embed_documents, DATA_DIR, QDRANT_HOST, QDRANT_PORT
        )
        return {"status": "ok", "embedded_chunks": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"임베딩 오류: {str(e)}")


# ─────── 프론트엔드 정적 파일 서빙 (프로덕션) ───────
STATIC_DIR = Path(__file__).parent / "static"


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """Next.js 정적 빌드 파일을 서빙합니다. API 라우트보다 뒤에 정의되어 우선순위가 낮습니다."""
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
