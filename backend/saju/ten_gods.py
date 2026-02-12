"""
Phase 5: 십성 배치 분석 (Ten Gods Analysis)
일간과 다른 7개 글자의 십성 관계를 분석합니다.
"""

from .calculator import FourPillars
from .constants import (
    get_ten_god, STEM_ELEMENT, HIDDEN_STEMS,
    TEN_GOD_CATEGORY, TEN_GOD_KO_TO_EN, STEM_KO,
)


def analyze_ten_gods(pillars: FourPillars) -> dict:
    """
    일간 기준 모든 글자의 십성을 배치합니다.

    십성 결정 로직:
    - 비겁(比劫): 오행이 같음 (비견/겁재)
    - 식상(食傷): 일간이 생함 (식신/상관)
    - 재성(財星): 일간이 극함 (편재/정재)
    - 관성(官星): 일간을 극함 (편관/정관)
    - 인성(印星): 일간을 생함 (편인/정인)
    - 음양 같으면 '편', 다르면 '정'
    """
    day_stem = pillars.day.stem

    # 각 위치별 십성 계산
    ten_god_map = {}

    # 천간
    positions = [
        ("year_stem", pillars.year.stem, "연간"),
        ("month_stem", pillars.month.stem, "월간"),
        ("day_stem", pillars.day.stem, "일간"),
        ("time_stem", pillars.time.stem, "시간"),
    ]

    for key, stem, label in positions:
        if key == "day_stem":
            ten_god_map[key] = {
                "char": stem,
                "char_ko": STEM_KO.get(stem, ""),
                "ten_god": "일간(본인)",
                "category": "본인",
                "position": label,
            }
        else:
            tg = get_ten_god(day_stem, stem)
            ten_god_map[key] = {
                "char": stem,
                "char_ko": STEM_KO.get(stem, ""),
                "ten_god": tg,
                "category": TEN_GOD_CATEGORY.get(tg, ""),
                "position": label,
            }

    # 지지
    branch_positions = [
        ("year_branch", pillars.year.branch, "연지"),
        ("month_branch", pillars.month.branch, "월지"),
        ("day_branch", pillars.day.branch, "일지"),
        ("time_branch", pillars.time.branch, "시지"),
    ]

    from .constants import BRANCH_KO

    for key, branch, label in branch_positions:
        # 지지의 본기(주기)로 십성 결정
        hidden = HIDDEN_STEMS.get(branch, [])
        if hidden:
            main_stem = hidden[0][0]
            tg = get_ten_god(day_stem, main_stem)
        else:
            tg = ""

        # 지장간 전체 십성
        hidden_ten_gods = []
        for hs, days in hidden:
            htg = get_ten_god(day_stem, hs)
            hidden_ten_gods.append({
                "stem": hs,
                "stem_ko": STEM_KO.get(hs, ""),
                "ten_god": htg,
                "category": TEN_GOD_CATEGORY.get(htg, ""),
                "days": days,
            })

        ten_god_map[key] = {
            "char": branch,
            "char_ko": BRANCH_KO.get(branch, ""),
            "ten_god": tg,
            "category": TEN_GOD_CATEGORY.get(tg, ""),
            "position": label,
            "hidden_ten_gods": hidden_ten_gods,
        }

    # 십성 분포 통계
    category_count = {"비겁": 0, "식상": 0, "재성": 0, "관성": 0, "인성": 0}
    for key, info in ten_god_map.items():
        cat = info.get("category", "")
        if cat in category_count:
            category_count[cat] += 1

    # 가장 많은 십성 카테고리
    dominant_category = max(category_count, key=lambda k: category_count[k])

    return {
        "ten_god_map": ten_god_map,
        "category_distribution": category_count,
        "dominant_category": dominant_category,
        "interpretation": _get_ten_god_interpretation(dominant_category, category_count),
    }


def _get_ten_god_interpretation(dominant: str, distribution: dict) -> str:
    """십성 분포 기반 해석"""
    interpretations = {
        "비겁": "비겁이 많아 독립심과 자주성이 강하며, 형제/친구의 인연이 깊습니다. 경쟁심이 강할 수 있습니다.",
        "식상": "식상이 많아 표현력과 창의력이 뛰어나며, 예술적 재능이 있습니다. 자유로운 영혼입니다.",
        "재성": "재성이 많아 현실적이고 재물 감각이 뛰어납니다. 사업이나 재테크에 능합니다.",
        "관성": "관성이 많아 책임감이 강하고 조직에서 인정받기 쉽습니다. 규율과 질서를 중시합니다.",
        "인성": "인성이 많아 학문적 능력이 뛰어나고 어른의 도움을 받기 쉽습니다. 사고력이 깊습니다.",
    }

    # 없는 십성 확인
    missing = [k for k, v in distribution.items() if v == 0]

    desc = interpretations.get(dominant, "")
    if missing:
        missing_str = ", ".join(missing)
        desc += f" 사주에 {missing_str}이(가) 부족하여 해당 영역의 보완이 필요합니다."

    return desc
