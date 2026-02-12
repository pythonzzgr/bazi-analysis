"""
사주팔자 분석에 필요한 모든 상수 정의
천간(天干), 지지(地支), 오행(五行), 십성(十星), 합충형파 테이블
"""

# ──────────────────────────── 오행 (Five Elements) ────────────────────────────

ELEMENTS = ["木", "火", "土", "金", "水"]
ELEMENT_KO = {"木": "목", "火": "화", "土": "토", "金": "금", "水": "수"}
ELEMENT_EN = {"木": "Wood", "火": "Fire", "土": "Earth", "金": "Metal", "水": "Water"}

# 오행 상생 (생하는 관계): 木→火→土→金→水→木
ELEMENT_GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}

# 오행 상극 (극하는 관계): 木→土→水→火→金→木
ELEMENT_CONTROLS = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

# ──────────────────────────── 천간 (Heavenly Stems) ──────────────────────────

HEAVENLY_STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
STEM_KO = {
    "甲": "갑", "乙": "을", "丙": "병", "丁": "정", "戊": "무",
    "己": "기", "庚": "경", "辛": "신", "壬": "임", "癸": "계",
}

STEM_ELEMENT = {
    "甲": "木", "乙": "木",
    "丙": "火", "丁": "火",
    "戊": "土", "己": "土",
    "庚": "金", "辛": "金",
    "壬": "水", "癸": "水",
}

STEM_POLARITY = {
    "甲": "양", "乙": "음", "丙": "양", "丁": "음", "戊": "양",
    "己": "음", "庚": "양", "辛": "음", "壬": "양", "癸": "음",
}

# ──────────────────────────── 지지 (Earthly Branches) ────────────────────────

EARTHLY_BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
BRANCH_KO = {
    "子": "자", "丑": "축", "寅": "인", "卯": "묘", "辰": "진", "巳": "사",
    "午": "오", "未": "미", "申": "신", "酉": "유", "戌": "술", "亥": "해",
}

BRANCH_ELEMENT = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
    "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水",
}

BRANCH_POLARITY = {
    "子": "양", "丑": "음", "寅": "양", "卯": "음", "辰": "양", "巳": "음",
    "午": "양", "未": "음", "申": "양", "酉": "음", "戌": "양", "亥": "음",
}

# 지지 계절 매핑
BRANCH_SEASON = {
    "寅": "봄", "卯": "봄", "辰": "환절기",
    "巳": "여름", "午": "여름", "未": "환절기",
    "申": "가을", "酉": "가을", "戌": "환절기",
    "亥": "겨울", "子": "겨울", "丑": "환절기",
}

# ──────────────────────────── 지장간 (Hidden Stems) ──────────────────────────

HIDDEN_STEMS = {
    "子": [("癸", 30)],
    "丑": [("己", 18), ("癸", 9), ("辛", 3)],
    "寅": [("甲", 16), ("丙", 7), ("戊", 7)],
    "卯": [("乙", 30)],
    "辰": [("戊", 18), ("乙", 9), ("癸", 3)],
    "巳": [("丙", 16), ("庚", 7), ("戊", 7)],
    "午": [("丁", 20), ("己", 10)],
    "未": [("己", 18), ("丁", 9), ("乙", 3)],
    "申": [("庚", 16), ("壬", 7), ("戊", 7)],
    "酉": [("辛", 30)],
    "戌": [("戊", 18), ("辛", 9), ("丁", 3)],
    "亥": [("壬", 20), ("甲", 10)],
}

# ──────────────────────────── 60갑자 (Sexagenary Cycle) ──────────────────────

SIXTY_JIAZI = []
for i in range(60):
    stem = HEAVENLY_STEMS[i % 10]
    branch = EARTHLY_BRANCHES[i % 12]
    SIXTY_JIAZI.append(stem + branch)

# ──────────────────────────── 십성 (Ten Gods) ───────────────────────────────

# 일간 오행 기준 다른 오행과의 관계
# (일간오행, 타오행) -> (음양동일일때, 음양상이일때)
TEN_GOD_TABLE = {
    "same":       ("비견", "겁재"),    # 오행 같음
    "i_generate": ("식신", "상관"),    # 내가 생함
    "i_control":  ("편재", "정재"),    # 내가 극함
    "controls_me":("편관", "정관"),    # 나를 극함
    "generates_me":("편인", "정인"),   # 나를 생함
}

TEN_GOD_KO_TO_EN = {
    "비견": "Peer", "겁재": "Rob Wealth",
    "식신": "Eating God", "상관": "Hurting Officer",
    "편재": "Indirect Wealth", "정재": "Direct Wealth",
    "편관": "7-Killing", "정관": "Direct Officer",
    "편인": "Indirect Seal", "정인": "Direct Seal",
}

