"""
Phase 7: 용신 선정 알고리즘 (Yong-Shin Selection)
사주의 균형을 맞추기 위해 가장 필요한 핵심 오행을 도출합니다.

선정 방법:
1. 억부용신(抑扶): 신강하면 식재관을, 신약하면 인비를 선정
2. 조후용신(調候): 너무 춥거나 더운 경우 온도 조절 오행 우선
3. 통관용신(通關): 두 오행이 격렬히 대립할 때 연결 오행
"""

from __future__ import annotations
from typing import Optional

from .constants import (
    ELEMENTS, ELEMENT_KO, ELEMENT_EN,
    ELEMENT_GENERATES, ELEMENT_CONTROLS,
    STEM_ELEMENT, BRANCH_ELEMENT,
    MONTH_TEMPERATURE,
)
from .calculator import FourPillars


def select_yong_shin(
    pillars: FourPillars,
    element_analysis: dict,
    strength_analysis: dict,
) -> dict:
    """
    용신(用神), 희신(喜神), 기신(忌神)을 선정합니다.

    Args:
        pillars: 사주 4주
        element_analysis: 오행 분석 결과
        strength_analysis: 신강/신약 분석 결과

    Returns:
        용신/희신/기신 정보와 선정 근거
    """
    day_element = STEM_ELEMENT[pillars.day.stem]
    strength_level = strength_analysis["strength_level"]
    month_branch = pillars.month.branch
    temperature = MONTH_TEMPERATURE.get(month_branch, "보통")
    stats = element_analysis["element_stats"]

    # ─────── 1단계: 조후용신 체크 ───────
    johu_needed = _check_johu(temperature, day_element, stats)

    # ─────── 2단계: 통관용신 체크 ───────
    tonggwan_needed = _check_tonggwan(stats)

    # ─────── 3단계: 억부용신 결정 ───────
    yong_shin, hee_shin, gi_shin, reason = _select_by_strength(
        day_element, strength_level, stats
    )

    # 조후가 필요하면 조후 우선
    if johu_needed and temperature in ("매우 뜨거움", "매우 차가움"):
        yong_shin = johu_needed
        reason = f"조후용신: {temperature} 사주로 온도 조절이 최우선입니다."

    # 통관이 필요하면 통관 우선
    if tonggwan_needed:
        yong_shin = tonggwan_needed["mediator"]
        reason = (
            f"통관용신: {ELEMENT_KO[tonggwan_needed['element1']]}과(와) "
            f"{ELEMENT_KO[tonggwan_needed['element2']]}의 대립을 "
            f"{ELEMENT_KO[tonggwan_needed['mediator']]}이(가) 중재합니다."
        )

    # 기신은 용신을 극하는 오행
    if not gi_shin:
        gi_shin = ELEMENT_CONTROLS.get(
            next((e for e in ELEMENTS if ELEMENT_CONTROLS[e] == yong_shin), ""), ""
        )
        # 기신: 용신을 극하는 오행
        for e in ELEMENTS:
            if ELEMENT_CONTROLS[e] == yong_shin:
                gi_shin = e
                break

    return {
        "yong_shin": yong_shin,
        "yong_shin_ko": ELEMENT_KO.get(yong_shin, ""),
        "yong_shin_en": ELEMENT_EN.get(yong_shin, ""),
        "hee_shin": hee_shin,
        "hee_shin_ko": ELEMENT_KO.get(hee_shin, ""),
        "gi_shin": gi_shin,
        "gi_shin_ko": ELEMENT_KO.get(gi_shin, ""),
        "selection_method": _get_method_name(johu_needed, tonggwan_needed),
        "selection_reason": reason,
        "temperature": temperature,
        "recommendations": _get_recommendations(yong_shin, hee_shin),
    }


def _check_johu(temperature: str, day_element: str, stats: dict) -> str:
    """조후용신 필요 여부 체크"""
    if temperature in ("매우 뜨거움", "뜨거움"):
        return "水"
    if temperature in ("매우 차가움", "차가움"):
        return "火"
    return ""


def _check_tonggwan(stats: dict) -> dict | None:
    """
    통관용신 필요 여부 체크.
    두 오행이 각각 30% 이상이면 대립으로 간주.
    """
    high_elements = [e for e in ELEMENTS if stats[e]["ratio"] >= 30]

    if len(high_elements) >= 2:
        e1, e2 = high_elements[0], high_elements[1]
        # 두 오행이 상극 관계인지 확인
        if ELEMENT_CONTROLS[e1] == e2 or ELEMENT_CONTROLS[e2] == e1:
            # 중재자: e1이 e2를 극하면 → e1이 생하는 오행이 중재
            if ELEMENT_CONTROLS[e1] == e2:
                mediator = ELEMENT_GENERATES[e1]
            else:
                mediator = ELEMENT_GENERATES[e2]
            return {
                "element1": e1,
                "element2": e2,
                "mediator": mediator,
            }
    return None


