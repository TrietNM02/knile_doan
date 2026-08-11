import pygame
from settings import *


class Entity(pygame.sprite.Sprite):
    def __init__(self, groups):
        super().__init__(groups)
        self.frame = 0
        self.direction = pygame.math.Vector2()

    def check_future_collision(self, next_pos):
        """Kiểm tra xem ô mục tiêu tiếp theo có vật cản hay không trước khi bước vào"""
        future_hitbox = self.hitbox.copy()
        future_hitbox.center = (round(next_pos.x), round(next_pos.y))
            
        for sprite in self.collision_sprites.sprites():
            if hasattr(sprite, 'hitbox'):
                if sprite.hitbox.colliderect(future_hitbox):
                    return True  # Có va chạm (bị cản)
        return False  # Đường đi trống

    def move(self, dt):
        """Logic di chuyển mượt theo từng ô (Dùng chung cho Enemy/NPC nếu cần)"""
        if not self.is_moving:
            if self.direction.magnitude() > 0:
                potential_target = self.pos + self.direction * self.tile_size
                            
                if not self.check_future_collision(potential_target):
                    self.target_pos = potential_target
                    self.is_moving = True
                else:
                    self.is_moving = False
                    self.direction = pygame.math.Vector2()

            if 'walk' in getattr(self, 'action', ''):
                self.action = self.action.replace('walk_', 'idle_')
            return

        to_target = self.target_pos - self.pos
        distance = to_target.magnitude()
        speed = getattr(self, 'stats', {}).get('speed', 300)
        move_distance = speed * dt

        if move_distance >= distance:
            self.pos = pygame.math.Vector2(self.target_pos)
            self.is_moving = False
            self.direction = pygame.math.Vector2()
        else:
            self.pos += to_target.normalize() * move_distance

        # Cập nhật hitbox và rect
        if hasattr(self, 'hitbox'):
            self.hitbox.centerx = round(self.pos.x)
            self.hitbox.centery = round(self.pos.y)
            self.rect.centerx = self.hitbox.centerx
            self.rect.bottom = self.hitbox.bottom