"""Ігрова сесія: карта, герой, інвентар, взаємодія з тайлами."""
import copy
import random

import pygame

import hud
import level
import menus
from assets import load_image
from battle import Battle
from character import Enemy, Hero, Item
from config import HEIGHT, TILE_SIZE, WIDTH, quit_game
from inventory import Inventory

CHEST_CHOICES = 3


class Game:
    def __init__(self, items, enemies):
        """items - список словників з gamedata.load_items, enemies - {tile: словник}."""
        self.screen = pygame.display.get_surface()
        self.item_data = items
        self.enemy_data = enemies
        self.map = copy.deepcopy(level.MAP_DATA)

        self.tile_paths = dict(level.TILE_IMAGES)
        self.tile_paths.update({tile: data["image"] for tile, data in enemies.items()})
        self.walkable = level.WALKABLE_TILES | set(enemies)

        self.hero = Hero("photo/hero.png", self._spawn_position(), tile_size=TILE_SIZE, scale=1)
        self.inventory = Inventory()
        start = next(d for d in items if d["start"])
        self.inventory.equip(0, Item.from_data(start), self.hero)

    def _spawn_position(self):
        """Герой з'являється під будинком; якщо будинку немає - у (0, 0)."""
        for y, row in enumerate(self.map):
            for x, tile in enumerate(row):
                if tile == level.TILE_HOUSE:
                    return x * TILE_SIZE, (y + 1) * TILE_SIZE
        return 0, 0

    # ---------- малювання ----------

    def _offset(self):
        return WIDTH // 2 - self.hero.rect.centerx, HEIGHT // 2 - self.hero.rect.centery

    def _draw_map(self, offset):
        for y, row in enumerate(self.map):
            for x, tile in enumerate(row):
                px, py = x * TILE_SIZE + offset[0], y * TILE_SIZE + offset[1]
                if -TILE_SIZE < px < WIDTH and -TILE_SIZE < py < HEIGHT:  # лише видимі тайли
                    self.screen.blit(load_image(self.tile_paths[tile]), (px, py))

    def draw_world(self):
        """Карта + герой + HUD. Використовується і як фон для меню."""
        offset = self._offset()
        self.screen.fill((0, 0, 0))
        self._draw_map(offset)
        self.hero.draw(self.screen, offset)
        hud.draw_hud(self.screen, self.hero, self.inventory)

    # ---------- головний цикл ----------

    def run(self):
        """Повертає "menu" (вихід у меню) або "restart" (почати заново)."""
        clock = pygame.time.Clock()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    quit_game()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if menus.pause_menu(self.draw_world) == "menu":
                            return "menu"
                    elif event.key == pygame.K_q:
                        self.inventory.cycle()

            self.hero.handle_input(pygame.key.get_pressed(), self.map, self.walkable)
            self.draw_world()

            outcome = self._handle_tile()
            if outcome:
                return outcome

            pygame.display.flip()
            clock.tick(60)

    # ---------- події на тайлах ----------

    def _handle_tile(self):
        x, y = self.hero.tile_pos
        tile = self.map[y][x]
        if tile in self.enemy_data:
            return self._fight(tile, x, y)
        if tile == level.TILE_CHEST:
            self._open_chest(x, y)
        elif tile == level.TILE_HOUSE_FINAL:
            return menus.end_screen("Ви пройшли гру!", (255, 255, 255),
                                    ["Натисніть ESC, щоб вийти"], "audio/zvuk-vyiigryisha.mp3",
                                    background=self.draw_world, title_size=72, click_closes=True)
        return None

    def _fight(self, tile, x, y):
        data = self.enemy_data[tile]
        result = Battle(self.hero, self.inventory, Enemy.from_data(data)).run()
        if result == "defeat":
            return menus.end_screen("Ви програли!", (255, 0, 0),
                                    ["Натисніть ESC, щоб вийти", "Натисніть R, щоб почати заново"],
                                    "audio/opoveschenie-o-proigryishe.mp3", allow_restart=True)
        self.map[y][x] = data["replace_tile"]
        if not self._enemies_left():
            self._unlock_house()
        return None

    def _enemies_left(self):
        return any(tile in self.enemy_data for row in self.map for tile in row)

    def _unlock_house(self):
        """Після перемоги над усіма ворогами будинок стає фінальним."""
        self.map = [[level.TILE_HOUSE_FINAL if t == level.TILE_HOUSE else t for t in row]
                    for row in self.map]

    def _open_chest(self, x, y):
        pool = [d for d in self.item_data if d["chest"]]
        choices = [Item.from_data(d) for d in random.sample(pool, k=min(CHEST_CHOICES, len(pool)))]
        menus.chest_menu(self.hero, self.inventory, choices, self.draw_world)
        self.map[y][x] = level.TILE_CHEST_OPEN
