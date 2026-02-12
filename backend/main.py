"""
사주팔자 AI 에이전트 - FastAPI 서버
"""

import os
import uuid
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# .env 로드
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from .saju.analyzer import full_analysis, analysis_to_text
from .saju.calculator import get_leap_month_for_year
from .agent.chat import SajuChatAgent
from .rag.embedder import embed_documents, COLLECTION_NAME

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
        qc = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
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
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:3005", "http://localhost:3006", "http://127.0.0.1:5173", "http://127.0.0.1:3000", "http://127.0.0.1:3005"],
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
    interpretation: str


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="세션 ID")
    message: str = Field(..., description="사용자 메시지")


class ChatResponse(BaseModel):
    reply: str
    session_id: str


# ─────── API 엔드포인트 ───────

@app.get("/api/health")
async def health_check():
    """헬스체크"""
    return {"status": "ok", "service": "saju-agent"}


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    """
    사주 분석을 수행하고 AI 해석을 반환합니다.

    1. Python 엔진으로 사주 계산
    2. 결과를 AI 에이전트에 전달
    3. AI가 종합 해석 생성
    """
    try:
        # 사주 계산
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

        # 분석 결과를 텍스트로 변환
        text = analysis_to_text(result)

        # 세션 생성
        session_id = str(uuid.uuid4())
        agent.create_session(session_id, text, result)

        # AI 해석 생성
        interpretation = await asyncio.to_thread(
            agent.get_initial_reading, session_id
        )

        return AnalyzeResponse(
            session_id=session_id,
            analysis=result,
            interpretation=interpretation,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분석 중 오류: {str(e)}")


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """후속 대화를 처리합니다."""
    if not agent.has_session(request.session_id):
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    try:
        reply = await asyncio.to_thread(
            agent.chat, request.session_id, request.message
        )
        return ChatResponse(reply=reply, session_id=request.session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"대화 처리 중 오류: {str(e)}")


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
