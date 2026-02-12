"""
통합 분석 파이프라인 (Full Analysis Pipeline)
모든 분석 모듈을 순차 호출하여 최종 JSON 결과를 생성합니다.
"""

from .calculator import calculate_four_pillars
from .elements import analyze_elements
from .strength import analyze_strength
from .ten_gods import analyze_ten_gods
from .interactions import analyze_interactions
from .yong_shin import select_yong_shin
from .fortune import analyze_fortune


def full_analysis(
    name: str,
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int = 0,
    gender: str = "남",
    is_lunar: bool = False,
    is_leap_month: bool = False,
) -> dict:
    """
    사주 전체 분석을 수행합니다.

    단계:
    1. 사주 8자 계산 (Four Pillars)
    2. 오행 분포 분석 (Five Elements)
    3. 신강/신약 판단 (Strength)
    4. 십성 배치 (Ten Gods)
    5. 합충형파 분석 (Interactions)
    6. 용신 선정 (Yong-Shin)
    7. 대운/세운 계산 (Fortune)

    Args:
        is_lunar: True이면 음력 날짜로 처리
        is_leap_month: True이면 윤달(閏月)

    Returns:
        모든 분석 결과를 통합한 딕셔너리
    """
    # Phase 1: 사주 8자 계산
    pillars = calculate_four_pillars(
        year, month, day, hour, minute, gender, name,
        is_lunar=is_lunar, is_leap_month=is_leap_month,
    )

    # Phase 2-3: 오행 분석
    element_result = analyze_elements(pillars)

    # Phase 4: 신강/신약 판단
    strength_result = analyze_strength(pillars, element_result)

    # Phase 5: 십성 배치
    ten_gods_result = analyze_ten_gods(pillars)

    # Phase 6: 합충형파 분석
    interactions_result = analyze_interactions(pillars)

    # Phase 7: 용신 선정
    yong_shin_result = select_yong_shin(pillars, element_result, strength_result)

    # Phase 8: 대운/세운 계산
    fortune_result = analyze_fortune(
        pillars, yong_shin_result,
        year, month, day, hour, minute, gender,
        is_lunar=is_lunar, is_leap_month=is_leap_month,
    )

    return {
        "eight_characters": pillars.to_dict(),
        "element_analysis": element_result,
        "strength_analysis": strength_result,
        "ten_gods_analysis": ten_gods_result,
        "interactions_analysis": interactions_result,
        "yong_shin_analysis": yong_shin_result,
        "fortune_analysis": fortune_result,
    }


