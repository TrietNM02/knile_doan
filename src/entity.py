import pygame

from settings import *


class Entity(pygame.sprite.Sprite):
    def __init__(self, groups):
        super().__init__(groups)
        self.frame = 0
        self.speed = 500
        self.direction = pygame.math.Vector2()


    def check_future_collision(self, next_pos):
        """Kiểm tra xem ô mục tiêu tiếp theo có vật cản hay không trước khi đi"""
         # Tạo một hitbox giả lập ở vị trí tương lai
        future_hitbox = self.hitbox.copy()
        future_hitbox.center = (round(next_pos.x), round(next_pos.y))
            
        for sprite in self.collision_sprites.sprites():
            if hasattr(sprite, 'hitbox'):
                if sprite.hitbox.colliderect(future_hitbox):
                    return True # Có va chạm
        return False # Đường đi trống

    def move(self, dt):
            if not self.is_moving:
                # Logic di chuyen
                if self.direction.magnitude() > 0:
                
                    potential_target = self.pos + self.direction * self.tile_size
                                
                    if not self.check_future_collision(potential_target):
                        self.target_pos = potential_target
                        self.is_moving = True
                    else:
                        self.is_moving = False
                        self.direction = pygame.math.Vector2()
                        if 'walk' in self.action:
                            self.action = self.action.replace('walk_', 'idle_')
                                
                if 'walk' in self.action:
                    self.action = self.action.replace('walk_', 'idle_')
                return
    
            to_target = self.target_pos - self.pos
            distance = to_target.magnitude()
            move_distance = self.speed * dt
    
            if move_distance >= distance:
                self.pos = pygame.math.Vector2(self.target_pos)
                self.is_moving = False
                self.direction = pygame.math.Vector2()
            else:
                self.pos += to_target.normalize() * move_distance
    
            # Cập nhật vị trí thực tế cho hitbox
            self.hitbox.centerx = round(self.pos.x)
            self.hitbox.centery = round(self.pos.y)
            
            # Cập nhật rect dựa trên đáy hitbox
            self.rect.centerx = self.hitbox.centerx
            self.rect.bottom = self.hitbox.bottom

    def collision(self, direction):
        for sprite in self.collision_sprites.sprites():
            if hasattr(sprite, 'hitbox'):
                if sprite.hitbox.colliderect(self.hitbox):
                    if direction == 'horizontal':
                        if self.direction.x > 0: # moving right
                            self.hitbox.right = sprite.hitbox.left 
                        if self.direction.x < 0: # moving left
                            self.hitbox.left = sprite.hitbox.right
                        self.rect.centerx = self.hitbox.centerx
                        self.pos.x = self.hitbox.centerx
    
                    if direction == 'vertical':
                        if self.direction.y > 0: # moving down
                            self.hitbox.bottom = sprite.hitbox.top 
                        if self.direction.y < 0: # moving up
                            self.hitbox.top = sprite.hitbox.bottom
                        self.rect.centery = self.hitbox.centery
                        self.pos.y = self.hitbox.centery
    
                    self.is_moving = False
    
                    self.target_pos = pygame.math.Vector2(self.pos)
                    self.direction = pygame.math.Vector2()   