# 십성 분류
TEN_GOD_CATEGORY = {
    "비견": "비겁", "겁재": "비겁",
    "식신": "식상", "상관": "식상",
    "편재": "재성", "정재": "재성",
    "편관": "관성", "정관": "관성",
    "편인": "인성", "정인": "인성",
}

# ──────────────────────────── 천간합 (Heavenly Stem Combinations) ────────────

# 갑기합토, 을경합금, 병신합수, 정임합목, 무계합화
STEM_COMBINATIONS = {
    frozenset(["甲", "己"]): "土",
    frozenset(["乙", "庚"]): "金",
    frozenset(["丙", "辛"]): "水",
    frozenset(["丁", "壬"]): "木",
    frozenset(["戊", "癸"]): "火",
}

# ──────────────────────────── 지지육합 (Six Branch Combinations) ─────────────

BRANCH_SIX_COMBINATIONS = {
    frozenset(["子", "丑"]): "土",
    frozenset(["寅", "亥"]): "木",
    frozenset(["卯", "戌"]): "火",
    frozenset(["辰", "酉"]): "金",
    frozenset(["巳", "申"]): "水",
    frozenset(["午", "未"]): "土",
}

# ──────────────────────────── 삼합 (Three Harmony) ──────────────────────────

BRANCH_THREE_HARMONY = {
    frozenset(["申", "子", "辰"]): "水",
    frozenset(["亥", "卯", "未"]): "木",
    frozenset(["寅", "午", "戌"]): "火",
    frozenset(["巳", "酉", "丑"]): "金",
}

# ──────────────────────────── 방합 (Directional Harmony) ────────────────────

BRANCH_DIRECTIONAL = {
    frozenset(["寅", "卯", "辰"]): "木",
    frozenset(["巳", "午", "未"]): "火",
    frozenset(["申", "酉", "戌"]): "金",
    frozenset(["亥", "子", "丑"]): "水",
}

# ──────────────────────────── 지충 (Branch Clashes) ─────────────────────────

BRANCH_CLASHES = {
    frozenset(["子", "午"]),
    frozenset(["丑", "未"]),
    frozenset(["寅", "申"]),
    frozenset(["卯", "酉"]),
    frozenset(["辰", "戌"]),
    frozenset(["巳", "亥"]),
}

# ──────────────────────────── 지형 (Branch Punishments) ─────────────────────

BRANCH_PUNISHMENTS = {
    # 삼형 (무례지형)
    frozenset(["寅", "巳", "申"]): "무례지형",
    # 삼형 (은혜지형)
    frozenset(["丑", "戌", "未"]): "은혜지형",
    # 자형
    frozenset(["子", "卯"]): "무례지형",
    # 자형 (자기형)
    frozenset(["午", "午"]): "자형",
    frozenset(["辰", "辰"]): "자형",
    frozenset(["酉", "酉"]): "자형",
    frozenset(["亥", "亥"]): "자형",
}

# ──────────────────────────── 지파 (Branch Breaks) ──────────────────────────

BRANCH_BREAKS = {
    frozenset(["子", "酉"]),
    frozenset(["丑", "辰"]),
    frozenset(["寅", "亥"]),
    frozenset(["卯", "午"]),
    frozenset(["巳", "申"]),
    frozenset(["未", "戌"]),
}

# ──────────────────────────── 월건 (Monthly Stems) ──────────────────────────

# 연간(年干)에 따른 월간 시작 천간
# 갑기년: 병인월 시작, 을경년: 무인월 시작, ...
YEAR_STEM_TO_MONTH_STEM_START = {
    "甲": "丙", "己": "丙",
    "乙": "戊", "庚": "戊",
    "丙": "庚", "辛": "庚",
    "丁": "壬", "壬": "壬",
    "戊": "甲", "癸": "甲",
}

# 월지 순서 (인월~축월)
MONTH_BRANCHES = ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"]

# ──────────────────────────── 시간 → 시주 매핑 ──────────────────────────────

# 일간에 따른 시간 시작 천간
DAY_STEM_TO_HOUR_STEM_START = {
    "甲": "甲", "己": "甲",
    "乙": "丙", "庚": "丙",
    "丙": "戊", "辛": "戊",
    "丁": "庚", "壬": "庚",
    "戊": "壬", "癸": "壬",
}

# 시간대별 지지 매핑 (시작 시각, 지지)
HOUR_TO_BRANCH = [
    (23, "子"), (1, "丑"), (3, "寅"), (5, "卯"),
    (7, "辰"), (9, "巳"), (11, "午"), (13, "未"),
    (15, "申"), (17, "酉"), (19, "戌"), (21, "亥"),
]

# ──────────────────────────── 오행 가중치 (Position Weights) ────────────────

