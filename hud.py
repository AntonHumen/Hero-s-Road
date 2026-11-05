"""Спільні функції малювання: HUD, підказки предметів, спливаючі цифри."""
import pygame

from assets import load_font, load_image
from config import HEIGHT, WIDTH

PIXEL_FONT = "8bit2.ttf"
_ICON_FILES = {"hp": "hp", "attack": "atack", "shield": "shield", "speed": "speed"}


def hud_font():
    return load_font("8bit.ttf", 36)


def stat_icon(stat, size=(60, 60), smooth=False):
    return load_image(f"photo/characteristics/{_ICON_FILES[stat]}.png", size, smooth)


def draw_icon_with_value(surface, icon, value, pos, font, color=(255, 255, 255), padding=10):
    x, y = pos
    surface.blit(icon, (x, y))
    text = font.render(str(value), True, color)
    surface.blit(text, (x + icon.get_width() + padding, y + (icon.get_height() - text.get_height()) // 2))


def draw_icon_with_value_mirrored(surface, icon, value, pos, font, color=(255, 255, 255), padding=10):
    x, y = pos
    text = font.render(str(value), True, color)
    surface.blit(text, (x - text.get_width() - padding, y + (icon.get_height() - text.get_height()) // 2))
    surface.blit(icon, (x, y))


def draw_wrapped_text(surface, text, font, color, rect, line_height):
    lines, current = [], ""
    for word in text.split(" "):
        candidate = current + word + " "
        if font.size(candidate)[0] <= rect.width:
            current = candidate
        else:
            lines.append(current)
            current = word + " "
    lines.append(current)
    y = rect.top
    for line in lines:
        surface.blit(font.render(line.strip(), True, color), (rect.left, y))
        y += line_height


def draw_item_stats(surface, item):
    """Підказка біля курсора: бонуси предмета та опис."""
    if item is None or item.is_empty:
        return

    value_font = load_font(PIXEL_FONT, 32)
    desc_font = load_font(PIXEL_FONT, 20)
    icon_size = (32, 32)

    stats = [(stat_icon(stat, icon_size, smooth=True), value)
             for stat, value in (("hp", item.hp_mod), ("shield", item.shield_mod),
                                 ("attack", item.attack_mod), ("speed", item.speed_mod))
             if value != 0]

    padding, spacing = 8, 6
    stat_height = len(stats) * (icon_size[1] + spacing) - spacing if stats else 0
    stat_width = icon_size[0] + 8 + max((value_font.size(f"{v:+d}")[0] for _, v in stats), default=0)

    desc_surfs = [desc_font.render(line, True, (255, 255, 255))
                  for line in item.description.split("\n")] if item.description else []
    desc_width = max((s.get_width() for s in desc_surfs), default=0)
    desc_height = sum(s.get_height() for s in desc_surfs) + max(0, len(desc_surfs) - 1) * 2

    width = max(stat_width, desc_width) + padding * 2
    height = stat_height + (padding * 2 if stats else 0) + (desc_height + padding if desc_surfs else 0)

    mx, my = pygame.mouse.get_pos()
    rect = pygame.Rect(min(mx + 20, WIDTH - width), min(my + 20, HEIGHT - height), width, height)

    background = pygame.Surface((width, height), pygame.SRCALPHA)
    background.fill((40, 40, 40, 230))
    surface.blit(background, rect.topleft)
    pygame.draw.rect(surface, (255, 215, 0), rect, 2)

    y = rect.y + padding
    for icon, value in stats:
        surface.blit(icon, (rect.x + padding, y))
        text = value_font.render(f"{value:+d}", True, (255, 255, 255))
        surface.blit(text, (rect.x + padding + icon_size[0] + 8, y + (icon_size[1] - text.get_height()) // 2))
        y += icon_size[1] + spacing

    if desc_surfs:
        if stats:
            y += padding // 2
        for surf in desc_surfs:
            surface.blit(surf, (rect.x + padding, y))
            y += surf.get_height() + 2


def draw_hud(surface, hero, inventory):
    """Ліва панель: характеристики героя та інвентар."""
    lines = load_image("photo/menu_lines.png", (1550, 871))
    surface.blit(lines, (WIDTH // 2 - lines.get_width() // 2, HEIGHT // 2 - lines.get_height() // 2))

    font = hud_font()
    s = hero.stats
    for stat, value, y in (("hp", s.hp, 125), ("attack", s.attack, 190),
                           ("shield", s.shield, 252), ("speed", s.speed, 315)):
        draw_icon_with_value(surface, stat_icon(stat), value, (220, y), font)

    inventory.draw(surface)
    draw_item_stats(surface, inventory.item_at(pygame.mouse.get_pos()))


class DamagePopup:
    """Цифра зі значком, що спливає вгору та згасає."""
    COLORS = {"damage": ((255, 0, 0), "-"), "heal": ((0, 255, 0), "+"),
              "buff": ((255, 165, 0), "+"), "debuff": ((255, 165, 0), "-")}

    def __init__(self, amount, icon, pos, font, kind="damage"):
        self.amount = amount
        self.icon = icon
        self.x, self.y = pos
        self.font = font
        self.kind = kind
        self.start_time = pygame.time.get_ticks()
        self.duration = 1000
        self.alpha = 255
        self.offset_y = 0

    def update(self):
        elapsed = pygame.time.get_ticks() - self.start_time
        if elapsed > self.duration:
            return False
        self.offset_y = -(elapsed / self.duration) * 30
        self.alpha = 255 * (1 - elapsed / self.duration)
        return True

    def draw(self, surface):
        color, sign = self.COLORS[self.kind]
        text = self.font.render(f"{sign}{abs(self.amount)}", True, color)
        text.set_alpha(self.alpha)
        icon = self.icon.copy()
        icon.set_alpha(self.alpha)
        surface.blit(icon, (self.x, self.y + self.offset_y))
        surface.blit(text, (self.x + self.icon.get_width() + 5, self.y + self.offset_y))
