"""
Phase 4: 신강/신약 판단 (Strength Analysis)
일간의 세력을 분석하여 신강/신약/중화를 판단합니다.

3대 지표:
1. 득령(得令): 월지가 일간을 돕는가?
2. 득지(得地): 일지에 일간의 뿌리(통근)가 있는가?
3. 득세(得勢): 전체적으로 일간을 돕는 세력이 많은가?
"""

from .calculator import FourPillars
from .constants import (
    STEM_ELEMENT, BRANCH_ELEMENT, HIDDEN_STEMS,
    ELEMENT_GENERATES, TEN_GOD_CATEGORY,
    get_ten_god,
)


def _is_supporting_element(day_element: str, other_element: str) -> bool:
    """
    해당 오행이 일간을 돕는 오행인지 판단합니다.
    비겁(같은 오행) 또는 인성(일간을 생하는 오행)이면 True
    """
    if day_element == other_element:
        return True  # 비겁
    if ELEMENT_GENERATES[other_element] == day_element:
        return True  # 인성 (나를 생함)
    return False


def analyze_strength(pillars: FourPillars, element_analysis: dict) -> dict:
    """
    신강/신약을 판단합니다.

    Args:
        pillars: 사주 4주
        element_analysis: 오행 분석 결과

    Returns:
        신강/신약 판단 결과
    """
    day_stem = pillars.day.stem
    day_element = STEM_ELEMENT[day_stem]

    # ─────── 1. 득령(得令) 판단 ───────
    month_branch = pillars.month.branch
    month_element = BRANCH_ELEMENT[month_branch]
    month_hidden = HIDDEN_STEMS.get(month_branch, [])

    # 월지 본기(가장 큰 비중)가 일간을 돕는가
    is_deuk_ryeong = False
    if month_hidden:
        main_hidden_element = STEM_ELEMENT[month_hidden[0][0]]
        is_deuk_ryeong = _is_supporting_element(day_element, main_hidden_element)

    # ─────── 2. 득지(得地) 판단 ───────
    day_branch = pillars.day.branch
    day_hidden = HIDDEN_STEMS.get(day_branch, [])

    is_deuk_ji = False
    for stem, _ in day_hidden:
        if STEM_ELEMENT[stem] == day_element:
            is_deuk_ji = True
            break

    # ─────── 3. 득세(得勢) 판단 ───────
    # 일간을 제외한 7자 중 일간을 돕는 글자의 비율
    support_count = 0
    total_count = 0

    all_chars = [
        pillars.year.stem, pillars.month.stem, pillars.time.stem,  # 천간 (일간 제외)
        pillars.year.branch, pillars.month.branch,
        pillars.day.branch, pillars.time.branch,  # 지지
    ]

    for char in all_chars:
        total_count += 1
        if char in STEM_ELEMENT:
            elem = STEM_ELEMENT[char]
        else:
            elem = BRANCH_ELEMENT[char]

        if _is_supporting_element(day_element, elem):
            support_count += 1

    is_deuk_se = support_count > total_count / 2

    # ─────── 종합 점수 계산 ───────
    # 인성 + 비겁 점수 합계
    stats = element_analysis["element_stats"]
    supporting_score = 0
    total_score = element_analysis["total_score"]

    # 비겁 (같은 오행)
    supporting_score += stats[day_element]["score"]

    # 인성 (나를 생하는 오행)
    for elem in stats:
        if ELEMENT_GENERATES[elem] == day_element:
            supporting_score += stats[elem]["score"]

    support_ratio = round(supporting_score / total_score * 100, 1) if total_score > 0 else 0

    # ─────── 신강/신약 판단 ───────
    deuk_count = sum([is_deuk_ryeong, is_deuk_ji, is_deuk_se])

    if support_ratio >= 55:
        strength_status = "身强(신강)"
        strength_level = "strong"
    elif support_ratio >= 50 and deuk_count >= 2:
        strength_status = "身强(신강)"
        strength_level = "strong"
    elif support_ratio <= 40:
        strength_status = "身弱(신약)"
        strength_level = "weak"
    elif support_ratio <= 45 and deuk_count <= 1:
        strength_status = "身弱(신약)"
        strength_level = "weak"
    else:
        strength_status = "中和(중화)"
        strength_level = "balanced"

    # 극단적 경우
    if support_ratio >= 70:
        strength_status = "極强(극강)"
        strength_level = "very_strong"
    elif support_ratio <= 25:
        strength_status = "極弱(극약)"
        strength_level = "very_weak"

    return {
        "strength_status": strength_status,
        "strength_level": strength_level,
        "analysis": {
            "self_support_score": round(supporting_score, 1),
            "self_support_ratio": support_ratio,
            "is_deuk_ryeong": is_deuk_ryeong,
            "is_deuk_ji": is_deuk_ji,
            "is_deuk_se": is_deuk_se,
            "deuk_count": deuk_count,
        },
        "description": _get_strength_description(strength_level, is_deuk_ryeong, is_deuk_ji, is_deuk_se),
    }


def _get_strength_description(
    level: str, deuk_ryeong: bool, deuk_ji: bool, deuk_se: bool
) -> str:
    """신강/신약 판단 근거 설명"""
    parts = []

    if deuk_ryeong:
        parts.append("월령(月令)의 도움을 받아 득령(得令)하였습니다")
    else:
        parts.append("월령(月令)의 도움을 받지 못해 실령(失令)하였습니다")

    if deuk_ji:
        parts.append("일지에 뿌리(通根)를 두어 득지(得地)하였습니다")
    else:
        parts.append("일지에 뿌리가 없어 실지(失地)하였습니다")

    if deuk_se:
        parts.append("주변 세력의 도움이 많아 득세(得勢)하였습니다")
    else:
        parts.append("주변 세력의 도움이 부족하여 실세(失勢)하였습니다")

    status_desc = {
        "very_strong": "일간의 세력이 매우 강한 극강 사주입니다.",
        "strong": "일간의 세력이 강한 신강 사주입니다.",
        "balanced": "일간의 세력이 균형을 이룬 중화 사주입니다.",
        "weak": "일간의 세력이 약한 신약 사주입니다.",
        "very_weak": "일간의 세력이 매우 약한 극약 사주입니다.",
    }

    parts.append(status_desc.get(level, ""))
    return " ".join(parts)
