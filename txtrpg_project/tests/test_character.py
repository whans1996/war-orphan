from random import Random
import unittest

from game.character import Character
from game.stats import AGE_10_START_RANGES, Stats


class StatsTests(unittest.TestCase):
    def test_derived_hp_and_stamina(self) -> None:
        stats = Stats(str=20, agi=30, con=30, per=35, int=40, wil=25, sen=5)
        self.assertEqual(stats.max_hp, 100)
        self.assertEqual(stats.max_stamina, 85)

    def test_age_10_generation_stays_inside_source_ranges(self) -> None:
        stats = Stats.random_age_10(Random(7))
        for key, (low, high) in AGE_10_START_RANGES.items():
            self.assertGreaterEqual(getattr(stats, key), low)
            self.assertLessEqual(getattr(stats, key), high)


class CharacterTests(unittest.TestCase):
    def test_new_war_orphan_source_defaults(self) -> None:
        player = Character.new_war_orphan("소연", rng=Random(11))
        self.assertEqual(player.age, 10)
        self.assertEqual(player.identity, "전쟁고아")
        self.assertEqual(player.martial_realm, "무인 이전")
        self.assertEqual(player.hp, player.max_hp)
        self.assertEqual(player.stamina, player.max_stamina)
        self.assertFalse(player.dantian_open)
        self.assertEqual(player.max_internal_energy, 0)

    def test_character_round_trip(self) -> None:
        player = Character.new_war_orphan("무명", rng=Random(3))
        restored = Character.from_dict(player.to_dict())
        self.assertEqual(restored.to_dict(), player.to_dict())


if __name__ == "__main__":
    unittest.main()
