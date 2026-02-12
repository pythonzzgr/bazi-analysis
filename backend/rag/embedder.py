"""
RAG Embedder: data/ 폴더의 마크다운 문서를 청킹하여 Qdrant에 임베딩 저장
"""

import os
import re
import hashlib
from pathlib import Path

from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue,
)


COLLECTION_NAME = "saju_methodology"
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536


def get_clients(qdrant_host: str = "localhost", qdrant_port: int = 6333):
    """OpenAI 및 Qdrant 클라이언트 생성"""
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port)
    return openai_client, qdrant_client


def chunk_markdown(text: str, filename: str) -> list[dict]:
    """
    마크다운 문서를 섹션 단위로 청킹합니다.

    전략:
    - ### 제목 기준으로 섹션 분리
    - 각 섹션에 파일명과 상위 제목을 메타데이터로 포함
    - 너무 짧은 청크는 이전 청크에 병합
    """
    chunks = []
    lines = text.split("\n")

    current_h1 = filename
    current_section_title = ""
    current_content = []

    for line in lines:
        # H1 제목
        if line.startswith("# "):
            current_h1 = line.strip("# ").strip()
            continue

        # H3 제목 (섹션 구분)
        if line.startswith("### ") or line.startswith("## "):
            # 이전 섹션 저장
            if current_content:
                content_text = "\n".join(current_content).strip()
                if len(content_text) > 50:  # 최소 50자 이상만 저장
                    chunks.append({
                        "filename": filename,
                        "phase": current_h1,
                        "section": current_section_title,
                        "content": content_text,
                    })
                current_content = []

            current_section_title = line.strip("#").strip()
            current_content.append(line)
        else:
            current_content.append(line)

    # 마지막 섹션
    if current_content:
        content_text = "\n".join(current_content).strip()
        if len(content_text) > 50:
            chunks.append({
                "filename": filename,
                "phase": current_h1,
                "section": current_section_title,
                "content": content_text,
            })

    # 청크가 너무 적으면 전체를 하나의 청크로
    if not chunks and len(text.strip()) > 50:
        chunks.append({
            "filename": filename,
            "phase": current_h1,
            "section": "전체",
            "content": text.strip(),
        })

    return chunks


def embed_text(client: OpenAI, text: str) -> list[float]:
    """텍스트를 임베딩 벡터로 변환"""
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
    )
    return response.data[0].embedding


def create_collection(qdrant: QdrantClient):
    """Qdrant 컬렉션 생성 (없으면)"""
    collections = qdrant.get_collections().collections
    names = [c.name for c in collections]

    if COLLECTION_NAME not in names:
        qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=EMBEDDING_DIM,
                distance=Distance.COSINE,
            ),
        )
        print(f"[Qdrant] Collection '{COLLECTION_NAME}' created.")
    else:
        print(f"[Qdrant] Collection '{COLLECTION_NAME}' already exists.")


def embed_documents(data_dir: str, qdrant_host: str = "localhost", qdrant_port: int = 6333):
    """
    data/ 폴더의 모든 .md 파일을 임베딩하여 Qdrant에 저장합니다.

    Args:
        data_dir: 데이터 디렉토리 경로
        qdrant_host: Qdrant 호스트
        qdrant_port: Qdrant 포트
    """
    openai_client, qdrant_client = get_clients(qdrant_host, qdrant_port)
    create_collection(qdrant_client)

    data_path = Path(data_dir)
    md_files = sorted(data_path.glob("*.md"))

    if not md_files:
        print(f"[Embedder] No .md files found in {data_dir}")
        return

    all_points = []
    point_id = 0

    for md_file in md_files:
        print(f"[Embedder] Processing: {md_file.name}")
        text = md_file.read_text(encoding="utf-8")
        chunks = chunk_markdown(text, md_file.name)

        for chunk in chunks:
            # 임베딩할 텍스트 구성 (제목 + 내용)
            embed_input = f"Phase: {chunk['phase']}\nSection: {chunk['section']}\n\n{chunk['content']}"
            vector = embed_text(openai_client, embed_input)

            # 고유 ID 생성
            content_hash = hashlib.md5(chunk["content"].encode()).hexdigest()
            point_id_int = int(content_hash[:8], 16)

            point = PointStruct(
                id=point_id_int,
                vector=vector,
                payload={
                    "filename": chunk["filename"],
                    "phase": chunk["phase"],
                    "section": chunk["section"],
                    "content": chunk["content"],
                },
            )
            all_points.append(point)
            point_id += 1

    if all_points:
        # 배치 업서트
        qdrant_client.upsert(
            collection_name=COLLECTION_NAME,
            points=all_points,
        )
        print(f"[Embedder] Successfully embedded {len(all_points)} chunks into Qdrant.")
    else:
        print("[Embedder] No chunks to embed.")

    return len(all_points)
