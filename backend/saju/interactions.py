"""
Phase 6: 합(合), 충(沖), 형(刑), 파(破) 분석
글자들 사이의 결합과 충돌을 통해 오행의 변화와 사건 발생을 예측합니다.

처리 우선순위: 방합 > 삼합 > 육합 > 충 > 형/파/해
"""

from .calculator import FourPillars
from .constants import (
    STEM_COMBINATIONS, BRANCH_SIX_COMBINATIONS,
    BRANCH_THREE_HARMONY, BRANCH_DIRECTIONAL,
    BRANCH_CLASHES, BRANCH_PUNISHMENTS, BRANCH_BREAKS,
    STEM_KO, BRANCH_KO, ELEMENT_KO,
)


def analyze_interactions(pillars: FourPillars) -> dict:
    """
    사주 내 천간/지지의 합충형파 관계를 분석합니다.

    Returns:
        발견된 모든 상호작용 목록과 해석
    """
    interactions = []

    stems = [
        ("연간", pillars.year.stem),
        ("월간", pillars.month.stem),
        ("일간", pillars.day.stem),
        ("시간", pillars.time.stem),
    ]

    branches = [
        ("연지", pillars.year.branch),
        ("월지", pillars.month.branch),
        ("일지", pillars.day.branch),
        ("시지", pillars.time.branch),
    ]

    # ─────── 1. 천간합 분석 ───────
    for i in range(len(stems)):
        for j in range(i + 1, len(stems)):
            pair = frozenset([stems[i][1], stems[j][1]])
            if pair in STEM_COMBINATIONS:
                result_element = STEM_COMBINATIONS[pair]
                interactions.append({
                    "type": "천간합",
                    "priority": 3,
                    "elements": [stems[i][1], stems[j][1]],
                    "elements_ko": [STEM_KO[stems[i][1]], STEM_KO[stems[j][1]]],
                    "positions": [stems[i][0], stems[j][0]],
                    "result": result_element,
                    "result_ko": ELEMENT_KO.get(result_element, ""),
                    "impact": "medium",
                    "description": (
                        f"{stems[i][0]} {STEM_KO[stems[i][1]]}과(와) "
                        f"{stems[j][0]} {STEM_KO[stems[j][1]]}이(가) "
                        f"합하여 {ELEMENT_KO.get(result_element, '')}({result_element})의 기운을 생성합니다."
                    ),
                })

    branch_list = [b[1] for b in branches]
    branch_set = set(branch_list)

    # ─────── 2. 방합 분석 (최우선) ───────
    for combo, result_element in BRANCH_DIRECTIONAL.items():
        if combo.issubset(branch_set):
            members = list(combo)
            pos_list = [branches[branch_list.index(m)][0] for m in members if m in branch_list]
            interactions.append({
                "type": "방합",
                "priority": 1,
                "elements": members,
                "elements_ko": [BRANCH_KO[m] for m in members],
                "positions": pos_list,
                "result": result_element,
                "result_ko": ELEMENT_KO.get(result_element, ""),
                "impact": "very_high",
                "description": (
                    f"{', '.join(BRANCH_KO[m] for m in members)}이(가) "
                    f"방합하여 강력한 {ELEMENT_KO.get(result_element, '')}({result_element})국을 형성합니다."
                ),
            })

    # ─────── 3. 삼합 분석 ───────
    for combo, result_element in BRANCH_THREE_HARMONY.items():
        matching = combo.intersection(branch_set)
        if len(matching) >= 2:
            members = list(matching)
            pos_list = [branches[branch_list.index(m)][0] for m in members if m in branch_list]
            is_full = len(matching) == 3

            interactions.append({
                "type": "삼합" if is_full else "반삼합",
                "priority": 2 if is_full else 2.5,
                "elements": members,
                "elements_ko": [BRANCH_KO[m] for m in members],
                "positions": pos_list,
                "result": result_element,
                "result_ko": ELEMENT_KO.get(result_element, ""),
                "impact": "high" if is_full else "medium",
                "description": (
                    f"{', '.join(BRANCH_KO[m] for m in members)}이(가) "
                    f"{'삼합' if is_full else '반삼합'}하여 "
                    f"{ELEMENT_KO.get(result_element, '')}({result_element})국을 {'형성' if is_full else '지향'}합니다."
                ),
            })

    # ─────── 4. 육합 분석 ───────
    for i in range(len(branches)):
        for j in range(i + 1, len(branches)):
            pair = frozenset([branches[i][1], branches[j][1]])
            if pair in BRANCH_SIX_COMBINATIONS:
                result_element = BRANCH_SIX_COMBINATIONS[pair]
                interactions.append({
                    "type": "육합",
                    "priority": 3,
                    "elements": [branches[i][1], branches[j][1]],
                    "elements_ko": [BRANCH_KO[branches[i][1]], BRANCH_KO[branches[j][1]]],
                    "positions": [branches[i][0], branches[j][0]],
                    "result": result_element,
                    "result_ko": ELEMENT_KO.get(result_element, ""),
                    "impact": "medium",
                    "description": (
                        f"{branches[i][0]} {BRANCH_KO[branches[i][1]]}과(와) "
                        f"{branches[j][0]} {BRANCH_KO[branches[j][1]]}이(가) "
                        f"육합하여 {ELEMENT_KO.get(result_element, '')}({result_element})의 기운을 생성합니다."
                    ),
                })

    # ─────── 5. 지충 분석 ───────
    for i in range(len(branches)):
        for j in range(i + 1, len(branches)):
            pair = frozenset([branches[i][1], branches[j][1]])
            if pair in BRANCH_CLASHES:
                interactions.append({
                    "type": "충",
                    "priority": 4,
                    "elements": [branches[i][1], branches[j][1]],
                    "elements_ko": [BRANCH_KO[branches[i][1]], BRANCH_KO[branches[j][1]]],
                    "positions": [branches[i][0], branches[j][0]],
                    "result": "",
                    "impact": "high",
                    "description": (
                        f"{branches[i][0]} {BRANCH_KO[branches[i][1]]}과(와) "
                        f"{branches[j][0]} {BRANCH_KO[branches[j][1]]}이(가) "
                        f"충하여 변화와 이동의 에너지가 있습니다."
                    ),
                })

    # ─────── 6. 형(刑) 분석 ───────
    # 삼형 체크
    for combo, punishment_type in BRANCH_PUNISHMENTS.items():
        members = list(combo)
        # 자형(같은 글자 2개) 체크
        if len(members) == 2 and members[0] == members[1]:
            count = branch_list.count(members[0])
            if count >= 2:
                interactions.append({
                    "type": "자형",
                    "priority": 5,
                    "elements": [members[0]],
                    "elements_ko": [BRANCH_KO[members[0]]],
                    "positions": [],
                    "result": "",
                    "impact": "medium",
                    "description": (
                        f"{BRANCH_KO[members[0]]}이(가) 자형(自刑)합니다. "
                        f"자기 자신과의 갈등이나 내면적 고뇌를 의미합니다."
                    ),
                })
        elif len(members) == 2 and members[0] != members[1]:
            # 자묘 형
            if set(members).issubset(branch_set):
                interactions.append({
                    "type": "형",
                    "priority": 5,
                    "elements": members,
                    "elements_ko": [BRANCH_KO[m] for m in members],
                    "positions": [],
                    "result": "",
                    "impact": "medium",
                    "description": (
                        f"{BRANCH_KO[members[0]]}과(와) {BRANCH_KO[members[1]]}이(가) "
                        f"{punishment_type}으로 형(刑)합니다."
                    ),
                })
        elif len(members) == 3:
            matching = set(members).intersection(branch_set)
            if len(matching) >= 2:
                interactions.append({
                    "type": "삼형",
                    "priority": 5,
                    "elements": list(matching),
                    "elements_ko": [BRANCH_KO[m] for m in matching],
                    "positions": [],
                    "result": "",
                    "impact": "high" if len(matching) == 3 else "medium",
                    "description": (
                        f"{', '.join(BRANCH_KO[m] for m in matching)}이(가) "
                        f"{punishment_type}으로 형(刑)합니다."
                    ),
                })

    # ─────── 7. 파(破) 분석 ───────
    for i in range(len(branches)):
        for j in range(i + 1, len(branches)):
            pair = frozenset([branches[i][1], branches[j][1]])
            if pair in BRANCH_BREAKS:
                interactions.append({
                    "type": "파",
                    "priority": 6,
                    "elements": [branches[i][1], branches[j][1]],
                    "elements_ko": [BRANCH_KO[branches[i][1]], BRANCH_KO[branches[j][1]]],
                    "positions": [branches[i][0], branches[j][0]],
                    "result": "",
                    "impact": "low",
                    "description": (
                        f"{branches[i][0]} {BRANCH_KO[branches[i][1]]}과(와) "
                        f"{branches[j][0]} {BRANCH_KO[branches[j][1]]}이(가) "
                        f"파(破)합니다. 관계에 미세한 균열을 의미합니다."
                    ),
                })

    # 우선순위 정렬
    interactions.sort(key=lambda x: x["priority"])

    # 요약
    type_counts = {}
    for inter in interactions:
        t = inter["type"]
        type_counts[t] = type_counts.get(t, 0) + 1

    return {
        "interactions": interactions,
        "type_counts": type_counts,
        "total_count": len(interactions),
        "has_major_clash": any(i["type"] == "충" for i in interactions),
        "has_harmony": any(i["type"] in ("방합", "삼합", "육합", "천간합") for i in interactions),
    }
