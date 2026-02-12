"""
Phase 1: 사주 8자 계산 (Four Pillars Calculation)
lunar_python 라이브러리를 활용한 만세력 기반 정확한 간지 계산
양력/음력 입력 및 윤달(閏月) 처리를 지원합니다.
"""

from dataclasses import dataclass, field
from typing import Optional
from lunar_python import Solar, Lunar, LunarYear

from .constants import (
    HIDDEN_STEMS, STEM_KO, BRANCH_KO, STEM_ELEMENT, BRANCH_ELEMENT,
    STEM_POLARITY, BRANCH_POLARITY, NAYIN, BRANCH_SEASON,
)


@dataclass
class Pillar:
    """간지 한 쌍 (천간 + 지지)"""
    stem: str          # 천간 (한자)
    branch: str        # 지지 (한자)
    stem_ko: str = ""  # 천간 (한글)
    branch_ko: str = "" # 지지 (한글)
    stem_element: str = ""
    branch_element: str = ""
    stem_polarity: str = ""
    branch_polarity: str = ""
    hidden_stems: list = field(default_factory=list)
    nayin: str = ""

    def __post_init__(self):
        self.stem_ko = STEM_KO.get(self.stem, "")
        self.branch_ko = BRANCH_KO.get(self.branch, "")
        self.stem_element = STEM_ELEMENT.get(self.stem, "")
        self.branch_element = BRANCH_ELEMENT.get(self.branch, "")
        self.stem_polarity = STEM_POLARITY.get(self.stem, "")
        self.branch_polarity = BRANCH_POLARITY.get(self.branch, "")
        self.hidden_stems = HIDDEN_STEMS.get(self.branch, [])
        gz = self.stem + self.branch
        self.nayin = NAYIN.get(gz, "")

    @property
    def ganzi(self) -> str:
        return self.stem + self.branch

    @property
    def ganzi_ko(self) -> str:
        return self.stem_ko + self.branch_ko

    def to_dict(self) -> dict:
        return {
            "stem": self.stem,
            "branch": self.branch,
            "stem_ko": self.stem_ko,
            "branch_ko": self.branch_ko,
            "ganzi": self.ganzi,
            "ganzi_ko": self.ganzi_ko,
            "stem_element": self.stem_element,
            "branch_element": self.branch_element,
            "stem_polarity": self.stem_polarity,
            "branch_polarity": self.branch_polarity,
            "hidden_stems": [
                {"stem": s, "stem_ko": STEM_KO.get(s, ""), "days": d}
                for s, d in self.hidden_stems
            ],
            "nayin": self.nayin,
        }


@dataclass
class FourPillars:
    """사주 4주 (연주/월주/일주/시주)"""
    year: Pillar
    month: Pillar
    day: Pillar
    time: Pillar
    solar_date: str = ""
    lunar_date: str = ""
    gender: str = ""     # "남" or "여"
    name: str = ""
    season: str = ""
    is_lunar_input: bool = False      # 음력 입력 여부
    is_leap_month: bool = False       # 윤달 여부

    def __post_init__(self):
        self.season = BRANCH_SEASON.get(self.month.branch, "")

    @property
    def day_stem(self) -> str:
        """일간 (일주의 천간) - 사주 분석의 핵심"""
        return self.day.stem

    def all_stems(self) -> list[str]:
        """모든 천간 목록"""
        return [self.year.stem, self.month.stem, self.day.stem, self.time.stem]

    def all_branches(self) -> list[str]:
        """모든 지지 목록"""
        return [self.year.branch, self.month.branch, self.day.branch, self.time.branch]

    def all_characters(self) -> list[str]:
        """8자 모두"""
        return self.all_stems() + self.all_branches()

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "gender": self.gender,
            "solar_date": self.solar_date,
            "lunar_date": self.lunar_date,
            "is_lunar_input": self.is_lunar_input,
            "is_leap_month": self.is_leap_month,
            "season": self.season,
            "pillars": {
                "year": self.year.to_dict(),
                "month": self.month.to_dict(),
                "day": self.day.to_dict(),
                "time": self.time.to_dict(),
            },
            "day_stem": {
                "stem": self.day.stem,
                "stem_ko": self.day.stem_ko,
                "element": self.day.stem_element,
                "polarity": self.day.stem_polarity,
            },
        }


