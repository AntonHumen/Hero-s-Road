import pygame


class _BaseButton:
    """Спільна логіка кнопок: зображення, звук, hover, клік."""

    def __init__(self, x, y, width, height, text, image_path, sound_path=None):
        self.x, self.y, self.width, self.height = x, y, width, height
        self.text = text
        self.image = pygame.transform.scale(pygame.image.load(image_path), (width, height))
        self.rect = self.image.get_rect(topleft=(x, y))

        self.sound = None
        if sound_path:
            self.sound = pygame.mixer.Sound(sound_path)
            self.sound.set_volume(0.1)

        self.is_hovered = False
        self._font = None

    @staticmethod
    def _load(path, size=None):
        img = pygame.image.load(path)
        return pygame.transform.scale(img, size) if size else img

    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def _draw_text(self, screen):
        if not self.text:
            return
        if self._font is None:
            self._font = pygame.font.Font(None, 36)
        surface = self._font.render(self.text, True, (255, 255, 255))
        screen.blit(surface, surface.get_rect(center=self.rect.center))

    def _click(self):
        if self.sound:
            self.sound.play()
        pygame.event.post(pygame.event.Event(pygame.USEREVENT, button=self))


class ImageButton(_BaseButton):
    """Кнопка зі стрілками зліва й справа при наведенні."""

    def __init__(self, x, y, width, height, text, image_path,
                 hover_image_left_path=None, hover_image_right_path=None,
                 hover_left_size=None, hover_right_size=None, sound_path=None):
        super().__init__(x, y, width, height, text, image_path, sound_path)
        self.hover_image_left = (self._load(hover_image_left_path, hover_left_size)
                                 if hover_image_left_path else None)
        self.hover_image_right = (self._load(hover_image_right_path, hover_right_size)
                                  if hover_image_right_path else None)

    def draw(self, screen):
        screen.blit(self.image, self.rect.topleft)
        self._draw_text(screen)
        if not self.is_hovered:
            return
        if self.hover_image_left:
            screen.blit(self.hover_image_left, (
                self.rect.left - self.hover_image_left.get_width() - 10,
                self.rect.centery - self.hover_image_left.get_height() // 2))
        if self.hover_image_right:
            screen.blit(self.hover_image_right, (
                self.rect.right + 10,
                self.rect.centery - self.hover_image_right.get_height() // 2))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.is_hovered:
            self._click()


class ImageButton2(_BaseButton):
    """Кнопка з окремими зображеннями для станів hover/pressed."""

    def __init__(self, x, y, width, height, text, image_path,
                 hover_image_path=None, pressed_image_path=None, sound_path=None):
        super().__init__(x, y, width, height, text, image_path, sound_path)
        size = (width, height)
        self.hover_image = self._load(hover_image_path, size) if hover_image_path else None
        self.pressed_image = self._load(pressed_image_path, size) if pressed_image_path else None
        self.is_pressed = False

    def draw(self, screen):
        if self.is_pressed and self.pressed_image:
            current = self.pressed_image
        elif self.is_hovered and self.hover_image:
            current = self.hover_image
        else:
            current = self.image
        screen.blit(current, self.rect.topleft)
        self._draw_text(screen)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.is_hovered:
            self.is_pressed = True
            self._click()

    def set_pressed(self, state):
        self.is_pressed = state
