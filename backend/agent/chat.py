"""
사주팔자 AI 채팅 에이전트
OpenAI GPT 기반 대화 에이전트로, 사주 분석 결과를 자연어로 해석합니다.
"""

import os
from datetime import datetime
from openai import OpenAI

from ..rag.retriever import retrieve_for_analysis


def _build_system_prompt() -> str:
    """현재 날짜를 포함한 시스템 프롬프트를 동적으로 생성합니다."""
    now = datetime.now()
    today_str = now.strftime("%Y년 %m월 %d일")
    current_year = now.year

    # 현재 연도의 천간지지 계산
    stem_idx = (current_year - 4) % 10
    branch_idx = (current_year - 4) % 12
    stems = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    branches = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    stems_ko = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
    branches_ko = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]
    year_ganzi = f"{stems[stem_idx]}{branches[branch_idx]}({stems_ko[stem_idx]}{branches_ko[branch_idx]})"

    return f"""당신은 50년 경력의 사주 전문가 "명리선생"입니다. 마치 실제로 손님 앞에 앉아 점을 봐주는 것처럼 편안하고 자연스럽게 이야기합니다.

[현재 날짜 정보]
오늘: {today_str}
올해: {current_year}년 ({year_ganzi}년)
"올해"는 반드시 {current_year}년입니다. 세운 데이터에서 {current_year}년 항목이 올해입니다.

[말투와 스타일 규칙 - 반드시 지키세요]

1. 진짜 점집에서 이야기하듯이 자연스러운 줄글로 써주세요. 목록(-, *, 1. 2.)이나 표는 쓰지 마세요.
2. 전문 용어는 최대한 피하고, 꼭 필요하면 괄호 안에 쉬운 설명을 붙여주세요. 예: "일간이 辛金인데, 쉽게 말하면 보석처럼 섬세하고 예민한 기질이에요."
3. 한자는 처음 한 번만 쓰고 이후에는 한글로만 써주세요.
4. "---" 수평선은 절대 쓰지 마세요. 주제가 바뀔 때는 빈 줄 두 번으로 구분하세요.
5. 볼드(**강조**)는 정말 핵심 결론 한두 군데에만 쓰세요. 남발하지 마세요.
6. 마크다운 헤딩(#, ##, ###)은 쓰지 마세요. 주제 전환은 자연스럽게 "자, 그러면 성격 이야기를 해볼게요." 같은 문장으로 하세요.
7. 코드 블록, 인용문(>), 테이블은 절대 쓰지 마세요.
8. 친근하지만 품위 있는 존댓말을 쓰세요. "~이에요", "~거든요", "~하셔야 해요" 같은 부드러운 말투요.

[첫 해석 시 다룰 내용 - 순서대로 자연스럽게 이어서]

1. 사주의 전체적인 기운과 타고난 성격
2. 대인관계와 사회성
3. 돈복과 직업운
4. 건강에서 주의할 점
5. 올해({current_year}년) 운세
6. 종합 조언과 행운을 부르는 방법

각 주제를 줄글 문단으로 편하게 풀어주세요. 점 봐주는 사람이 맞은편에 앉아서 차분하게 설명하는 느낌이면 됩니다.

[후속 질문 답변 규칙]

1. 사주 데이터를 근거로 구체적이고 명확하게 답변하세요. "~일 수 있습니다" 같은 애매한 말은 하지 마세요.
2. "사람마다 달라요", "상황에 따라 다릅니다" 같은 일반론은 쓰지 마세요. 이 사람 사주에 맞는 이야기만 하세요.
3. 연애든 직업이든 건강이든, 사주의 오행과 용신을 근거로 딱 잘라 말해주세요.
4. "올해"를 언급할 때는 반드시 {current_year}년 세운 데이터를 참조하세요.
5. 답변도 줄글로 자연스럽게 써주세요. 목록이나 헤딩 쓰지 마세요."""