def calculate_four_pillars(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int = 0,
    gender: str = "남",
    name: str = "",
    is_lunar: bool = False,
    is_leap_month: bool = False,
) -> FourPillars:
    """
    생년월일시로부터 사주 4주를 계산합니다.
    양력/음력 입력 및 윤달을 지원합니다.

    Args:
        year: 년도
        month: 월
        day: 일
        hour: 시간 (0-23)
        minute: 분 (0-59)
        gender: "남" 또는 "여"
        name: 이름
        is_lunar: True이면 음력 입력으로 처리
        is_leap_month: True이면 해당 월이 윤달(閏月)

    Returns:
        FourPillars 객체
    """
    if is_lunar:
        # 음력 입력: Lunar 객체로 생성 후 Solar로 변환
        # 윤달인 경우 month를 음수로 전달 (lunar_python 규칙)
        lunar_month = -month if is_leap_month else month
        lunar = Lunar.fromYmdHms(year, lunar_month, day, hour, minute, 0)
        solar = lunar.getSolar()
    else:
        # 양력 입력: Solar 객체로 바로 생성
        solar = Solar(year, month, day, hour, minute, 0)
        lunar = solar.getLunar()

    ba_zi = lunar.getEightChar()

    year_pillar = Pillar(stem=ba_zi.getYearGan(), branch=ba_zi.getYearZhi())
    month_pillar = Pillar(stem=ba_zi.getMonthGan(), branch=ba_zi.getMonthZhi())
    day_pillar = Pillar(stem=ba_zi.getDayGan(), branch=ba_zi.getDayZhi())
    time_pillar = Pillar(stem=ba_zi.getTimeGan(), branch=ba_zi.getTimeZhi())

    # 음력 날짜 문자열 (윤달 표시 포함)
    lunar_month_abs = abs(lunar.getMonth())
    leap_mark = "(윤)" if is_leap_month and is_lunar else ""
    lunar_str = f"{lunar.getYear()}년 {leap_mark}{lunar_month_abs}월 {lunar.getDay()}일"

    solar_str = (
        f"{solar.getYear()}년 {solar.getMonth()}월 {solar.getDay()}일 "
        f"{hour}시 {minute}분"
    )

    return FourPillars(
        year=year_pillar,
        month=month_pillar,
        day=day_pillar,
        time=time_pillar,
        solar_date=solar_str,
        lunar_date=lunar_str,
        gender=gender,
        name=name,
        is_lunar_input=is_lunar,
        is_leap_month=is_leap_month,
    )


def get_leap_month_for_year(year: int) -> int:
    """
    해당 음력 연도에 윤달이 있는지 확인합니다.

    Args:
        year: 음력 연도

    Returns:
        윤달이 있는 월 번호 (없으면 0)
    """
    try:
        return LunarYear.fromYear(year).getLeapMonth()
    except Exception:
        return 0


def get_yun_data(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    gender: str,
    is_lunar: bool = False,
    is_leap_month: bool = False,
) -> dict:
    """
    대운 정보를 계산합니다.

    Returns:
        대운 리스트와 시작 정보를 포함한 딕셔너리
    """
    if is_lunar:
        lunar_month = -month if is_leap_month else month
        lunar = Lunar.fromYmdHms(year, lunar_month, day, hour, minute, 0)
    else:
        solar = Solar(year, month, day, hour, minute, 0)
        lunar = solar.getLunar()
    ba_zi = lunar.getEightChar()

    # gender: 1 = 남, 0 = 여
    gender_code = 1 if gender == "남" else 0
    yun = ba_zi.getYun(gender_code)

    start_year = yun.getStartYear()
    start_month = yun.getStartMonth()
    start_day = yun.getStartDay()

    da_yun_list = []
    da_yun_objs = yun.getDaYun()

    for dy in da_yun_objs:
        ganzi = dy.getGanZhi()
        if not ganzi:
            continue

        stem = ganzi[0] if ganzi else ""
        branch = ganzi[1] if len(ganzi) > 1 else ""

        da_yun_list.append({
            "start_age": dy.getStartAge(),
            "end_age": dy.getEndAge(),
            "stem": stem,
            "branch": branch,
            "ganzi": ganzi,
            "stem_ko": STEM_KO.get(stem, ""),
            "branch_ko": BRANCH_KO.get(branch, ""),
            "ganzi_ko": STEM_KO.get(stem, "") + BRANCH_KO.get(branch, ""),
            "stem_element": STEM_ELEMENT.get(stem, ""),
            "branch_element": BRANCH_ELEMENT.get(branch, ""),
        })

    return {
        "start_year": start_year,
        "start_month": start_month,
        "start_day": start_day,
        "direction": "순행" if gender_code == 1 else "역행",
        "da_yun": da_yun_list,
    }
