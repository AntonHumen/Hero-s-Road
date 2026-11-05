import pygame

from abilities import create_ability
from assets import load_image
from stats import Stats

ITEM_SIZE = (100, 100)


class Hero:
    def __init__(self, image_path, pos, tile_size=64, scale=1.0):
        size = int(tile_size * scale)
        self.image = load_image(image_path, (size, size))
        self.rect = self.image.get_rect(topleft=pos)

        self.move_cooldown = 200
        self.last_move_time = pygame.time.get_ticks()
        self.tile_size = tile_size
        self.move_dir = None

        self.walk_sound = pygame.mixer.Sound("audio/hotba.mp3")
        self.walk_sound.set_volume(0.1)

        self.stats = Stats(hp=10, shield=0, attack=0, speed=0)

    @property
    def tile_pos(self):
        return self.rect.centerx // self.tile_size, self.rect.centery // self.tile_size

    def can_move_to(self, dx, dy, map_data, walkable_tiles):
        tile_x = (self.rect.x + dx) // self.tile_size
        tile_y = (self.rect.y + dy) // self.tile_size
        if 0 <= tile_y < len(map_data) and 0 <= tile_x < len(map_data[0]):
            return map_data[tile_y][tile_x] in walkable_tiles
        return False

    def move(self, dx, dy):
        now = pygame.time.get_ticks()
        if now - self.last_move_time >= self.move_cooldown:
            self.rect.x += dx
            self.rect.y += dy
            self.last_move_time = now
            self.walk_sound.stop()
            self.walk_sound.play()

    def handle_input(self, keys, map_data, walkable_tiles):
        ts = self.tile_size
        directions = (
            (pygame.K_w, 0, -ts, "up"),
            (pygame.K_s, 0, ts, "down"),
            (pygame.K_a, -ts, 0, "left"),
            (pygame.K_d, ts, 0, "right"),
        )
        self.move_dir = None
        for key, dx, dy, name in directions:
            if keys[key] and self.can_move_to(dx, dy, map_data, walkable_tiles):
                self.move(dx, dy)
                self.move_dir = name
                break

    def draw(self, surface, offset=(0, 0)):
        surface.blit(self.image, (self.rect.x + offset[0], self.rect.y + offset[1]))


class Enemy:
    def __init__(self, name, hp, shield, attack, speed, image_path,
                 ability=None, description=""):
        self.name = name
        self.stats = Stats(hp, shield, attack, speed)
        self.image_path = image_path
        self.ability = ability if ability is not None else create_ability(None)
        self.description = description

    @classmethod
    def from_data(cls, d):
        """Створює ворога зі словника, провалідованого у gamedata."""
        return cls(d["name"], d["hp"], d["shield"], d["attack"], d["speed"],
                   d["image"], create_ability(d["ability"]), d["description"])


class Item:
    is_empty = False

    def __init__(self, image_path, border_image_path=None, hp=0, shield=0, attack=0,
                 speed=0, item_size=ITEM_SIZE, border_size=None, description="",
                 item_type="item", lifesteal=0, item_id=None):
        self.id = item_id
        self.image = load_image(image_path, item_size, smooth=True)
        self.border_image = None
        if border_image_path:
            self.border_image = load_image(border_image_path, border_size or item_size, smooth=True)

        self.hp_mod = hp
        self.shield_mod = shield
        self.attack_mod = attack
        self.speed_mod = speed
        self.lifesteal = lifesteal  # скільки hp відновлює власник при кожному ударі
        self.description = description
        self.type = item_type

    @classmethod
    def from_data(cls, d):
        return cls(d["image"], d["border"] or None, hp=d["hp"], shield=d["shield"],
                   attack=d["attack"], speed=d["speed"], description=d["description"],
                   item_type=d["type"], lifesteal=d["lifesteal"], item_id=d["id"])

    def apply_effect(self, target):
        s = target.stats
        s.max_hp += self.hp_mod
        s.hp += self.hp_mod
        s.max_shield += self.shield_mod
        s.shield += self.shield_mod
        s.attack += self.attack_mod
        s.speed += self.speed_mod

    def remove_effect(self, target):
        s = target.stats
        s.max_hp -= self.hp_mod
        s.hp = min(s.hp, s.max_hp)
        s.max_shield -= self.shield_mod
        s.shield = min(s.shield, s.max_shield)
        s.attack -= self.attack_mod
        s.speed -= self.speed_mod

    def draw(self, surface, pos, selected=False):
        x, y = pos
        surface.blit(self.image, (x, y))
        if selected and self.border_image:
            surface.blit(self.border_image, (
                x - (self.border_image.get_width() - self.image.get_width()) // 2,
                y - (self.border_image.get_height() - self.image.get_height()) // 2))


class EmptyItem:
    """Порожній слот інвентарю (Null Object): усі методи безпечні."""
    is_empty = True
    id = None
    type = "empty"
    image = None
    description = ""
    hp_mod = shield_mod = attack_mod = speed_mod = lifesteal = 0

    def apply_effect(self, target):
        pass

    def remove_effect(self, target):
        pass

    def draw(self, surface, pos, selected=False):
        pass
