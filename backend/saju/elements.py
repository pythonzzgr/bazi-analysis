"""
Phase 2-3: 오행 분포 분석 (Five Elements Analysis)
일간을 중심으로 사주 전체의 오행 에너지 분포를 가중치 기반으로 분석
"""

from .calculator import FourPillars
from .constants import (
    STEM_ELEMENT, BRANCH_ELEMENT, HIDDEN_STEMS,
    POSITION_WEIGHTS, ELEMENTS, ELEMENT_KO, ELEMENT_EN,
)


def analyze_elements(pillars: FourPillars) -> dict:
    """
    사주의 오행 분포를 가중치 기반으로 분석합니다.

    가중치 기준 (data/2번 파일 참조):
    - 월지(월령): 35점 (계절 주관, 가장 중요)
    - 일지: 18점 (본인의 뿌리)
    - 천간: 각 10점
    - 나머지 지지: 각 10점
    - 지장간: 비례 배분

    Returns:
        오행별 점수, 개수, 비율 등을 포함한 분석 결과
    """
    # 오행별 점수 초기화
    element_scores = {e: 0.0 for e in ELEMENTS}
    element_counts = {e: 0 for e in ELEMENTS}

    # 위치별 매핑
    positions = {
        "year_stem": pillars.year.stem,
        "year_branch": pillars.year.branch,
        "month_stem": pillars.month.stem,
        "month_branch": pillars.month.branch,
        "day_stem": pillars.day.stem,
        "day_branch": pillars.day.branch,
        "time_stem": pillars.time.stem,
        "time_branch": pillars.time.branch,
    }

    # 천간/지지 직접 점수 계산
    for pos_key, char in positions.items():
        weight = POSITION_WEIGHTS[pos_key]
        if weight == 0:
            continue

        if pos_key.endswith("_stem"):
            element = STEM_ELEMENT[char]
            element_scores[element] += weight
            element_counts[element] += 1
        else:
            # 지지는 지장간으로 분배
            branch = char
            hidden = HIDDEN_STEMS.get(branch, [])
            total_days = sum(d for _, d in hidden)
            if total_days > 0:
                for stem, days in hidden:
                    elem = STEM_ELEMENT[stem]
                    ratio = days / total_days
                    element_scores[elem] += weight * ratio

            # 지지 자체의 오행도 카운트
            element_counts[BRANCH_ELEMENT[branch]] += 1

    # 일간(day stem) 본인의 오행 점수도 별도로 추가 (기본 점수)
    day_element = STEM_ELEMENT[pillars.day.stem]
    element_scores[day_element] += 5  # 일간 기본 점수

    # 총점 계산
    total_score = sum(element_scores.values())

    # 비율 계산
    element_ratios = {}
    for e in ELEMENTS:
        element_ratios[e] = round(element_scores[e] / total_score * 100, 1) if total_score > 0 else 0

    # 결과 구성
    stats = {}
    for e in ELEMENTS:
        stats[e] = {
            "element": e,
            "element_ko": ELEMENT_KO[e],
            "element_en": ELEMENT_EN[e],
            "count": element_counts[e],
            "score": round(element_scores[e], 1),
            "ratio": element_ratios[e],
        }

    # 최강/최약 오행
    strongest = max(ELEMENTS, key=lambda e: element_scores[e])
    weakest = min(ELEMENTS, key=lambda e: element_scores[e])

    # 부족한 오행 (5% 미만)
    missing = [e for e in ELEMENTS if element_ratios[e] < 5]

    return {
        "element_stats": stats,
        "total_score": round(total_score, 1),
        "strongest_element": strongest,
        "weakest_element": weakest,
        "missing_elements": missing,
        "day_element": day_element,
        "day_element_ko": ELEMENT_KO[day_element],
    }
