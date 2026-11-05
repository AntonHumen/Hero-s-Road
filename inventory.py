import pygame

from assets import load_image
from character import EmptyItem

SLOT_POSITIONS = [(295, 410), (220, 550), (360, 550), (220, 680), (360, 680)]
SLOT_SIZE = (100, 100)
WEAPON_SLOT = 0


class Inventory:
    """5 слотів: слот 0 - зброя, слоти 1-4 - звичайні предмети."""

    def __init__(self):
        self.slots = [EmptyItem() for _ in SLOT_POSITIONS]
        self.selected = 0

    @property
    def weapon(self):
        return self.slots[WEAPON_SLOT]

    @staticmethod
    def can_equip(index, item):
        """Зброя - лише у слот 0, усе інше - лише у слоти 1-4."""
        return (item.type == "weapon") == (index == WEAPON_SLOT)

    def equip(self, index, item, hero):
        self.slots[index].remove_effect(hero)
        self.slots[index] = item
        item.apply_effect(hero)
        self.selected = index

    def cycle(self):
        self.selected = (self.selected + 1) % len(self.slots)

    def slot_at(self, pos, item):
        """Індекс слота під курсором, у який можна покласти item (або None)."""
        for index, slot_pos in enumerate(SLOT_POSITIONS):
            if pygame.Rect(slot_pos, SLOT_SIZE).collidepoint(pos) and self.can_equip(index, item):
                return index
        return None

    def item_at(self, pos):
        """Непорожній предмет під курсором (для підказки) або None."""
        for item, slot_pos in zip(self.slots, SLOT_POSITIONS):
            if not item.is_empty and pygame.Rect(slot_pos, SLOT_SIZE).collidepoint(pos):
                return item
        return None

    def draw(self, surface):
        backgrounds = ["weapon_slot"] + [f"{n}slot" for n in range(1, 5)]
        for name, pos in zip(backgrounds, SLOT_POSITIONS):
            surface.blit(load_image(f"photo/slots/{name}.png", SLOT_SIZE), pos)
        for index, (item, pos) in enumerate(zip(self.slots, SLOT_POSITIONS)):
            item.draw(surface, pos, selected=(index == self.selected))
