"""Особливості ворогів. Кожна здібність - окремий клас (замість п'яти копій бою).

Модуль не залежить від pygame: здібності повертають Effect, а відображення
(спливаючі цифри) вирішує код бою.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Effect:
    target: str  # "hero" | "enemy"
    stat: str    # "hp" | "shield" | "attack"
    amount: int
    kind: str    # "damage" | "heal" | "buff" | "debuff"


class Ability:
    """Базова здібність: нічого не змінює (наприклад, Лицар)."""

    def attack_bonus(self, hero, enemy):
        """Додаткова атака ворога в поточний момент."""
        return 0

    def on_hero_hit(self, hero, enemy):
        """Викликається після удару героя. Повертає список Effect."""
        return []


class LowHpRage(Ability):
    """Вовк: +bonus до атаки, якщо у героя hp <= hp_threshold."""

    def __init__(self, hp_threshold=5, bonus=2):
        self.hp_threshold = hp_threshold
        self.bonus = bonus

    def attack_bonus(self, hero, enemy):
        return self.bonus if hero.stats.hp <= self.hp_threshold else 0


class ArmorRage(Ability):
    """Ведмідь: +bonus до атаки, поки у героя є броня."""

    def __init__(self, bonus=3):
        self.bonus = bonus

    def attack_bonus(self, hero, enemy):
        return self.bonus if hero.stats.shield > 0 else 0


class SpeedStrike(Ability):
    """Павук: +bonus до атаки, якщо він швидший за героя."""

    def __init__(self, bonus=2):
        self.bonus = bonus

    def attack_bonus(self, hero, enemy):
        return self.bonus if enemy.stats.speed > hero.stats.speed else 0


class Regeneration(Ability):
    """Кажан: відновлює amount hp кожен every-й удар героя."""

    def __init__(self, every=2, amount=1):
        self.every = every
        self.amount = amount
        self.hits = 0

    def on_hero_hit(self, hero, enemy):
        stats = enemy.stats
        if not stats.is_alive() or stats.hp >= stats.max_hp:
            return []
        self.hits += 1
        if self.hits % self.every == 0:
            healed = stats.heal(self.amount)
            if healed:
                return [Effect("enemy", "hp", healed, "heal")]
        return []


ABILITIES = {
    "low_hp_rage": LowHpRage,
    "armor_rage": ArmorRage,
    "speed_strike": SpeedStrike,
    "regeneration": Regeneration,
}


def create_ability(spec):
    """Створює здібність зі словника {"type": ..., параметри...}. None -> без здібності."""
    if not spec:
        return Ability()
    params = dict(spec)
    kind = params.pop("type", None)
    if kind not in ABILITIES:
        raise ValueError(f"Невідома здібність: {kind!r}")
    return ABILITIES[kind](**params)
