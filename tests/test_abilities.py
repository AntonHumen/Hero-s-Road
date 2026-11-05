import unittest
from types import SimpleNamespace

from abilities import (ArmorRage, Ability, LowHpRage, Regeneration, SpeedStrike,
                       create_ability)
from stats import Stats


def actor(hp=10, shield=0, attack=1, speed=0):
    return SimpleNamespace(stats=Stats(hp, shield, attack, speed))


class AbilityTests(unittest.TestCase):
    def test_wolf_rage_only_at_low_hp(self):
        wolf, hero = LowHpRage(hp_threshold=5, bonus=2), actor(hp=10)
        enemy = actor()
        self.assertEqual(wolf.attack_bonus(hero, enemy), 0)
        hero.stats.hp = 5
        self.assertEqual(wolf.attack_bonus(hero, enemy), 2)

    def test_bear_rage_depends_on_hero_shield(self):
        bear, enemy = ArmorRage(bonus=3), actor()
        self.assertEqual(bear.attack_bonus(actor(shield=2), enemy), 3)
        self.assertEqual(bear.attack_bonus(actor(shield=0), enemy), 0)

    def test_spider_bonus_only_if_faster(self):
        spider = SpeedStrike(bonus=2)
        self.assertEqual(spider.attack_bonus(actor(speed=1), actor(speed=4)), 2)
        self.assertEqual(spider.attack_bonus(actor(speed=4), actor(speed=4)), 0)

    def test_bat_heals_every_second_hit(self):
        bat_ability, hero = Regeneration(every=2, amount=1), actor()
        bat = actor(hp=6)
        bat.stats.hp = 3
        self.assertEqual(bat_ability.on_hero_hit(hero, bat), [])
        effects = bat_ability.on_hero_hit(hero, bat)
        self.assertEqual(len(effects), 1)
        self.assertEqual(bat.stats.hp, 4)

    def test_bat_does_not_heal_dead_or_full(self):
        ability, hero = Regeneration(every=1), actor()
        full = actor(hp=6)
        self.assertEqual(ability.on_hero_hit(hero, full), [])
        dead = actor(hp=6)
        dead.stats.hp = 0
        self.assertEqual(ability.on_hero_hit(hero, dead), [])

    def test_create_ability(self):
        self.assertIsInstance(create_ability(None), Ability)
        self.assertIsInstance(create_ability({"type": "armor_rage", "bonus": 4}), ArmorRage)
        with self.assertRaises(ValueError):
            create_ability({"type": "nope"})


if __name__ == "__main__":
    unittest.main()
