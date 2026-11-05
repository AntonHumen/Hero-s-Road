"""Кеш ресурсів: кожне зображення, шрифт і звук завантажується з диска один раз.

Усі функції викликати тільки ПІСЛЯ pygame.display.set_mode (потрібен convert_alpha).
Повернені Surface спільні - перед зміною (наприклад set_alpha) робіть .copy().
"""
from functools import lru_cache

import pygame


@lru_cache(maxsize=None)
def load_image(path, size=None, smooth=False):
    image = pygame.image.load(path).convert_alpha()
    if size is not None:
        scale = pygame.transform.smoothscale if smooth else pygame.transform.scale
        image = scale(image, size)
    return image


@lru_cache(maxsize=None)
def load_font(path, size):
    return pygame.font.Font(path, size)


@lru_cache(maxsize=None)
def load_sound(path, volume=1.0):
    sound = pygame.mixer.Sound(path)
    sound.set_volume(volume)
    return sound
