import pygame

from settings import *

from timers import Timer

class Generic(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups, z = LAYERS['main']):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft = pos)
        self.z = z
        if self.z != LAYERS['ground']:
            self.hitbox = self.rect.copy().inflate((-self.rect.width * 0.2, -self.rect.height * 0.75))
            self.hitbox.bottom = self.rect.bottom - 10

class Tree(Generic):
    def __init__(self, pos, surf, groups):
        super().__init__(pos, surf, groups)

        self.health = 5
        self.alive = True
        self.stump_path = f"../assets/objects/Stump1.png"
        self.stump_surf = pygame.image.load(self.stump_path).convert_alpha()
        self.hitbox = self.rect.copy().inflate(-self.rect.width * 0.7, -self.rect.height * 0.80)
        self.hitbox.bottom = self.rect.bottom

    def damaged(self):
        self.health -= 1

    def check_death(self):
        if self.health <= 0:
            self.image = self.stump_surf
            self.rect = self.image.get_rect(midbottom = self.rect.midbottom)
            self.hitbox = self.rect.copy().inflate(-10, -self.rect.height * 0.6)
            self.alive = False

    def update(self, dt):
        if self.alive:
            self.check_death()
