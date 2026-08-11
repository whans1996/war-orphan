"""Playable Txtrpg continuation - survival/inventory milestone.

This keeps the tiny original project's single-file spirit while moving the
prototype toward the 《전란고아》 survival rules: persistent carried items,
equipment, food/water/medicine, encumbrance, survival needs, loot and saves.

The Knight/Archer/Mage choice is intentionally kept for one more milestone as
compatibility scaffolding. A later milestone can replace it with the 10-year-old
war-orphan character generator without throwing away the systems built here.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from random import choice, randint, random
from typing import Callable

SAVE_FILE = Path(__file__).with_name("txtrpg_save.json")
EXP_TO_LEVEL = 100
SAVE_VERSION = 2


def ask_int(prompt: str, valid: set[int]) -> int:
    """Read an integer choice without crashing on bad input."""
    while True:
        try:
            value = int(input(prompt).strip())
        except ValueError:
            print("숫자로 입력해 주세요.")
            continue
        if value in valid:
            return value
        print(f"가능한 선택: {', '.join(map(str, sorted(valid)))}")


@dataclass(frozen=True)
class ItemDef:
    key: str
    name: str
    category: str
    weight: float
    value: int
    description: str
    slot: str | None = None
    attack_kind: str | None = None
    attack_bonus: int = 0
    defense: int = 0
    hp_restore: int = 0
    hunger_restore: int = 0
    thirst_restore: int = 0


ITEMS: dict[str, ItemDef] = {
    "rusty_sword": ItemDef(
        "rusty_sword", "녹슨 단검", "weapon", 1.4, 5,
        "날이 무뎌졌지만 맨손보다는 낫다.", "weapon", "melee", 3,
    ),
    "short_bow": ItemDef(
        "short_bow", "낡은 단궁", "weapon", 1.2, 6,
        "작은 체격에도 겨우 다룰 수 있는 짧은 활.", "weapon", "ranged", 3,
    ),
    "worn_staff": ItemDef(
        "worn_staff", "금 간 목봉", "weapon", 1.8, 4,
        "여행용 지팡이로도 쓸 수 있는 낡은 목봉.", "weapon", "magic", 3,
    ),
    "patched_clothes": ItemDef(
        "patched_clothes", "기운 누더기옷", "armor", 1.0, 2,
        "여러 번 기워 입은 옷. 약간의 보호만 제공한다.", "body", defense=1,
    ),
    "leather_vest": ItemDef(
        "leather_vest", "해진 가죽조끼", "armor", 2.4, 12,
        "낡았지만 칼끝과 이빨을 조금 흘려준다.", "body", defense=2,
    ),
    "grain_cake": ItemDef(
        "grain_cake", "잡곡떡", "food", 0.25, 2,
        "딱딱하고 거칠지만 허기를 달랜다.", hunger_restore=28,
    ),
    "water_skin": ItemDef(
        "water_skin", "물 한 몫", "drink", 0.55, 1,
        "물주머니에서 한 번 마실 수 있는 양.", thirst_restore=35,
    ),
    "bandage": ItemDef(
        "bandage", "깨끗한 천붕대", "medicine", 0.10, 3,
        "가벼운 상처를 감싸는 데 쓸 수 있다.", hp_restore=4,
    ),
    "herbal_salvo": ItemDef(
        "herbal_salvo", "상처 연고", "medicine", 0.18, 6,
        "피부 상처에 바르는 값싼 약.", hp_restore=8,
    ),
    "scrap_metal": ItemDef(
        "scrap_metal", "쓸 만한 쇳조각", "material", 0.65, 2,
        "당장 쓸모는 적지만 대장간에서 값이 나갈 수 있다.",
    ),
    "wolf_hide": ItemDef(
        "wolf_hide", "들개 가죽", "material", 1.6, 4,
        "제대로 손질하면 팔 수 있는 거친 가죽.",
    ),
}


class Character:
    def __init__(self, name: str, powers: dict[str, int], buff: str):
        self.name = name
        self.age = 10
        self.hp = 35
        self.max_hp = 35
        self.gold = 10  # compatibility name; treated as small coin in UI
        self.level = 1
        self.exp = 0
        self.powers = dict(powers)
        self.buff = buff
        self.inventory: dict[str, int] = {}
        self.equipment: dict[str, str] = {}
        self.hunger = 15  # 0 good -> 100 critical
        self.thirst = 10
        self.fatigue = 10
        self.max_carry_weight = 12.0
        self.set_regen = False  # retained for old saves; no travel auto-heal

    # ---------- combat ----------
    def equipment_attack_bonus(self, kind: str) -> int:
        key = self.equipment.get("weapon")
        if not key or key not in ITEMS:
            return 0
        item = ITEMS[key]
        return item.attack_bonus if item.attack_kind == kind else 0

    def defense(self) -> int:
        total = 0
        for key in self.equipment.values():
            item = ITEMS.get(key)
            if item:
                total += item.defense
        return total

    def survival_attack_penalty(self) -> int:
        penalty = 0
        if self.hunger >= 70:
            penalty += 2
        if self.thirst >= 70:
            penalty += 3
        if self.fatigue >= 70:
            penalty += 3
        if self.hunger >= 90:
            penalty += 2
        if self.thirst >= 90:
            penalty += 3
        if self.fatigue >= 90:
            penalty += 2
        return penalty

    def _attack(self, kind: str, buff_code: str) -> int:
        class_bonus = 5 if self.buff == buff_code else 0
        equipment_bonus = self.equipment_attack_bonus(kind)
        penalty = self.survival_attack_penalty()
        ceiling = max(1, self.powers[kind] + class_bonus + equipment_bonus - penalty)
        return randint(0, ceiling)

    def melee(self) -> int:
        return self._attack("melee", "Me")

    def ranged(self) -> int:
        return self._attack("ranged", "Ra")

    def magic(self) -> int:
        return self._attack("magic", "Mag")

    # ---------- progression ----------
    def gain_exp(self, amount: int) -> None:
        self.exp += amount
        while self.exp >= EXP_TO_LEVEL:
            self.exp -= EXP_TO_LEVEL
            self.level_up()

    def level_up(self) -> None:
        for power in self.powers:
            self.powers[power] += randint(1, 6)
        hp_gain = randint(3, 6)
        self.max_hp += hp_gain
        self.hp = min(self.max_hp, self.hp + hp_gain)
        self.max_carry_weight += 0.5
        self.level += 1
        print(f"\n★ 성장! Lv.{self.level} / 최대 HP +{hp_gain} / 휴대 한도 +0.5")

    # ---------- inventory ----------
    def carried_weight(self) -> float:
        return round(
            sum(ITEMS[key].weight * qty for key, qty in self.inventory.items() if key in ITEMS),
            2,
        )

    def can_carry(self, key: str, qty: int = 1) -> bool:
        return self.carried_weight() + ITEMS[key].weight * qty <= self.max_carry_weight + 1e-9

    def add_item(self, key: str, qty: int = 1) -> bool:
        if key not in ITEMS or qty <= 0:
            return False
        if not self.can_carry(key, qty):
            return False
        self.inventory[key] = self.inventory.get(key, 0) + qty
        return True

    def remove_item(self, key: str, qty: int = 1) -> bool:
        if qty <= 0 or self.inventory.get(key, 0) < qty:
            return False
        self.inventory[key] -= qty
        if self.inventory[key] <= 0:
            self.inventory.pop(key, None)
            for slot, equipped_key in list(self.equipment.items()):
                if equipped_key == key:
                    self.equipment.pop(slot, None)
        return True

    def equip(self, key: str) -> tuple[bool, str]:
        if self.inventory.get(key, 0) <= 0 or key not in ITEMS:
            return False, "그 물건은 가지고 있지 않다."
        item = ITEMS[key]
        if not item.slot:
            return False, "장착할 수 없는 물건이다."
        old = self.equipment.get(item.slot)
        self.equipment[item.slot] = key
        if old and old != key:
            return True, f"{ITEMS[old].name} 대신 {item.name}을(를) 장착했다."
        return True, f"{item.name}을(를) 장착했다."

    def use_item(self, key: str) -> tuple[bool, str]:
        if self.inventory.get(key, 0) <= 0 or key not in ITEMS:
            return False, "그 물건은 가지고 있지 않다."
        item = ITEMS[key]
        if item.category not in {"food", "drink", "medicine"}:
            return False, "지금 바로 사용할 수 있는 소비품이 아니다."

        before = (self.hp, self.hunger, self.thirst)
        if item.hp_restore:
            self.hp = min(self.max_hp, self.hp + item.hp_restore)
        if item.hunger_restore:
            self.hunger = max(0, self.hunger - item.hunger_restore)
        if item.thirst_restore:
            self.thirst = max(0, self.thirst - item.thirst_restore)

        if before == (self.hp, self.hunger, self.thirst):
            return False, "지금은 써도 얻는 효과가 없다."

        self.remove_item(key, 1)
        parts: list[str] = []
        if self.hp != before[0]:
            parts.append(f"HP {before[0]}→{self.hp}")
        if self.hunger != before[1]:
            parts.append(f"허기 {before[1]}→{self.hunger}")
        if self.thirst != before[2]:
            parts.append(f"갈증 {before[2]}→{self.thirst}")
        return True, f"{item.name} 사용: " + ", ".join(parts)

    # ---------- survival ----------
    def advance_travel_needs(self) -> None:
        self.hunger = min(100, self.hunger + randint(6, 10))
        self.thirst = min(100, self.thirst + randint(9, 14))
        self.fatigue = min(100, self.fatigue + randint(7, 11))

        if self.thirst >= 95:
            self.hp = max(1, self.hp - 3)
        elif self.hunger >= 95 or self.fatigue >= 95:
            self.hp = max(1, self.hp - 1)

    def rest(self) -> str:
        old_fatigue = self.fatigue
        old_hp = self.hp
        self.fatigue = max(0, self.fatigue - 35)
        self.hunger = min(100, self.hunger + 5)
        self.thirst = min(100, self.thirst + 7)
        if self.hunger < 75 and self.thirst < 75 and self.hp < self.max_hp:
            self.hp = min(self.max_hp, self.hp + 2)
        return (
            f"휴식: 피로 {old_fatigue}→{self.fatigue}, HP {old_hp}→{self.hp}. "
            f"쉬는 동안 허기와 갈증은 조금 늘었다."
        )

    # ---------- save ----------
    def to_dict(self) -> dict:
        return {
            "save_version": SAVE_VERSION,
            "class": type(self).__name__,
            "name": self.name,
            "age": self.age,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "gold": self.gold,
            "level": self.level,
            "exp": self.exp,
            "powers": self.powers,
            "buff": self.buff,
            "inventory": self.inventory,
            "equipment": self.equipment,
            "hunger": self.hunger,
            "thirst": self.thirst,
            "fatigue": self.fatigue,
            "max_carry_weight": self.max_carry_weight,
            "set_regen": False,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Character":
        class_map = {"Knight": Knight, "Archer": Archer, "Mage": Mage}
        player_cls = class_map.get(data.get("class"), Knight)
        player = player_cls(str(data.get("name", "Adventurer")), give_starter_items=False)
        player.age = int(data.get("age", 10))
        player.hp = int(data.get("hp", player.hp))
        player.max_hp = int(data.get("max_hp", player.max_hp))
        player.gold = int(data.get("gold", 0))
        player.level = int(data.get("level", 1))
        player.exp = int(data.get("exp", 0))
        player.powers = {k: int(v) for k, v in data.get("powers", player.powers).items()}
        player.buff = str(data.get("buff", player.buff))

        raw_inventory = data.get("inventory")
        if isinstance(raw_inventory, dict):
            player.inventory = {
                str(key): int(qty)
                for key, qty in raw_inventory.items()
                if key in ITEMS and int(qty) > 0
            }
        else:
            # v1 migration: old saves had a list[str] named "items" but no real item data.
            player.inventory = {}

        raw_equipment = data.get("equipment", {})
        if isinstance(raw_equipment, dict):
            player.equipment = {
                str(slot): str(key)
                for slot, key in raw_equipment.items()
                if str(key) in ITEMS and player.inventory.get(str(key), 0) > 0
            }
        player.hunger = int(data.get("hunger", 15))
        player.thirst = int(data.get("thirst", 10))
        player.fatigue = int(data.get("fatigue", 10))
        player.max_carry_weight = float(data.get("max_carry_weight", 12.0))
        player.set_regen = False
        return player


class Knight(Character):
    def __init__(self, name: str, give_starter_items: bool = True):
        super().__init__(name, {"melee": 15, "ranged": 5, "magic": 5}, "Me")
        if give_starter_items:
            give_starter_kit(self, "rusty_sword")


class Archer(Character):
    def __init__(self, name: str, give_starter_items: bool = True):
        super().__init__(name, {"melee": 5, "ranged": 15, "magic": 5}, "Ra")
        if give_starter_items:
            give_starter_kit(self, "short_bow")


class Mage(Character):
    def __init__(self, name: str, give_starter_items: bool = True):
        super().__init__(name, {"melee": 5, "ranged": 5, "magic": 15}, "Mag")
        if give_starter_items:
            give_starter_kit(self, "worn_staff")


def give_starter_kit(player: Character, weapon_key: str) -> None:
    for key, qty in {
        weapon_key: 1,
        "patched_clothes": 1,
        "grain_cake": 2,
        "water_skin": 2,
        "bandage": 1,
    }.items():
        player.add_item(key, qty)
    player.equip(weapon_key)
    player.equip("patched_clothes")


class Enemy:
    """Small milestone enemy model. Exact hidden stats are still shown in debug-like combat UI."""

    TEMPLATES = [
        ("굶주린 들개", "beast"),
        ("떠돌이 산적", "bandit"),
        ("패잔병", "soldier"),
        ("길목 도적", "bandit"),
        ("독기 없는 산뱀", "beast"),
    ]

    def __init__(self, player_level: int):
        self.name, self.kind = choice(self.TEMPLATES)
        if player_level <= 5:
            self.power = randint(2, 8)
            self.hp = randint(7, 15)
            self.drop_exp = randint(8, 20)
        elif player_level <= 10:
            self.power = randint(8, 18)
            self.hp = randint(15, 30)
            self.drop_exp = randint(18, 30)
        else:
            self.power = randint(16, 30)
            self.hp = randint(25, 45)
            self.drop_exp = randint(28, 42)
        self.drop_gold = randint(0, 5) if self.kind != "beast" else 0

    def attack(self) -> int:
        return randint(0, self.power)

    def roll_loot(self) -> list[tuple[str, int]]:
        loot: list[tuple[str, int]] = []
        if self.kind == "beast":
            if random() < 0.65:
                loot.append(("wolf_hide", 1))
        else:
            if random() < 0.35:
                loot.append(("grain_cake", 1))
            if random() < 0.25:
                loot.append(("bandage", 1))
            if random() < 0.20:
                loot.append(("scrap_metal", 1))
            if random() < 0.08:
                loot.append(("leather_vest", 1))
        return loot


def need_label(value: int) -> str:
    if value < 30:
        return "양호"
    if value < 55:
        return "신경 쓰임"
    if value < 75:
        return "나쁨"
    if value < 90:
        return "위험"
    return "위급"


def show_status(player: Character) -> None:
    print("\n" + "-" * 56)
    print(f"{player.name} | {type(player).__name__} | {player.age}세 | Lv.{player.level}")
    print(f"HP {player.hp}/{player.max_hp} | EXP {player.exp}/{EXP_TO_LEVEL} | 동전 {player.gold}")
    print(
        f"허기 {player.hunger}/100({need_label(player.hunger)}) | "
        f"갈증 {player.thirst}/100({need_label(player.thirst)}) | "
        f"피로 {player.fatigue}/100({need_label(player.fatigue)})"
    )
    print(
        "기초 능력 | "
        f"근접 {player.powers['melee']} / 원거리 {player.powers['ranged']} / 특수 {player.powers['magic']}"
    )
    print(f"휴대 {player.carried_weight():.2f}/{player.max_carry_weight:.2f}")
    if player.equipment:
        equipped = ", ".join(f"{slot}: {ITEMS[key].name}" for slot, key in player.equipment.items())
    else:
        equipped = "없음"
    print(f"장비 | {equipped} | 방어 {player.defense()}")
    print("-" * 56)


def inventory_rows(player: Character) -> list[str]:
    return sorted(player.inventory)


def show_inventory(player: Character) -> None:
    print("\n【소지품】")
    print(f"휴대 중량: {player.carried_weight():.2f}/{player.max_carry_weight:.2f}")
    keys = inventory_rows(player)
    if not keys:
        print("(비어 있음)")
        return
    for idx, key in enumerate(keys, 1):
        item = ITEMS[key]
        equipped = " [장착]" if key in player.equipment.values() else ""
        print(
            f"{idx}. {item.name} x{player.inventory[key]} | {item.category} | "
            f"{item.weight:.2f}씩{equipped}"
        )
        print(f"   {item.description}")


def inventory_menu(player: Character, combat: bool = False) -> bool:
    """Return True if a combat turn was consumed by using an item."""
    while True:
        show_inventory(player)
        print("(1) 사용 (2) 장착 (3) 버리기 (4) 돌아가기")
        action = ask_int("> ", {1, 2, 3, 4})
        if action == 4:
            return False
        keys = inventory_rows(player)
        if not keys:
            return False
        idx = ask_int("물건 번호 > ", set(range(1, len(keys) + 1)))
        key = keys[idx - 1]
        item = ITEMS[key]

        if action == 1:
            ok, message = player.use_item(key)
            print(message)
            if ok and combat:
                return True
        elif action == 2:
            if combat:
                print("교전 중 장비 교체는 이번 단계에서는 허용하지 않는다.")
                continue
            _, message = player.equip(key)
            print(message)
        elif action == 3:
            if key in player.equipment.values():
                print("장착 중인 물건은 먼저 다른 장비로 교체해야 한다.")
                continue
            player.remove_item(key, 1)
            print(f"{item.name} 1개를 내려놓았다.")


def battle(player: Character, enemy: Enemy) -> bool:
    print("\n" + "=" * 56)
    print(f"{player.name} VS {enemy.name}")
    print(f"내 HP: {player.hp}/{player.max_hp} | 상대 상태: 겉보기엔 아직 움직일 수 있다.")
    print("=" * 56)

    attacks: dict[int, tuple[str, Callable[[], int]]] = {
        1: ("근접", player.melee),
        2: ("원거리", player.ranged),
        3: ("특수", player.magic),
    }

    while player.hp > 0 and enemy.hp > 0:
        print(f"\n내 HP {player.hp}/{player.max_hp} | 허기 {player.hunger} 갈증 {player.thirst} 피로 {player.fatigue}")
        action = ask_int("(1) 근접 (2) 원거리 (3) 특수 (4) 소지품 > ", {1, 2, 3, 4})
        if action == 4:
            turn_used = inventory_menu(player, combat=True)
            if not turn_used:
                continue
        else:
            attack_name, attack_fn = attacks[action]
            damage = attack_fn()
            enemy.hp = max(0, enemy.hp - damage)
            if enemy.hp == 0:
                print(f"{attack_name} 공격이 제대로 들어갔다. {enemy.name}이(가) 쓰러졌다.")
            elif damage == 0:
                print(f"{attack_name} 공격이 빗나가거나 제대로 힘이 실리지 않았다.")
            else:
                print(f"{attack_name} 공격으로 {damage}만큼 타격을 입혔다.")

        if enemy.hp <= 0:
            break

        raw = enemy.attack()
        received = max(0, raw - player.defense())
        player.hp = max(0, player.hp - received)
        if received == 0:
            print(f"{enemy.name}의 공격을 장비가 받아냈다.")
        else:
            print(f"{enemy.name}의 반격으로 {received}만큼 피해를 입었다. HP {player.hp}")

    return player.hp > 0


def collect_loot(player: Character, enemy: Enemy) -> None:
    loot = enemy.roll_loot()
    if not loot:
        print("가져갈 만한 물건은 보이지 않는다.")
        return

    print("\n【전리품】")
    for key, qty in loot:
        item = ITEMS[key]
        print(f"- {item.name} x{qty} ({item.weight * qty:.2f} 무게)")
        if player.add_item(key, qty):
            print("  → 챙겼다.")
        else:
            print("  → 너무 무거워 챙기지 못했다. 그 자리에 남겼다.")


def travel(player: Character) -> None:
    player.advance_travel_needs()
    print(
        f"길을 옮겼다. 허기 {player.hunger}, 갈증 {player.thirst}, 피로 {player.fatigue}."
    )

    encounter = randint(0, 30)
    if encounter % 3 != 0:
        print("이번 길에서는 눈에 띄는 충돌 없이 지나갔다.")
        return

    enemy = Enemy(player.level)
    print(f"\n⚔ 길 앞을 {enemy.name}이(가) 가로막는다.")
    action = ask_int("(1) 싸운다 (2) 달아난다 > ", {1, 2})

    if action == 2:
        lost = round(player.gold / 10) if player.gold else 0
        player.gold = max(0, player.gold - lost)
        player.fatigue = min(100, player.fatigue + 8)
        print(f"간신히 벗어났다. 달아나는 와중 동전 {lost}개를 흘렸다.")
        return

    won = battle(player, enemy)
    if won:
        print(f"\n승리. 경험 +{enemy.drop_exp}, 동전 +{enemy.drop_gold}")
        player.gain_exp(enemy.drop_exp)
        player.gold += enemy.drop_gold
        collect_loot(player, enemy)
    else:
        print("\n패배했다. 목숨은 붙어 있지만 돈과 물건 일부를 잃었다.")
        player.gold = max(0, player.gold // 2)
        player.hp = max(1, player.max_hp // 3)
        player.fatigue = min(100, player.fatigue + 20)
        # Causal simplification for this milestone: one non-equipped stack may be lost.
        loose = [key for key in player.inventory if key not in player.equipment.values()]
        if loose:
            lost_key = choice(loose)
            player.remove_item(lost_key, 1)
            print(f"정신을 차렸을 때 {ITEMS[lost_key].name} 1개가 사라져 있었다.")


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
    print("※ 클래스 선택은 원본 Txtrpg 호환용 임시 구조다. 다음 마일스톤에서 전란고아식 생성으로 교체한다.")
    class_choice = ask_int("기초 성향: (1) 근접 (2) 원거리 (3) 특수 > ", {1, 2, 3})
    name = input("이름 > ").strip() or "이름 없는 아이"
    classes = {1: Knight, 2: Archer, 3: Mage}
    return classes[class_choice](name)


def main() -> None:
    print("\n=== TXTRPG : Survival Milestone ===")
    choice_main = ask_int("(1) 새 게임 (2) 불러오기 (3) 종료 > ", {1, 2, 3})
    if choice_main == 3:
        return

    player = new_game() if choice_main == 1 else load_game()
    if player is None:
        player = new_game()

    print(f"\n{player.name}, 길 위에서 살아남아야 한다.")

    while True:
        print("\n(1) 이동 (2) 상태 (3) 소지품 (4) 휴식 (5) 저장 (6) 종료")
        action = ask_int("> ", {1, 2, 3, 4, 5, 6})
        if action == 1:
            travel(player)
        elif action == 2:
            show_status(player)
        elif action == 3:
            inventory_menu(player)
        elif action == 4:
            print(player.rest())
        elif action == 5:
            save_game(player)
        else:
            print("게임을 종료한다.")
            break


if __name__ == "__main__":
    main()
