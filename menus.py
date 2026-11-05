"""Усі меню та екрани: головне, налаштування, пауза, скриня, кінець гри."""
import pygame

import hud
from assets import load_font, load_image, load_sound
from button import ImageButton
from config import HEIGHT, WIDTH, load_settings, quit_game, save_settings


def _screen():
    return pygame.display.get_surface()


def _menu_button(name, y, width=352):
    return ImageButton(
        x=WIDTH // 2 - width // 2, y=y, width=width, height=80, text="",
        image_path=f"photo/{name}.png",
        hover_image_left_path="photo/right_play.png", hover_left_size=(64, 64),
        hover_image_right_path="photo/left_play.png", hover_right_size=(64, 64),
        sound_path="audio/button.wav")


def _menu_background():
    _screen().blit(load_image("photo/menu.png", (WIDTH, HEIGHT)), (0, 0))


def run_menu(buttons, actions, draw_background, escape=None, draw_extra=None, event_hook=None):
    """Універсальний цикл меню.

    actions: {кнопка: функція}; цикл завершується, коли функція (або escape)
    повертає не None - це значення й повертається.
    """
    screen = _screen()
    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_game()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and escape:
                result = escape()
                if result is not None:
                    return result
            if event_hook:
                event_hook(event)
            if event.type == pygame.USEREVENT:
                action = actions.get(getattr(event, "button", None))
                if action:
                    result = action()
                    if result is not None:
                        return result
            for button in buttons:
                button.handle_event(event)

        draw_background()
        if draw_extra:
            draw_extra()
        mouse = pygame.mouse.get_pos()
        for button in buttons:
            button.check_hover(mouse)
            button.draw(screen)
        pygame.display.flip()
        clock.tick(60)


def main_menu():
    """Повертає "play" або "quit"."""
    play = _menu_button("play", 300, 252)
    settings = _menu_button("settings", 450)
    quit_button = _menu_button("quite", 600)

    pygame.mixer.music.set_volume(load_settings()["volume"])
    pygame.mixer.music.load("audio/menu.mp3")
    pygame.mixer.music.play(-1)

    return run_menu(
        [play, settings, quit_button],
        {play: lambda: "play", settings: settings_menu, quit_button: lambda: "quit"},
        _menu_background)


def settings_menu():
    audio = _menu_button("audio", 300, 252)
    back = _menu_button("back", 700, 252)
    run_menu([audio, back], {audio: audio_menu, back: lambda: "back"},
             _menu_background, escape=lambda: "back")


class VolumeSlider:
    def __init__(self, x, y, width, height, knob_image, initial_volume=1.0):
        self.rect = pygame.Rect(x, y, width, height)
        self.knob_image = knob_image
        self.knob_width, self.knob_height = knob_image.get_size()
        self.volume = initial_volume
        self.knob_x = x + int(width * self.volume)
        self.dragging = False
        pygame.mixer.music.set_volume(self.volume)

    def _knob_rect(self):
        return pygame.Rect(self.knob_x - self.knob_width // 2,
                           self.rect.centery - self.knob_height // 2,
                           self.knob_width, self.knob_height)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self._knob_rect().collidepoint(event.pos):
            self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP and self.dragging:
            self.dragging = False
            save_settings({"volume": self.volume})  # пишемо файл один раз, а не на кожен рух миші
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.knob_x = max(self.rect.left, min(event.pos[0], self.rect.right))
            self.volume = (self.knob_x - self.rect.left) / self.rect.width
            pygame.mixer.music.set_volume(self.volume)

    def draw(self, surface):
        pygame.draw.rect(surface, (180, 180, 180), self.rect)
        fill = pygame.Rect(self.rect.left, self.rect.top, self.knob_x - self.rect.left, self.rect.height)
        pygame.draw.rect(surface, (255, 255, 255), fill)
        surface.blit(self.knob_image, (self.knob_x - self.knob_width // 2,
                                       self.rect.centery - self.knob_height // 2))


def audio_menu():
    screen = _screen()
    slider = VolumeSlider(1100, 400, 300, 30, load_image("photo/audio_pov.png", (192, 192)),
                          initial_volume=load_settings()["volume"])
    music_icon = load_image("photo/music.png", (500, 500))
    back = _menu_button("back", 700, 252)

    def draw_extra():
        screen.blit(music_icon, (500, 255))
        slider.draw(screen)

    run_menu([back], {back: lambda: "back"}, _menu_background, escape=lambda: "back",
             draw_extra=draw_extra, event_hook=slider.handle_event)


def pause_menu(draw_world):
    """Повертає "continue" або "menu". draw_world малює гру під напівпрозорим фоном."""
    screen = _screen()
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(120)
    title = load_font(hud.PIXEL_FONT, 48).render("Пауза", True, (255, 255, 255))

    def draw_background():
        draw_world()
        screen.blit(overlay, (0, 0))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 150))

    resume = _menu_button("continue", 300)
    settings = _menu_button("settings", 450)
    leave = _menu_button("exit", 600)
    return run_menu([resume, settings, leave],
                    {resume: lambda: "continue", settings: settings_menu, leave: lambda: "menu"},
                    draw_background, escape=lambda: "continue")


