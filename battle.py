"""Покроковий бій. Один клас замінює wolf_menu / bear_menu / beat_menu / spider_menu / knight.

Особливості ворогів живуть у abilities.py і задаються в data/enemies.json.
"""
import pygame

import hud
from abilities import Effect
from assets import load_font, load_image, load_sound
from button import ImageButton2
from config import HEIGHT, WIDTH, quit_game
from hud import DamagePopup

HERO_POS = (600, 400)
ENEMY_POS = (HERO_POS[0] + 500, HERO_POS[1])
SPRITE_SIZE = (200, 200)

ACTION_COOLDOWN = 1000     # мс між ударами
ANIM_DURATION = 300        # мс анімації удару
ANIM_DISTANCE = 20         # пікселів "кидка" вперед
ENEMY_FADE_SPEED = 5
VICTORY_FADE_SPEED = 3
SHIELD_ANIM_SPEED = 0.5
STAT_LINE_SPACING = 65

POPUP_ANCHOR = {"hero": (HERO_POS[0] + 50, HERO_POS[1]),
                "enemy": (ENEMY_POS[0] + 90, ENEMY_POS[1])}


def approach(current, target, step):
    """Наближає current до target не більше ніж на step."""
    if current < target:
        return min(current + step, target)
    if current > target:
        return max(current - step, target)
    return current


