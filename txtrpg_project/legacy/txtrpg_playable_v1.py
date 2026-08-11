"""A cleaned-up, playable continuation of neophyte88/Txtrpg.

The original project is a small single-file text RPG. This version keeps its
core ideas—three classes, melee/ranged/magic attacks, random enemies, travel,
combat, EXP and regeneration—while fixing runtime bugs and adding save/load.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from random import randint
from typing import Callable

SAVE_FILE = Path(__file__).with_name("txtrpg_save.json")
EXP_TO_LEVEL = 100


def ask_int(prompt: str, valid: set[int]) -> int:
    """Read an integer choice without crashing on bad input."""
    while True:
        try:
            choice = int(input(prompt).strip())
        except ValueError:
            print("숫자로 입력해 주세요.")
            continue
        if choice in valid:
            return choice
        print(f"가능한 선택: {', '.join(map(str, sorted(valid)))}")


class Character:
    def __init__(self, name: str, powers: dict[str, int], buff: str):
        self.name = name
        self.hp = 35
        self.max_hp = 35
        self.gold = 10
        self.level = 1
        self.exp = 0
        self.powers = dict(powers)
        self.buff = buff
        self.equipment: dict[str, str] = {}
        self.items: list[str] = []
        self.set_regen = False

    def _attack(self, kind: str, buff_code: str) -> int:
        bonus = 5 if self.buff == buff_code else 0
        return randint(0, self.powers[kind]) + bonus

    def melee(self) -> int:
        return self._attack("melee", "Me")

    def ranged(self) -> int:
        return self._attack("ranged", "Ra")

    def magic(self) -> int:
        return self._attack("magic", "Mag")

    def gain_exp(self, amount: int) -> None:
        self.exp += amount
        while self.exp >= EXP_TO_LEVEL:
            self.exp -= EXP_TO_LEVEL
            self.level_up()

    def level_up(self) -> None:
        for power in self.powers:
            self.powers[power] += randint(1, 10)
        hp_gain = randint(5, 10)
        self.max_hp += hp_gain
        self.hp = self.max_hp
        self.level += 1
        print(f"\n★ 레벨 업! Lv.{self.level} / 최대 HP +{hp_gain}")

    def regen(self) -> None:
        if self.hp >= self.max_hp:
            self.hp = self.max_hp
            self.set_regen = False
            return
        self.hp = min(self.max_hp, self.hp + 2)
        if self.hp == self.max_hp:
            self.set_regen = False

    def to_dict(self) -> dict:
        return {
            "class": type(self).__name__,
            "name": self.name,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "gold": self.gold,
            "level": self.level,
            "exp": self.exp,
            "powers": self.powers,
            "buff": self.buff,
            "equipment": self.equipment,
            "items": self.items,
            "set_regen": self.set_regen,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Character":
        class_map = {"Knight": Knight, "Archer": Archer, "Mage": Mage}
        player_cls = class_map[data["class"]]
        player = player_cls(data["name"])
        player.hp = int(data["hp"])
        player.max_hp = int(data["max_hp"])
        player.gold = int(data["gold"])
        player.level = int(data["level"])
        player.exp = int(data["exp"])
        player.powers = {k: int(v) for k, v in data["powers"].items()}
        player.buff = str(data["buff"])
        player.equipment = dict(data.get("equipment", {}))
        player.items = list(data.get("items", []))
        player.set_regen = bool(data.get("set_regen", False))
        return player


class Knight(Character):
    def __init__(self, name: str):
        super().__init__(name, {"melee": 15, "ranged": 5, "magic": 5}, "Me")


class Archer(Character):
    def __init__(self, name: str):
        super().__init__(name, {"melee": 5, "ranged": 15, "magic": 5}, "Ra")


class Mage(Character):
    def __init__(self, name: str):
        super().__init__(name, {"melee": 5, "ranged": 5, "magic": 15}, "Mag")


@dataclass
class Item:
    name: str
    type: str


class Enemy:
    NAMES = ["Zombie", "Wolf", "Necromancer", "Bandit", "Rogue", "Skeleton", "Orc", "Elf"]
    RARITIES = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]

    def __init__(self, player_level: int):
        if player_level <= 5:
            rarity_index = randint(0, 1)
            self.power = randint(1, 10)
            self.hp = randint(5, 15)
            self.drop_exp = randint(10, 25)
        elif player_level <= 10:
            rarity_index = randint(0, 2)
            self.power = randint(15, 25)
            self.hp = randint(15, 35)
            self.drop_exp = randint(20, 35)
        else:
            rarity_index = randint(0, 4)
            self.power = randint(25, 50)
            self.hp = randint(20, 50)
            self.drop_exp = randint(35, 45)

        self.rarity = self.RARITIES[rarity_index]
        self.name = f"{self.rarity} {self.NAMES[randint(0, len(self.NAMES) - 1)]}"
        self.drop_gold = max(1, randint(2, 6) + rarity_index * 3)

    def attack(self) -> int:
        return randint(0, self.power)


def show_status(player: Character) -> None:
    print("\n" + "-" * 48)
    print(f"{player.name} | {type(player).__name__} | Lv.{player.level}")
    print(f"HP {player.hp}/{player.max_hp} | EXP {player.exp}/{EXP_TO_LEVEL} | Gold {player.gold}")
    print(
        "Power | "
        f"Melee {player.powers['melee']} / "
        f"Ranged {player.powers['ranged']} / "
        f"Magic {player.powers['magic']}"
    )
    print("-" * 48)


def battle(player: Character, enemy: Enemy) -> bool:
    print("\n" + "=" * 48)
    print(f"{player.name} VS {enemy.name}")
    print(f"내 HP: {player.hp}/{player.max_hp} | 적 HP: {enemy.hp} | 적 공격력: {enemy.power}")
    print("=" * 48)

    attacks: dict[int, tuple[str, Callable[[], int]]] = {
        1: ("Melee", player.melee),
        2: ("Ranged", player.ranged),
        3: ("Magic", player.magic),
    }

    while player.hp > 0 and enemy.hp > 0:
        choice = ask_int("공격 선택: (1) Melee (2) Ranged (3) Magic > ", {1, 2, 3})
        attack_name, attack_fn = attacks[choice]
        damage = attack_fn()
        enemy.hp = max(0, enemy.hp - damage)
        print(f"{attack_name}! {damage} 피해 → {enemy.name} HP {enemy.hp}")

        if enemy.hp <= 0:
            break

        received = enemy.attack()
        player.hp = max(0, player.hp - received)
        print(f"{enemy.name}의 반격! {received} 피해 → 내 HP {player.hp}")

    return player.hp > 0


def travel(player: Character) -> None:
    if player.set_regen:
        player.regen()

    encounter = randint(0, 30)
    if encounter % 3 != 0:
        print("조용한 길이다. 별일 없이 이동했다.")
        return

    enemy = Enemy(player.level)
    print(f"\n⚔ {enemy.name}이(가) 나타났다!")
    action = ask_int("(1) 싸운다 (2) 도망간다 > ", {1, 2})

    if action == 2:
        lost = round(player.gold / 10) if player.gold else 0
        player.gold = max(0, player.gold - lost)
        print(f"도망쳤다. 흘린 골드: {lost}")
        return

    won = battle(player, enemy)
    if won:
        print(f"\n승리! EXP +{enemy.drop_exp}, Gold +{enemy.drop_gold}")
        player.gain_exp(enemy.drop_exp)
        player.gold += enemy.drop_gold
        player.set_regen = player.hp < player.max_hp
    else:
        print("\n패배… 레벨 1과 모든 골드를 잃고 간신히 살아남았다.")
        player.level = max(1, player.level - 1)
        player.gold = 0
        player.hp = max(1, player.max_hp // 2)
        player.set_regen = True


def save_game(player: Character, path: Path = SAVE_FILE) -> None:
    path.write_text(json.dumps(player.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"저장 완료: {path.name}")


def load_game(path: Path = SAVE_FILE) -> Character | None:
    if not path.exists():
        print("저장 파일이 없습니다.")
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        player = Character.from_dict(data)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"저장 파일을 읽지 못했습니다: {exc}")
        return None
    print(f"불러오기 완료: {player.name} Lv.{player.level}")
    return player


def new_game() -> Character:
    class_choice = ask_int("직업 선택: (1) Knight (2) Archer (3) Mage > ", {1, 2, 3})
    name = input("이름 > ").strip() or "Adventurer"
    classes = {1: Knight, 2: Archer, 3: Mage}
    return classes[class_choice](name)


def main() -> None:
    print("\n=== TXTRPG ===")
    choice = ask_int("(1) New Game (2) Load (3) Exit > ", {1, 2, 3})
    if choice == 3:
        return

    player = new_game() if choice == 1 else load_game()
    if player is None:
        player = new_game()

    print(f"\n환영한다, {player.name}!")

    while True:
        print("\n(1) Travel (2) Status (3) Save (4) Exit")
        action = ask_int("> ", {1, 2, 3, 4})
        if action == 1:
            travel(player)
        elif action == 2:
            show_status(player)
        elif action == 3:
            save_game(player)
        else:
            print("게임을 종료한다.")
            break


if __name__ == "__main__":
    main()