POSITION_WEIGHTS = {
    "year_stem": 10,
    "year_branch": 10,
    "month_stem": 10,
    "month_branch": 35,   # 월지(월령) - 가장 높은 가중치
    "day_stem": 0,         # 일간 본인이므로 제외
    "day_branch": 18,      # 일지 - 배우자궁/본인의 뿌리
    "time_stem": 7,
    "time_branch": 10,
}

# ──────────────────────────── 조후 (Temperature Regulation) ─────────────────

# 월지에 따른 사주 온도 경향
MONTH_TEMPERATURE = {
    "寅": "약간 차가움", "卯": "보통", "辰": "보통",
    "巳": "따뜻함", "午": "매우 뜨거움", "未": "뜨거움",
    "申": "약간 따뜻함", "酉": "보통", "戌": "약간 차가움",
    "亥": "차가움", "子": "매우 차가움", "丑": "매우 차가움",
}

# 조후용신 테이블: (월지, 일간오행) → 필요한 오행
JOHU_YONGSHIN = {
    # 여름생 (사/오/미)이면 수(水)가 필요
    "very_hot": "水",
    "hot": "水",
    # 겨울생 (해/자/축)이면 화(火)가 필요
    "very_cold": "火",
    "cold": "火",
}

# ──────────────────────────── 납음 오행 (Nayin Elements) ────────────────────

NAYIN = {
    "甲子": "海中金", "乙丑": "海中金",
    "丙寅": "爐中火", "丁卯": "爐中火",
    "戊辰": "大林木", "己巳": "大林木",
    "庚午": "路傍土", "辛未": "路傍土",
    "壬申": "劍鋒金", "癸酉": "劍鋒金",
    "甲戌": "山頭火", "乙亥": "山頭火",
    "丙子": "澗下水", "丁丑": "澗下水",
    "戊寅": "城頭土", "己卯": "城頭土",
    "庚辰": "白蠟金", "辛巳": "白蠟金",
    "壬午": "楊柳木", "癸未": "楊柳木",
    "甲申": "泉中水", "乙酉": "泉中水",
    "丙戌": "屋上土", "丁亥": "屋上土",
    "戊子": "霹靂火", "己丑": "霹靂火",
    "庚寅": "松柏木", "辛卯": "松柏木",
    "壬辰": "長流水", "癸巳": "長流水",
    "甲午": "砂中金", "乙未": "砂中金",
    "丙申": "山下火", "丁酉": "山下火",
    "戊戌": "平地木", "己亥": "平地木",
    "庚子": "壁上土", "辛丑": "壁上土",
    "壬寅": "金箔金", "癸卯": "金箔金",
    "甲辰": "覆燈火", "乙巳": "覆燈火",
    "丙午": "天河水", "丁未": "天河水",
    "戊申": "大驛土", "己酉": "大驛土",
    "庚戌": "釵釧金", "辛亥": "釵釧金",
    "壬子": "桑柘木", "癸丑": "桑柘木",
    "甲寅": "大溪水", "乙卯": "大溪水",
    "丙辰": "沙中土", "丁巳": "沙中土",
    "戊午": "天上火", "己未": "天上火",
    "庚申": "石榴木", "辛酉": "石榴木",
    "壬戌": "大海水", "癸亥": "大海水",
}

# ──────────────────────────── 유틸리티 함수 ─────────────────────────────────

def get_element(char: str) -> str:
    """천간 또는 지지의 오행을 반환"""
    if char in STEM_ELEMENT:
        return STEM_ELEMENT[char]
    if char in BRANCH_ELEMENT:
        return BRANCH_ELEMENT[char]
    raise ValueError(f"Unknown character: {char}")


def get_polarity(char: str) -> str:
    """천간 또는 지지의 음양을 반환"""
    if char in STEM_POLARITY:
        return STEM_POLARITY[char]
    if char in BRANCH_POLARITY:
        return BRANCH_POLARITY[char]
    raise ValueError(f"Unknown character: {char}")


def get_relation(self_element: str, other_element: str) -> str:
    """두 오행 사이의 관계를 반환"""
    if self_element == other_element:
        return "same"
    if ELEMENT_GENERATES[self_element] == other_element:
        return "i_generate"
    if ELEMENT_CONTROLS[self_element] == other_element:
        return "i_control"
    if ELEMENT_CONTROLS[other_element] == self_element:
        return "controls_me"
    if ELEMENT_GENERATES[other_element] == self_element:
        return "generates_me"
    raise ValueError(f"No relation found: {self_element} -> {other_element}")


def get_ten_god(day_stem: str, other: str) -> str:
    """일간 기준으로 다른 천간/지지의 십성을 반환"""
    day_element = get_element(day_stem)
    other_element = get_element(other)
    day_pol = get_polarity(day_stem)
    other_pol = get_polarity(other)

    relation = get_relation(day_element, other_element)
    same_polarity = (day_pol == other_pol)
    pair = TEN_GOD_TABLE[relation]
    return pair[0] if same_polarity else pair[1]
