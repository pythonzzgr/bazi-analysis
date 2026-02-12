"""
Phase 8: 대운(大運) 및 세운(歲運) 계산
시간에 따른 운의 흐름을 계산하고 원국과의 반응을 분석합니다.
"""

from datetime import datetime
from .calculator import FourPillars, get_yun_data
from .constants import (
    STEM_ELEMENT, BRANCH_ELEMENT, ELEMENT_KO,
    ELEMENT_GENERATES, ELEMENT_CONTROLS,
    HEAVENLY_STEMS, EARTHLY_BRANCHES,
    STEM_KO, BRANCH_KO,
)


def analyze_fortune(
    pillars: FourPillars,
    yong_shin_result: dict,
    birth_year: int,
    birth_month: int,
    birth_day: int,
    birth_hour: int,
    birth_minute: int,
    gender: str,
    is_lunar: bool = False,
    is_leap_month: bool = False,
) -> dict:
    """
    대운 및 현재 세운을 분석합니다.

    Args:
        pillars: 사주 4주
        yong_shin_result: 용신 분석 결과
        birth_*: 생년월일시
        gender: 성별
        is_lunar: 음력 입력 여부
        is_leap_month: 윤달 여부

    Returns:
        대운 리스트, 현재 대운, 현재 세운 분석
    """
    yong_shin = yong_shin_result["yong_shin"]
    gi_shin = yong_shin_result.get("gi_shin", "")

    # 대운 데이터 가져오기
    yun_data = get_yun_data(
        birth_year, birth_month, birth_day, birth_hour, birth_minute, gender,
        is_lunar=is_lunar, is_leap_month=is_leap_month,
    )

    # 현재 나이 계산
    now = datetime.now()
    current_age = now.year - birth_year + 1  # 한국 나이

    # 대운별 점수 매기기
    scored_da_yun = []
    current_da_yun = None

    for dy in yun_data["da_yun"]:
        score = _score_fortune(dy["stem"], dy["branch"], yong_shin, gi_shin, pillars)
        dy_scored = {**dy, "score": score, "rating": _score_to_rating(score)}

        scored_da_yun.append(dy_scored)

        if dy["start_age"] <= current_age <= dy["end_age"]:
            current_da_yun = dy_scored

    # 현재 세운 (올해)
    current_year = now.year
    current_year_fortune = _calculate_yearly_fortune(
        current_year, yong_shin, gi_shin, pillars
    )

    # 향후 5년 세운
    yearly_fortunes = []
    for y in range(current_year, current_year + 6):
        yf = _calculate_yearly_fortune(y, yong_shin, gi_shin, pillars)
        yearly_fortunes.append(yf)

    return {
        "yun_info": {
            "start_year": yun_data["start_year"],
            "start_month": yun_data["start_month"],
            "direction": yun_data["direction"],
        },
        "current_age": current_age,
        "da_yun_list": scored_da_yun,
        "current_da_yun": current_da_yun,
        "current_year_fortune": current_year_fortune,
        "yearly_fortunes": yearly_fortunes,
    }


def _calculate_yearly_fortune(
    year: int,
    yong_shin: str,
    gi_shin: str,
    pillars: FourPillars,
) -> dict:
    """특정 연도의 세운을 계산합니다."""
    # 연도의 천간지지 계산 (60갑자 순환)
    stem_idx = (year - 4) % 10
    branch_idx = (year - 4) % 12
    stem = HEAVENLY_STEMS[stem_idx]
    branch = EARTHLY_BRANCHES[branch_idx]

    score = _score_fortune(stem, branch, yong_shin, gi_shin, pillars)

    return {
        "year": year,
        "stem": stem,
        "branch": branch,
        "ganzi": stem + branch,
        "ganzi_ko": STEM_KO.get(stem, "") + BRANCH_KO.get(branch, ""),
        "stem_element": STEM_ELEMENT[stem],
        "branch_element": BRANCH_ELEMENT[branch],
        "score": score,
        "rating": _score_to_rating(score),
        "summary": _get_fortune_summary(score, stem, branch, yong_shin),
    }


def _score_fortune(
    stem: str,
    branch: str,
    yong_shin: str,
    gi_shin: str,
    pillars: FourPillars,
) -> int:
    """
    대운/세운의 간지를 용신과 비교하여 점수를 매깁니다.

    점수 기준:
    - 용신과 같은 오행: +30
    - 용신을 생하는 오행: +20
    - 용신과 합: +15
    - 기신과 같은 오행: -20
    - 기신을 생하는 오행: -10
    - 원국과 충: -15 (변동성)
    """
    score = 50  # 기본 점수

    stem_elem = STEM_ELEMENT.get(stem, "")
    branch_elem = BRANCH_ELEMENT.get(branch, "")

    for elem in [stem_elem, branch_elem]:
        if not elem:
            continue

        # 용신 관련
        if elem == yong_shin:
            score += 25
        elif ELEMENT_GENERATES.get(elem) == yong_shin:
            score += 15
        elif ELEMENT_GENERATES.get(yong_shin) == elem:
            score += 5

        # 기신 관련
        if elem == gi_shin:
            score -= 20
        elif ELEMENT_GENERATES.get(elem) == gi_shin:
            score -= 10

    # 점수 범위 제한
    score = max(0, min(100, score))
    return score


def _score_to_rating(score: int) -> str:
    """점수를 등급으로 변환"""
    if score >= 85:
        return "대길(大吉)"
    elif score >= 70:
        return "길(吉)"
    elif score >= 55:
        return "보통(普通)"
    elif score >= 40:
        return "흉(凶)"
    else:
        return "대흉(大凶)"


def _get_fortune_summary(score: int, stem: str, branch: str, yong_shin: str) -> str:
    """운세 요약 생성"""
    stem_elem = STEM_ELEMENT.get(stem, "")
    branch_elem = BRANCH_ELEMENT.get(branch, "")
    ganzi_ko = STEM_KO.get(stem, "") + BRANCH_KO.get(branch, "")

    if score >= 85:
        return f"{ganzi_ko}년은 용신 {ELEMENT_KO.get(yong_shin, '')}의 기운이 강하게 작용하여 매사 순조롭고 크게 발전하는 해입니다."
    elif score >= 70:
        return f"{ganzi_ko}년은 전반적으로 좋은 기운이 흐르며, 노력한 만큼 성과를 얻을 수 있는 해입니다."
    elif score >= 55:
        return f"{ganzi_ko}년은 큰 변동 없이 안정적인 해입니다. 꾸준한 노력이 중요합니다."
    elif score >= 40:
        return f"{ganzi_ko}년은 다소 어려움이 예상되는 해입니다. 신중한 판단과 인내가 필요합니다."
    else:
        return f"{ganzi_ko}년은 시련이 예상되는 해입니다. 큰 결정은 피하고 내실을 다지는 것이 좋습니다."
