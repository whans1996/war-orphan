"""《전란고아》 기본 능력치와 파생 능력치.

원문 규칙의 기본 능력치(STR/AGI/CON/PER/INT/WIL/SEN),
10세 시작 범위, HP/ST 공식을 코드로 옮긴다.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from random import Random
from typing import ClassVar


STAT_MIN = 1
STAT_MAX = 100

# 10세 플레이어 시작 범위. (최솟값, 최댓값)
AGE_10_START_RANGES: dict[str, tuple[int, int]] = {
    "str": (15, 30),
    "agi": (25, 45),
    "con": (20, 40),
    "per": (25, 50),
    "int": (25, 60),
    "wil": (20, 45),
    "sen": (0, 20),
}


@dataclass(slots=True)
class Stats:
    """인간형 캐릭터의 7대 기본 능력치."""

    str: int
    agi: int
    con: int
    per: int
    int: int
    wil: int
    sen: int

    KOREAN_NAMES: ClassVar[dict[str, str]] = {
        "str": "근력",
        "agi": "민첩",
        "con": "체질",
        "per": "감각",
        "int": "오성",
        "wil": "정신",
        "sen": "기감",
    }

    def __post_init__(self) -> None:
        for stat_field in fields(self):
            name = stat_field.name
            value = getattr(self, name)
            if not isinstance(value, int):
                raise TypeError(f"{name} 능력치는 정수여야 합니다: {value!r}")

            # 기감은 원문에서 10세 시작 시 0이 가능하다. 일반 범위의 예외로 허용한다.
            minimum = 0 if name == "sen" else STAT_MIN
            if not minimum <= value <= STAT_MAX:
                raise ValueError(
                    f"{name} 능력치는 {minimum}~{STAT_MAX} 범위여야 합니다: {value}"
                )

    @property
    def max_hp(self) -> int:
        """최대 기혈 HP = 20 + (CON × 2) + STR."""

        return 20 + (self.con * 2) + self.str

    @property
    def max_stamina(self) -> int:
        """최대 체력 ST = 20 + CON + WIL + floor(STR / 2)."""

        return 20 + self.con + self.wil + (self.str // 2)

    def to_dict(self) -> dict[str, int]:
        return {stat_field.name: getattr(self, stat_field.name) for stat_field in fields(self)}

    @classmethod
    def from_dict(cls, data: dict[str, int]) -> "Stats":
        return cls(**{key: int(data[key]) for key in AGE_10_START_RANGES})

    @classmethod
    def random_age_10(cls, rng: Random | None = None) -> "Stats":
        """원문에 명시된 10세 시작 범위 안에서 능력치를 생성한다."""

        generator = rng or Random()
        values = {
            key: generator.randint(low, high)
            for key, (low, high) in AGE_10_START_RANGES.items()
        }
        return cls(**values)

    def display_lines(self) -> list[str]:
        return [
            f"{self.KOREAN_NAMES[name]}({name.upper()}): {getattr(self, name)}"
            for name in AGE_10_START_RANGES
        ]
