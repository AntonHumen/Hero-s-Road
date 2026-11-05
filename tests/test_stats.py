import unittest

from stats import Stats


class StatsTests(unittest.TestCase):
    def test_damage_goes_to_shield_first(self):
        s = Stats(hp=10, shield=3, attack=0, speed=0)
        self.assertEqual(s.take_damage(2), (2, 0))
        self.assertEqual((s.shield, s.hp), (1, 10))

    def test_overflow_damage_hits_hp(self):
        s = Stats(hp=10, shield=3, attack=0, speed=0)
        self.assertEqual(s.take_damage(5), (3, 2))
        self.assertEqual((s.shield, s.hp), (0, 8))

    def test_hp_never_negative_and_death(self):
        s = Stats(hp=2, shield=0, attack=0, speed=0)
        s.take_damage(99)
        self.assertEqual(s.hp, 0)
        self.assertFalse(s.is_alive())

    def test_negative_damage_is_ignored(self):
        s = Stats(hp=5, shield=1, attack=0, speed=0)
        self.assertEqual(s.take_damage(-4), (0, 0))
        self.assertEqual((s.hp, s.shield), (5, 1))

    def test_heal_is_capped_by_max_hp(self):
        s = Stats(hp=10, shield=0, attack=0, speed=0)
        s.take_damage(3)
        self.assertEqual(s.heal(10), 3)
        self.assertEqual(s.hp, 10)

    def test_restore_shield(self):
        s = Stats(hp=5, shield=4, attack=0, speed=0)
        s.take_damage(4)
        s.restore_shield()
        self.assertEqual(s.shield, 4)


if __name__ == "__main__":
    unittest.main()
