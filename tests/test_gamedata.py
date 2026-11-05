import unittest

import gamedata
from gamedata import DataError


def item(**kw):
    base = {"id": "a", "image": "a.png", "type": "weapon", "start": True}
    base.update(kw)
    return base


def enemy(**kw):
    base = {"id": "e", "name": "E", "image": "e.png", "tile": 16, "replace_tile": 5,
            "hp": 3, "shield": 0, "attack": 1, "speed": 1}
    base.update(kw)
    return base


class GameDataTests(unittest.TestCase):
    def test_real_data_files_are_valid(self):
        items = gamedata.load_items()
        enemies = gamedata.load_enemies()
        self.assertEqual(sum(i["start"] for i in items), 1)
        self.assertEqual(set(enemies), {16, 17, 20, 21, 22})

    def test_missing_file(self):
        with self.assertRaises(DataError):
            gamedata.load_items("data/no_such_file.json")

    def test_missing_required_field(self):
        raw = item()
        del raw["image"]
        with self.assertRaises(DataError):
            gamedata.parse_items([raw])

    def test_stat_must_be_integer(self):
        with self.assertRaises(DataError):
            gamedata.parse_items([item(attack="3")])
        with self.assertRaises(DataError):
            gamedata.parse_items([item(attack=True)])

    def test_unknown_item_type(self):
        with self.assertRaises(DataError):
            gamedata.parse_items([item(type="hat")])

    def test_duplicate_item_id(self):
        with self.assertRaises(DataError):
            gamedata.parse_items([item(), item()])

    def test_exactly_one_start_item(self):
        with self.assertRaises(DataError):
            gamedata.parse_items([item(start=False)])

    def test_enemy_validation(self):
        self.assertIn(16, gamedata.parse_enemies([enemy()]))
        with self.assertRaises(DataError):
            gamedata.parse_enemies([enemy(hp=0)])
        with self.assertRaises(DataError):
            gamedata.parse_enemies([enemy(ability={"type": "nope"})])
        with self.assertRaises(DataError):
            gamedata.parse_enemies([enemy(), enemy(id="e2")])


if __name__ == "__main__":
    unittest.main()