def _select_by_strength(
    day_element: str,
    strength_level: str,
    stats: dict,
) -> tuple[str, str, str, str]:
    """억부용신 결정"""

    # 일간을 생하는 오행 (인성)
    insung_element = ""
    for e in ELEMENTS:
        if ELEMENT_GENERATES[e] == day_element:
            insung_element = e
            break

    # 일간이 생하는 오행 (식상)
    siksang_element = ELEMENT_GENERATES[day_element]
    # 일간이 극하는 오행 (재성)
    jaesung_element = ELEMENT_CONTROLS[day_element]
    # 일간을 극하는 오행 (관성)
    gwansung_element = ""
    for e in ELEMENTS:
        if ELEMENT_CONTROLS[e] == day_element:
            gwansung_element = e
            break

    if strength_level in ("strong", "very_strong"):
        # 신강: 기운을 설기(泄氣)해야 함 → 식상/재성/관성 필요
        # 최적: 가장 약한 식/재/관 중 선택
        candidates = [
            (siksang_element, stats[siksang_element]["score"]),
            (jaesung_element, stats[jaesung_element]["score"]),
            (gwansung_element, stats[gwansung_element]["score"]),
        ]
        # 가장 점수가 낮은(=가장 필요한) 것을 용신으로
        candidates.sort(key=lambda x: x[1])
        yong_shin = candidates[0][0]
        hee_shin = candidates[1][0]
        gi_shin = insung_element  # 인성은 기신 (더 강하게 만드므로)

        reason = (
            f"억부용신: 신강 사주이므로 기운을 설기하는 "
            f"{ELEMENT_KO[yong_shin]}({yong_shin})이(가) 필요합니다."
        )

    elif strength_level in ("weak", "very_weak"):
        # 신약: 기운을 보충해야 함 → 인성/비겁 필요
        candidates = [
            (insung_element, stats[insung_element]["score"]),
            (day_element, stats[day_element]["score"]),  # 비겁
        ]
        candidates.sort(key=lambda x: x[1])
        yong_shin = candidates[0][0]
        hee_shin = candidates[1][0]
        gi_shin = gwansung_element  # 관성은 기신 (더 약하게 만드므로)

        reason = (
            f"억부용신: 신약 사주이므로 기운을 보충하는 "
            f"{ELEMENT_KO[yong_shin]}({yong_shin})이(가) 필요합니다."
        )

    else:
        # 중화: 가장 부족한 오행을 보충
        weakest = min(ELEMENTS, key=lambda e: stats[e]["score"])
        yong_shin = weakest
        hee_shin = ELEMENT_GENERATES.get(weakest, "")
        # 기신: 가장 과한 오행
        strongest = max(ELEMENTS, key=lambda e: stats[e]["score"] if e != day_element else 0)
        gi_shin = strongest

        reason = (
            f"중화 사주이지만 {ELEMENT_KO[weakest]}({weakest})이(가) "
            f"부족하여 이를 보충합니다."
        )

    return yong_shin, hee_shin, gi_shin, reason


def _get_method_name(johu: str, tonggwan: dict | None) -> str:
    if johu:
        return "조후용신(調候用神)"
    if tonggwan:
        return "통관용신(通關用神)"
    return "억부용신(抑扶用神)"


def _get_recommendations(yong_shin: str, hee_shin: str) -> dict:
    """용신/희신 기반 생활 추천"""
    color_map = {
        "木": ["초록색", "청색"],
        "火": ["빨간색", "보라색"],
        "土": ["노란색", "갈색"],
        "金": ["흰색", "은색"],
        "水": ["검정색", "파란색"],
    }
    direction_map = {
        "木": "동쪽",
        "火": "남쪽",
        "土": "중앙",
        "金": "서쪽",
        "水": "북쪽",
    }
    number_map = {
        "木": [3, 8],
        "火": [2, 7],
        "土": [5, 10],
        "金": [4, 9],
        "水": [1, 6],
    }
    career_map = {
        "木": "교육, 출판, 패션, 의류, 농업, 원예 관련 분야",
        "火": "방송, 연예, IT, 전기전자, 음식업 관련 분야",
        "土": "부동산, 건설, 농업, 중개업 관련 분야",
        "金": "금융, 법률, 의료, 기계, 자동차 관련 분야",
        "水": "무역, 물류, 유통, 수산업, 관광 관련 분야",
    }

    return {
        "lucky_colors": color_map.get(yong_shin, []) + color_map.get(hee_shin, []),
        "lucky_direction": direction_map.get(yong_shin, ""),
        "lucky_numbers": number_map.get(yong_shin, []),
        "career_advice": career_map.get(yong_shin, ""),
    }
