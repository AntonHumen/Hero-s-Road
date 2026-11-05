"""Характеристики персонажа. Модуль не залежить від pygame, тому легко тестується."""


class Stats:
    def __init__(self, hp, shield, attack, speed):
        self.max_hp = hp
        self.hp = hp
        self.max_shield = shield
        self.shield = shield
        self.attack = attack
        self.speed = speed

    def take_damage(self, amount):
        """Спочатку знімає броню, залишок іде в здоров'я.

        Повертає (шкода броні, шкода здоров'ю).
        """
        amount = max(0, amount)
        damage_to_shield = min(self.shield, amount)
        self.shield -= damage_to_shield
        damage_to_hp = amount - damage_to_shield
        if damage_to_hp > 0:
            self.hp = max(0, self.hp - damage_to_hp)
        return damage_to_shield, damage_to_hp

    def heal(self, amount):
        """Лікує, не перевищуючи max_hp. Повертає фактично відновлене значення."""
        before = self.hp
        self.hp = min(self.max_hp, self.hp + max(0, amount))
        return self.hp - before

    def is_alive(self):
        return self.hp > 0

    def restore_shield(self):
        self.shield = self.max_shield
