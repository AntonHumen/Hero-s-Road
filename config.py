"""Глобальні константи та налаштування користувача."""
import json
import sys

import pygame

WIDTH, HEIGHT = 1920, 1080
TILE_SIZE = 64
SETTINGS_PATH = "settings.json"
DEFAULT_SETTINGS = {"volume": 1.0}


def load_settings():
    """Читає settings.json; при будь-якій проблемі повертає значення за замовчуванням."""
    settings = dict(DEFAULT_SETTINGS)
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        volume = float(data.get("volume", settings["volume"]))
        settings["volume"] = min(1.0, max(0.0, volume))
    except (OSError, ValueError, TypeError, AttributeError):
        pass
    return settings


def save_settings(settings):
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(settings, f)
    except OSError as e:
        print(f"Не вдалося зберегти налаштування: {e}")


def quit_game():
    pygame.quit()
    sys.exit()
