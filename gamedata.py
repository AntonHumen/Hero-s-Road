"""Завантаження та валідація ігрових даних (предмети, вороги) з JSON."""
import json

from abilities import ABILITIES

ITEMS_PATH = "data/items.json"
ENEMIES_PATH = "data/enemies.json"

ITEM_TYPES = {"weapon", "item"}
STAT_FIELDS = ("hp", "attack", "shield", "speed")


class DataError(Exception):
    """Помилка у файлі даних (відсутній, пошкоджений або з некоректними значеннями)."""


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def read_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise DataError(f"Файл не знайдено: {path}") from None
    except json.JSONDecodeError as e:
        raise DataError(f"Некоректний JSON у {path}: {e}") from None
    except OSError as e:
        raise DataError(f"Не вдалося прочитати {path}: {e}") from None


def _text(raw, key, where, required=True, default=""):
    if key not in raw:
        if required:
            raise DataError(f"{where}: відсутнє поле '{key}'")
        return default
    if not isinstance(raw[key], str):
        raise DataError(f"{where}: поле '{key}' має бути рядком")
    return raw[key]


def _number(raw, key, where, minimum=None, default=0, required=False):
    if key not in raw:
        if required:
            raise DataError(f"{where}: відсутнє поле '{key}'")
        return default
    value = raw[key]
    if not _is_int(value):
        raise DataError(f"{where}: поле '{key}' має бути цілим числом")
    if minimum is not None and value < minimum:
        raise DataError(f"{where}: поле '{key}' має бути >= {minimum}")
    return value


def validate_item(raw, index=0):
    if not isinstance(raw, dict):
        raise DataError(f"Предмет #{index}: очікувався об'єкт")
    where = f"Предмет '{raw.get('id', index)}'"
    item = {
        "id": _text(raw, "id", where),
        "image": _text(raw, "image", where),
        "border": _text(raw, "border", where, required=False),
        "description": _text(raw, "description", where, required=False),
        "type": _text(raw, "type", where),
        "lifesteal": _number(raw, "lifesteal", where, minimum=0),
        "chest": raw.get("chest", True),
        "start": raw.get("start", False),
    }
    for stat in STAT_FIELDS:
        item[stat] = _number(raw, stat, where)
    if item["type"] not in ITEM_TYPES:
        raise DataError(f"{where}: type має бути одним із {sorted(ITEM_TYPES)}")
    if not isinstance(item["chest"], bool) or not isinstance(item["start"], bool):
        raise DataError(f"{where}: 'chest' і 'start' мають бути true/false")
    return item


def validate_enemy(raw, index=0):
    if not isinstance(raw, dict):
        raise DataError(f"Ворог #{index}: очікувався об'єкт")
    where = f"Ворог '{raw.get('id', index)}'"
    enemy = {
        "id": _text(raw, "id", where),
        "name": _text(raw, "name", where),
        "image": _text(raw, "image", where),
        "description": _text(raw, "description", where, required=False),
        "tile": _number(raw, "tile", where, required=True),
        "replace_tile": _number(raw, "replace_tile", where, required=True),
        "hp": _number(raw, "hp", where, minimum=1, required=True),
        "shield": _number(raw, "shield", where, minimum=0, required=True),
        "attack": _number(raw, "attack", where, minimum=0, required=True),
        "speed": _number(raw, "speed", where, required=True),
        "ability": raw.get("ability"),
    }
    ability = enemy["ability"]
    if ability is not None:
        if not isinstance(ability, dict) or ability.get("type") not in ABILITIES:
            raise DataError(f"{where}: невідома або некоректна здібність {ability!r}")
    return enemy


def parse_items(raw_list):
    if not isinstance(raw_list, list):
        raise DataError("items.json: очікувався список предметів")
    items, seen = [], set()
    for i, raw in enumerate(raw_list):
        item = validate_item(raw, i)
        if item["id"] in seen:
            raise DataError(f"Дублікат id предмета: {item['id']}")
        seen.add(item["id"])
        items.append(item)
    if sum(1 for it in items if it["start"]) != 1:
        raise DataError("Має бути рівно один стартовий предмет (start: true)")
    return items


def parse_enemies(raw_list):
    """Повертає словник {номер_тайла: дані_ворога}."""
    if not isinstance(raw_list, list):
        raise DataError("enemies.json: очікувався список ворогів")
    enemies = {}
    for i, raw in enumerate(raw_list):
        enemy = validate_enemy(raw, i)
        if enemy["tile"] in enemies:
            raise DataError(f"Два вороги з однаковим tile: {enemy['tile']}")
        enemies[enemy["tile"]] = enemy
    return enemies


def load_items(path=ITEMS_PATH):
    return parse_items(read_json(path))


def load_enemies(path=ENEMIES_PATH):
    return parse_enemies(read_json(path))