def analysis_to_text(result: dict) -> str:
    """
    분석 결과를 사람이 읽을 수 있는 텍스트로 변환합니다.
    LLM에게 컨텍스트로 전달하기 위한 구조화된 텍스트입니다.
    """
    ec = result["eight_characters"]
    ea = result["element_analysis"]
    sa = result["strength_analysis"]
    tg = result["ten_gods_analysis"]
    ia = result["interactions_analysis"]
    ys = result["yong_shin_analysis"]
    fa = result["fortune_analysis"]

    lines = []

    # 기본 정보
    lines.append(f"=== 사주팔자 분석 결과 ===")
    lines.append(f"이름: {ec['name']}")
    lines.append(f"성별: {ec['gender']}")
    lines.append(f"양력: {ec['solar_date']}")
    lines.append(f"음력: {ec['lunar_date']}")
    lines.append(f"계절: {ec['season']}")
    lines.append("")

    # 사주 원국
    lines.append("【 사주 원국 (四柱原局) 】")
    for pos in ["year", "month", "day", "time"]:
        p = ec["pillars"][pos]
        pos_ko = {"year": "연주", "month": "월주", "day": "일주", "time": "시주"}[pos]
        lines.append(
            f"  {pos_ko}: {p['ganzi']}({p['ganzi_ko']}) "
            f"[{p['stem_element']}/{p['branch_element']}] "
            f"납음: {p['nayin']}"
        )
    lines.append("")

    # 일간
    ds = ec["day_stem"]
    lines.append(f"【 일간(日干) 】: {ds['stem']}({ds['stem_ko']}) - {ds['element']}({ds['polarity']})")
    lines.append("")

    # 오행 분석
    lines.append("【 오행 분포 】")
    for elem in ["木", "火", "土", "金", "水"]:
        s = ea["element_stats"][elem]
        bar = "█" * int(s["ratio"] / 5) if s["ratio"] > 0 else ""
        lines.append(f"  {s['element_ko']}({elem}): {s['score']:5.1f}점 ({s['ratio']:4.1f}%) {bar}")
    lines.append(f"  최강: {ea['strongest_element']}  최약: {ea['weakest_element']}")
    if ea["missing_elements"]:
        lines.append(f"  부족한 오행: {', '.join(ea['missing_elements'])}")
    lines.append("")

    # 신강/신약
    lines.append(f"【 신강/신약 판단 】: {sa['strength_status']}")
    lines.append(f"  일간 세력 비율: {sa['analysis']['self_support_ratio']}%")
    lines.append(f"  득령: {'○' if sa['analysis']['is_deuk_ryeong'] else '✕'} | "
                 f"득지: {'○' if sa['analysis']['is_deuk_ji'] else '✕'} | "
                 f"득세: {'○' if sa['analysis']['is_deuk_se'] else '✕'}")
    lines.append(f"  {sa['description']}")
    lines.append("")

    # 십성
    lines.append("【 십성 배치 】")
    tgm = tg["ten_god_map"]
    for key in ["year_stem", "month_stem", "day_stem", "time_stem",
                "year_branch", "month_branch", "day_branch", "time_branch"]:
        info = tgm[key]
        lines.append(f"  {info['position']}: {info['char']}({info['char_ko']}) → {info['ten_god']}")
    lines.append(f"  주도 십성: {tg['dominant_category']}")
    lines.append(f"  해석: {tg['interpretation']}")
    lines.append("")

    # 합충형파
    if ia["interactions"]:
        lines.append("【 합충형파 】")
        for inter in ia["interactions"]:
            lines.append(f"  [{inter['type']}] {inter['description']}")
        lines.append("")

    # 용신
    lines.append(f"【 용신 선정 】")
    lines.append(f"  용신(用神): {ys['yong_shin']}({ys['yong_shin_ko']})")
    lines.append(f"  희신(喜神): {ys['hee_shin']}({ys['hee_shin_ko']})")
    lines.append(f"  기신(忌神): {ys['gi_shin']}({ys['gi_shin_ko']})")
    lines.append(f"  선정 방법: {ys['selection_method']}")
    lines.append(f"  근거: {ys['selection_reason']}")
    lines.append("")

    # 추천
    rec = ys["recommendations"]
    lines.append("【 생활 추천 】")
    lines.append(f"  행운색: {', '.join(rec['lucky_colors'])}")
    lines.append(f"  행운 방위: {rec['lucky_direction']}")
    lines.append(f"  행운 숫자: {', '.join(map(str, rec['lucky_numbers']))}")
    lines.append(f"  적합 직업: {rec['career_advice']}")
    lines.append("")

    # 대운
    lines.append("【 대운(大運) 】")
    lines.append(f"  대운 시작: {fa['yun_info']['start_year']}년 {fa['yun_info']['start_month']}개월")
    lines.append(f"  진행 방향: {fa['yun_info']['direction']}")
    if fa["current_da_yun"]:
        cd = fa["current_da_yun"]
        lines.append(f"  현재 대운: {cd['ganzi']}({cd['ganzi_ko']}) [{cd['start_age']}~{cd['end_age']}세] - {cd['rating']} ({cd['score']}점)")
    lines.append("")

    # 세운
    lines.append("【 세운(歲運) - 향후 6년 】")
    for yf in fa["yearly_fortunes"]:
        lines.append(f"  {yf['year']}년 {yf['ganzi']}({yf['ganzi_ko']}): {yf['rating']} ({yf['score']}점) - {yf['summary']}")

    return "\n".join(lines)
