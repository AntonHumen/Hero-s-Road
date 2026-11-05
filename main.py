import sys

import pygame

import menus
from config import HEIGHT, WIDTH
from game import Game
from gamedata import DataError, load_enemies, load_items


def main():
    pygame.init()
    pygame.display.set_caption("Game")
    pygame.display.set_mode((WIDTH, HEIGHT))

    try:
        items = load_items()
        enemies = load_enemies()
    except DataError as error:
        print(f"Помилка даних гри: {error}")
        pygame.quit()
        sys.exit(1)

    state = "menu"
    while True:
        if state == "menu":
            if menus.main_menu() == "quit":
                break
            state = "play"
        else:  # "play" або "restart"
            state = Game(items, enemies).run()
    pygame.quit()


if __name__ == "__main__":
    main()
