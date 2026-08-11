"""《전란고아》 캐릭터 코어 모델.

현재 단계에서는 10세 전쟁고아 플레이어의 정체성과 기본 능력치,
기혈(HP), 체력(ST)을 책임진다. 내공·부상·생존·장비는 별도 모듈에서
순차적으로 결합한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from random import Random

from game.stats import Stats


@dataclass(slots=True)
class Character:
    name: str
    age: int
    identity: str
    stats: Stats
    hp: int
    stamina: int
    martial_realm: str = "무인 이전"
    dantian_open: bool = False
    qi: int = 0
    current_internal_energy: int = 0
    max_internal_energy: int = 0

    def __post_init__(self) -> None:
        if self.age <= 0:
            raise ValueError("나이는 1 이상이어야 합니다.")
        if not 0 <= self.hp <= self.max_hp:
            raise ValueError(f"HP가 유효 범위를 벗어났습니다: {self.hp}/{self.max_hp}")
        if not 0 <= self.stamina <= self.max_stamina:
            raise ValueError(
                f"체력이 유효 범위를 벗어났습니다: {self.stamina}/{self.max_stamina}"
            )
        if not self.dantian_open and self.max_internal_energy != 0:
            raise ValueError("단전 미개방 상태의 최대 내력은 0이어야 합니다.")
        if not 0 <= self.current_internal_energy <= self.max_internal_energy:
            raise ValueError("현재 내력이 최대 내력 범위를 벗어났습니다.")

    @property
    def max_hp(self) -> int:
        return self.stats.max_hp

    @property
    def max_stamina(self) -> int:
        return self.stats.max_stamina

    @property
    def is_alive(self) -> bool:
        return self.hp > 0

    @classmethod
    def new_war_orphan(
        cls,
        name: str,
        *,
        rng: Random | None = None,
    ) -> "Character":
        """원문 시작 조건에 맞는 10세 전쟁고아 플레이어를 생성한다."""

        stats = Stats.random_age_10(rng)
        return cls(
            name=name.strip() or "이름 없는 아이",
            age=10,
            identity="전쟁고아",
            stats=stats,
            hp=stats.max_hp,
            stamina=stats.max_stamina,
            martial_realm="무인 이전",
            dantian_open=False,
            qi=0,
            current_internal_energy=0,
            max_internal_energy=0,
        )

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "age": self.age,
            "identity": self.identity,
            "stats": self.stats.to_dict(),
            "hp": self.hp,
            "stamina": self.stamina,
            "martial_realm": self.martial_realm,
            "dantian_open": self.dantian_open,
            "qi": self.qi,
            "current_internal_energy": self.current_internal_energy,
            "max_internal_energy": self.max_internal_energy,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Character":
        return cls(
            name=str(data["name"]),
            age=int(data["age"]),
            identity=str(data["identity"]),
            stats=Stats.from_dict(data["stats"]),
            hp=int(data["hp"]),
            stamina=int(data["stamina"]),
            martial_realm=str(data.get("martial_realm", "무인 이전")),
            dantian_open=bool(data.get("dantian_open", False)),
            qi=int(data.get("qi", 0)),
            current_internal_energy=int(data.get("current_internal_energy", 0)),
            max_internal_energy=int(data.get("max_internal_energy", 0)),
        )

    def status_text(self) -> str:
        stat_block = "\n".join(self.stats.display_lines())
        internal_energy = (
            f"{self.current_internal_energy}/{self.max_internal_energy}"
            if self.dantian_open
            else "단전 미개방"
        )
        return (
            "【상태】\n"
            f"이름: {self.name}\n"
            f"나이: {self.age}세\n"
            f"신분: {self.identity}\n"
            f"경지: {self.martial_realm}\n"
            f"기혈: {self.hp}/{self.max_hp}\n"
            f"체력: {self.stamina}/{self.max_stamina}\n"
            f"내력: {internal_energy}\n\n"
            "【능력치】\n"
            f"{stat_block}"
        )
