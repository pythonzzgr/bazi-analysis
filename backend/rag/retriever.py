"""
RAG Retriever: 쿼리를 기반으로 Qdrant에서 관련 방법론 문서를 검색합니다.
"""

import os
from openai import OpenAI
from qdrant_client import QdrantClient

from .embedder import COLLECTION_NAME, EMBEDDING_MODEL


def retrieve(
    query: str,
    top_k: int = 3,
    qdrant_host: str = "localhost",
    qdrant_port: int = 6333,
) -> list[dict]:
    """
    쿼리와 관련된 사주 방법론 문서를 검색합니다.

    Args:
        query: 검색 쿼리 (자연어)
        top_k: 반환할 최대 결과 수
        qdrant_host: Qdrant 호스트
        qdrant_port: Qdrant 포트

    Returns:
        관련 문서 청크 리스트 (score, payload 포함)
    """
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port)

    # 쿼리 임베딩
    response = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=query,
    )
    query_vector = response.data[0].embedding

    # Qdrant 검색 (query_points API - qdrant-client v1.12+)
    try:
        results = qdrant_client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=top_k,
        )
    except Exception as e:
        print(f"[Retriever] Search failed: {e}")
        return []

    retrieved = []
    for point in results.points:
        retrieved.append({
            "score": point.score if hasattr(point, "score") else 0.0,
            "filename": point.payload.get("filename", ""),
            "phase": point.payload.get("phase", ""),
            "section": point.payload.get("section", ""),
            "content": point.payload.get("content", ""),
        })

    return retrieved


def retrieve_for_analysis(analysis_text: str, **kwargs) -> str:
    """
    사주 분석 결과를 기반으로 관련 방법론을 검색하여 컨텍스트 문자열로 반환합니다.

    Args:
        analysis_text: 분석 결과 텍스트

    Returns:
        RAG 컨텍스트 문자열
    """
    # 핵심 키워드 추출하여 검색
    queries = [
        "사주 8자 계산 방법과 절기 기준",
        "오행 분석 가중치와 신강 신약 판단 기준",
        "십성 배치와 합충형파 분석 방법",
        "용신 선정 알고리즘과 대운 계산",
    ]

    all_results = []
    seen_contents = set()

    for query in queries:
        results = retrieve(query, top_k=2, **kwargs)
        for r in results:
            content_key = r["content"][:100]
            if content_key not in seen_contents:
                seen_contents.add(content_key)
                all_results.append(r)

    if not all_results:
        return ""

    context_parts = []
    context_parts.append("=== 사주 분석 방법론 (참고 자료) ===\n")
    for r in all_results:
        context_parts.append(f"[{r['phase']} - {r['section']}]")
        context_parts.append(r["content"])
        context_parts.append("")

    return "\n".join(context_parts)
