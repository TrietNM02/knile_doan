import pygame
from untils.settings import *
from typing import Tuple

class FloatingText(pygame.sprite.Sprite):
    """Sprite hiển thị số nhảy (Vàng, Sát thương, Heal) bay dần lên rồi biến mất."""
    def __init__(self, text: str, pos: Tuple[float, float], color: Tuple[int, int, int], groups: pygame.sprite.Group, font: pygame.font.Font):
        super().__init__(groups)
        self.image = font.render(text, True, color)
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.math.Vector2(self.rect.center)
        self.z = LAYERS['main']
        
        self.float_speed = 40.0  # Pixels per second
        self.alpha = 255
        self.fade_speed = 300   # Alpha loss per second

    def update(self, dt: float) -> None:
        # Bay lên trên
        self.pos.y -= self.float_speed * dt
        self.rect.centery = int(self.pos.y)

        # Mờ dần
        self.alpha -= self.fade_speed * dt
        if self.alpha <= 0:
            self.kill()
        else:
            self.image.set_alpha(int(self.alpha))