class Battle:
    """Результат run(): "victory" або "defeat"."""

    def __init__(self, hero, inventory, enemy):
        self.screen = pygame.display.get_surface()
        self.hero = hero
        self.inventory = inventory
        self.enemy = enemy
        self.ability = enemy.ability

        self.font = hud.hud_font()
        self.desc_font = load_font(hud.PIXEL_FONT, 32)
        self.hero_sprite = load_image("photo/hero.png", SPRITE_SIZE)
        self.enemy_sprite = load_image(enemy.image_path, SPRITE_SIZE)
        self.hit_sound = load_sound("audio/udar-nojom-po-vozduhu.mp3", 0.3)
        self.victory_sound = load_sound("audio/victory.mp3", 0.3)

        self.pause_button = ImageButton2(
            x=750, y=150, width=252, height=80, text="",
            image_path="photo/pau_con/pause.png",
            hover_image_path="photo/pau_con/pause2.png",
            pressed_image_path="photo/pau_con/pause3.png",
            sound_path="audio/button.wav")
        self.continue_button = ImageButton2(
            x=950, y=150, width=252, height=80, text="",
            image_path="photo/pau_con/continue.png",
            hover_image_path="photo/pau_con/continue2.png",
            pressed_image_path="photo/pau_con/continue3.png",
            sound_path="audio/button.wav")
        self.buttons = [self.pause_button, self.continue_button]

        self.turn = "hero" if hero.stats.speed >= enemy.stats.speed else "enemy"
        self.paused = True
        self.pause_button.set_pressed(True)
        self.animating = False
        self.anim_start = 0
        self.offset = 0
        self.last_action = pygame.time.get_ticks()

        self.popups = []
        self._popup_levels = {"hero": 0, "enemy": 0}
        self.bonus = 0  # поточний бонус атаки ворога від здібності

        self.enemy_alpha = 255
        self.victory_alpha = 0
        self.victory_sound_played = False
        self.shield_hero = float(hero.stats.shield)
        self.shield_enemy = float(enemy.stats.shield)

        self.running = True
        self.result = "victory"

    @property
    def is_over(self):
        return not self.hero.stats.is_alive() or not self.enemy.stats.is_alive()

    # ---------- головний цикл ----------

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            now = pygame.time.get_ticks()
            self._handle_events(now)
            self._update(now)
            if self.running:
                self._draw()
                pygame.display.flip()
            clock.tick(60)
        return self.result

    # ---------- події ----------

    def _handle_events(self, now):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_game()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and self.is_over:
                if not self.enemy.stats.is_alive():
                    self.hero.stats.restore_shield()
                self.running = False

            for button in self.buttons:
                button.handle_event(event)

            if event.type == pygame.USEREVENT:
                clicked = getattr(event, "button", None)
                for button in self.buttons:
                    button.set_pressed(button is clicked)
                if clicked is self.pause_button:
                    self.paused = True
                elif clicked is self.continue_button:
                    self.paused = False
                    self.last_action = now
                    self.animating = False

        mouse = pygame.mouse.get_pos()
        for button in self.buttons:
            button.check_hover(mouse)

    # ---------- логіка ----------

    def _update(self, now):
        if self.paused:
            self.offset = 0
        else:
            self._update_bonus()
            self._update_turn(now)

        self.shield_hero = approach(self.shield_hero, self.hero.stats.shield, SHIELD_ANIM_SPEED)
        self.shield_enemy = approach(self.shield_enemy, self.enemy.stats.shield, SHIELD_ANIM_SPEED)
        self._update_outcome()

    def _update_bonus(self):
        """Стежить за бонусом атаки ворога й показує спливаючий +/-."""
        bonus = self.ability.attack_bonus(self.hero, self.enemy)
        if bonus > self.bonus:
            self._emit(Effect("enemy", "attack", bonus - self.bonus, "buff"), level=2)
        elif bonus < self.bonus:
            self._emit(Effect("enemy", "attack", self.bonus - bonus, "debuff"), level=2)
        self.bonus = bonus

    def _update_turn(self, now):
        if self.animating:
            elapsed = now - self.anim_start
            if elapsed < ANIM_DURATION:
                progress = elapsed / ANIM_DURATION
                half = progress / 0.5 if progress < 0.5 else 1 - (progress - 0.5) / 0.5
                self.offset = int(ANIM_DISTANCE * half)
            else:
                self.animating = False
                self.offset = 0
                self.hit_sound.play()
                self._resolve_attack(now)
        else:
            self.offset = 0
            if now - self.last_action > ACTION_COOLDOWN and not self.is_over:
                self.animating = True
                self.anim_start = now

    def _resolve_attack(self, now):
        self._popup_levels = {"hero": 0, "enemy": 0}
        if self.turn == "hero":
            self._hero_attacks()
            self.turn = "enemy"
        else:
            self._enemy_attacks()
            self.turn = "hero"
        self.last_action = now

    def _hero_attacks(self):
        to_shield, to_hp = self.enemy.stats.take_damage(self.hero.stats.attack)
        if to_shield:
            self._emit(Effect("enemy", "shield", to_shield, "damage"))
        if to_hp:
            self._emit(Effect("enemy", "hp", to_hp, "damage"))

        lifesteal = self.inventory.weapon.lifesteal
        if lifesteal:
            healed = self.hero.stats.heal(lifesteal)
            if healed:
                self._emit(Effect("hero", "hp", healed, "heal"))

        for effect in self.ability.on_hero_hit(self.hero, self.enemy):
            self._emit(effect)

    def _enemy_attacks(self):
        damage = self.enemy.stats.attack + self.ability.attack_bonus(self.hero, self.enemy)
        to_shield, to_hp = self.hero.stats.take_damage(damage)
        if to_shield:
            self._emit(Effect("hero", "shield", to_shield, "damage"))
        if to_hp:
            self._emit(Effect("hero", "hp", to_hp, "damage"))

    def _emit(self, effect, level=None):
        """Створює спливаючу цифру; кілька цифр одного удару ставляться стовпчиком."""
        if level is None:
            level = self._popup_levels[effect.target]
            self._popup_levels[effect.target] += 1
        x, y = POPUP_ANCHOR[effect.target]
        self.popups.append(DamagePopup(effect.amount, hud.stat_icon(effect.stat),
                                       (x, y - 100 - 30 * level), self.font, effect.kind))

    def _update_outcome(self):
        if not self.enemy.stats.is_alive():
            self.enemy_alpha = max(0, self.enemy_alpha - ENEMY_FADE_SPEED)
            if self.enemy_alpha == 0:
                self.hero.stats.restore_shield()
                if self.victory_alpha < 255:
                    if not self.victory_sound_played:
                        self.victory_sound.play()
                        self.victory_sound_played = True
                    self.victory_alpha = min(255, self.victory_alpha + VICTORY_FADE_SPEED)
        if not self.hero.stats.is_alive():
            self.result = "defeat"
            self.running = False

    # ---------- малювання ----------

    def _draw(self):
        screen = self.screen
        screen.fill((30, 30, 30))
        lines = load_image("photo/menu_lines2.png", (1550, 871))
        screen.blit(lines, (WIDTH // 2 - lines.get_width() // 2, HEIGHT // 2 - lines.get_height() // 2))

        hero_dx = self.offset if self.turn == "hero" and self.animating else 0
        enemy_dx = -self.offset if self.turn == "enemy" and self.animating else 0
        screen.blit(self.hero_sprite, (HERO_POS[0] + hero_dx, HERO_POS[1]))

        sprite = self.enemy_sprite
        if self.enemy_alpha < 255:
            sprite = sprite.copy()
            sprite.set_alpha(self.enemy_alpha)
        screen.blit(sprite, (ENEMY_POS[0] + enemy_dx, ENEMY_POS[1]))

        self._draw_stats()
        hud.draw_wrapped_text(screen, self.enemy.description, self.desc_font, (180, 180, 180),
                              pygame.Rect(WIDTH - 470, 420, 280, 100), 32)

        if self.victory_alpha > 0:
            text = self.font.render("Victory!", True, (0, 255, 0))
            text.set_alpha(self.victory_alpha)
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2,
                               HEIGHT // 2 - text.get_height() // 2 - 100))

        for popup in self.popups[:]:
            if popup.update():
                popup.draw(screen)
            else:
                self.popups.remove(popup)

        for button in self.buttons:
            button.draw(screen)

        self.inventory.draw(screen)
        hud.draw_item_stats(screen, self.inventory.item_at(pygame.mouse.get_pos()))

    def _draw_stats(self):
        top = HERO_POS[1] + 200 + 10
        hero, enemy = self.hero.stats, self.enemy.stats
        hero_rows = (("hp", hero.hp), ("attack", hero.attack),
                     ("shield", int(self.shield_hero)), ("speed", hero.speed))
        enemy_rows = (("hp", enemy.hp), ("attack", enemy.attack + self.bonus),
                      ("shield", int(self.shield_enemy)), ("speed", enemy.speed))
        for i, (stat, value) in enumerate(hero_rows):
            hud.draw_icon_with_value(self.screen, hud.stat_icon(stat), value,
                                     (HERO_POS[0], top + i * STAT_LINE_SPACING), self.font)
        for i, (stat, value) in enumerate(enemy_rows):
            hud.draw_icon_with_value_mirrored(self.screen, hud.stat_icon(stat), value,
                                              (HERO_POS[0] + 640, top + i * STAT_LINE_SPACING), self.font)