def chest_menu(hero, inventory, items, draw_world):
    """Вибір одного з предметів скрині та слота для нього (клік по предмету, потім по слоту)."""
    screen = _screen()
    clock = pygame.time.Clock()
    hover_sound = load_sound("audio/8af5b2bf5d19c00.mp3", 0.2)
    click_sound = load_sound("audio/adad00544f841e9.mp3", 0.1)

    panel = pygame.Rect(0, 0, 500, 350)
    panel.center = (WIDTH // 2, HEIGHT // 2)
    rects = [pygame.Rect(panel.x + 80 + i * 120, panel.y + 80, *item.image.get_size())
             for i, item in enumerate(items)]

    picked = None
    last_hover = None
    while True:
        mouse = pygame.mouse.get_pos()
        hovered = next((i for i, r in enumerate(rects) if r.collidepoint(mouse)), None)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_game()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if picked is None:
                    if hovered is not None:
                        click_sound.play()
                        picked = items[hovered]
                else:
                    slot = inventory.slot_at(mouse, picked)
                    if slot is not None:
                        inventory.equip(slot, picked, hero)
                        click_sound.play()
                        return
                    picked = None  # клік повз слот скасовує вибір

        if hovered is not None and hovered != last_hover:
            hover_sound.play()
        last_hover = hovered

        draw_world()
        pygame.draw.rect(screen, (50, 25, 10), panel)
        pygame.draw.rect(screen, (200, 150, 80), panel, 3)

        for i, (item, rect) in enumerate(zip(items, rects)):
            slot_name = "item_slot" if item.type == "item" else "weapon_slot"
            screen.blit(load_image(f"photo/slots/{slot_name}.png", rect.size), rect.topleft)
            item.draw(screen, rect.topleft)
            if hovered == i:
                border = (rect.width + 20, rect.height + 20)
                screen.blit(load_image("photo/slots/selected_slot.png", border), (rect.x - 10, rect.y - 10))

        if hovered is not None:
            hud.draw_item_stats(screen, items[hovered])

        pygame.display.flip()
        clock.tick(60)


def end_screen(title, color, hints, sound_path, background=None,
               title_size=48, allow_restart=False, click_closes=False):
    """Екран перемоги/поразки з поступовим затемненням. Повертає "menu" або "restart"."""
    screen = _screen()
    clock = pygame.time.Clock()
    load_sound(sound_path, 0.5).play()

    fade = pygame.Surface((WIDTH, HEIGHT))
    fade.fill((0, 0, 0))
    title_surf = load_font(hud.PIXEL_FONT, title_size).render(title, True, color)
    title_rect = title_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
    hint_font = load_font(hud.PIXEL_FONT, 24)
    hint_surfs = [hint_font.render(h, True, (255, 255, 255)) for h in hints]

    alpha = 0
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_game()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "menu"
                if event.key == pygame.K_r and allow_restart:
                    return "restart"
            if event.type == pygame.MOUSEBUTTONDOWN and click_closes:
                return "menu"

        if background:
            background()
        else:
            screen.fill((50, 0, 0))

        fade.set_alpha(alpha)
        screen.blit(fade, (0, 0))
        if alpha >= 200:
            screen.blit(title_surf, title_rect)
            for i, surf in enumerate(hint_surfs):
                screen.blit(surf, surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 10 + i * 40)))
        alpha = min(200, alpha + 5)

        pygame.display.flip()
        clock.tick(60)