class SajuChatAgent:
    """사주팔자 AI 채팅 에이전트"""

    def __init__(self, qdrant_host: str = "localhost", qdrant_port: int = 6333):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.qdrant_host = qdrant_host
        self.qdrant_port = qdrant_port
        self.sessions: dict[str, dict] = {}

    def create_session(self, session_id: str, analysis_text: str, analysis_data: dict):
        """새 세션을 생성합니다."""
        # RAG 컨텍스트 가져오기
        try:
            rag_context = retrieve_for_analysis(
                analysis_text,
                qdrant_host=self.qdrant_host,
                qdrant_port=self.qdrant_port,
            )
        except Exception as e:
            print(f"[Agent] RAG retrieval failed (continuing without): {e}")
            rag_context = ""

        # 현재 날짜 정보
        now = datetime.now()
        current_year = now.year
        today_str = now.strftime("%Y년 %m월 %d일")

        # 컨텍스트 메시지 (사주 분석 데이터 + RAG)
        context_message = f"""아래는 사용자의 사주 분석 결과입니다. 이 데이터를 기반으로 해석해주세요.

**중요: 오늘은 {today_str}이며, 올해는 {current_year}년입니다. "올해 운세"를 분석할 때 반드시 세운 데이터에서 {current_year}년 항목을 참조하세요.**

{analysis_text}

{rag_context}"""

        # 시스템 프롬프트를 현재 시점 기준으로 동적 생성
        system_prompt = _build_system_prompt()

        # instructions = 시스템 프롬프트 + 컨텍스트 (Responses API용)
        instructions = f"{system_prompt}\n\n---\n\n{context_message}"

        self.sessions[session_id] = {
            "analysis_data": analysis_data,
            "analysis_text": analysis_text,
            "instructions": instructions,
            "messages": [],  # user/assistant 메시지만 저장
        }

    def get_initial_reading(self, session_id: str) -> str:
        """첫 사주 해석을 생성합니다."""
        if session_id not in self.sessions:
            return "세션을 찾을 수 없습니다."

        session = self.sessions[session_id]

        user_msg = "위의 사주 분석 결과를 바탕으로 종합적인 사주 해석을 해주세요."

        response = self.client.responses.create(
            model="gpt-5.2",
            instructions=session["instructions"],
            input=[{"role": "user", "content": user_msg}],
            temperature=0.7,
            max_output_tokens=3000,
        )

        assistant_msg = response.output_text

        # 대화 이력 저장
        session["messages"].append({"role": "user", "content": "사주 해석을 해주세요."})
        session["messages"].append({"role": "assistant", "content": assistant_msg})

        return assistant_msg

    def chat(self, session_id: str, user_message: str) -> str:
        """후속 대화를 처리합니다."""
        if session_id not in self.sessions:
            return "세션을 찾을 수 없습니다. 먼저 사주 분석을 진행해주세요."

        session = self.sessions[session_id]

        # RAG 보강: 사용자 질문에 관련된 방법론 검색
        try:
            extra_context = ""
            from ..rag.retriever import retrieve
            results = retrieve(
                user_message, top_k=2,
                qdrant_host=self.qdrant_host,
                qdrant_port=self.qdrant_port,
            )
            if results:
                extra_parts = ["\n[참고 방법론]"]
                for r in results:
                    extra_parts.append(f"- {r['phase']}/{r['section']}: {r['content'][:200]}")
                extra_context = "\n".join(extra_parts)
        except Exception:
            extra_context = ""

        # 현재 연도 정보
        now = datetime.now()
        current_year = now.year

        # 사주 데이터 리마인드 + RAG 컨텍스트를 포함한 메시지 구성
        saju_reminder = f"""[사용자 질문] {user_message}

[지시사항] 오늘은 {now.strftime("%Y년 %m월 %d일")}, 올해는 {current_year}년입니다.
사주 데이터를 근거로 구체적이고 명확하게 답변하세요. 애매한 표현은 쓰지 마세요.
줄글로 자연스럽게 쓰세요. 목록, 헤딩(#), 수평선(---) 쓰지 마세요. 볼드는 핵심 한두 곳만 쓰세요."""

        if extra_context:
            saju_reminder = f"{saju_reminder}\n{extra_context}"

        session["messages"].append({"role": "user", "content": saju_reminder})

        # 대화 이력이 너무 길면 최근 메시지만 유지
        recent = session["messages"]
        if len(recent) > 20:
            recent = recent[-20:]

        response = self.client.responses.create(
            model="gpt-5.2",
            instructions=session["instructions"],
            input=recent,
            temperature=0.5,
            max_output_tokens=2000,
        )

        assistant_msg = response.output_text
        session["messages"].append({"role": "assistant", "content": assistant_msg})

        return assistant_msg

    def has_session(self, session_id: str) -> bool:
        return session_id in self.sessions
