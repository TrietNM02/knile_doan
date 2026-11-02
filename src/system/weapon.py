import pygame
import os
from untils.settings import *

class Weapon(pygame.sprite.Sprite):
    def __init__(self, player, weapon_name, groups):
        super().__init__(groups)
        self.player = player
        self.weapon_info = weapon_data[weapon_name]
        self.direction = player.action.split('_')[1]
        self.z = LAYERS['main']

        # 1. TÍNH HITBOX (Giữ nguyên cách cũ của Lance & Sword)
        self.rect = self.calculate_hitbox(weapon_name)

        # 2. LOAD VÀ XOAY EFFECT
        src_dir = os.path.dirname(__file__)
        img_path = os.path.abspath(os.path.join(src_dir, '..', 'assets', 'effects', 'slash', '0.png'))
        
        try:
            raw_image = pygame.image.load(img_path).convert_alpha()
            self.image = self.rotate_frame(raw_image)
            self.image = pygame.transform.scale(self.image, (self.rect.width, self.rect.height))
        except Exception as e:
            # Fallback nếu thiếu file ảnh
            self.image = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)

        # 3. HIỆU ỨNG FADE VÀ GÂY SÁT THƯƠNG (Giữ nguyên cơ chế cũ)
        self.alpha = 255
        self.fade_speed = 500
        self.deal_damage()

    def calculate_hitbox(self, weapon_name):
        tile_size = self.player.tile_size

        # 🟢 LANCE: GIỮ NGUYÊN 100% CODE CŨ CỦA ÔNG
        if weapon_name == 'lance':
            lance_rect = self.player.hitbox.copy()

            if self.direction == 'right':
                lance_rect.width = tile_size * 1
                lance_rect.height = tile_size * 3
                lance_rect.left = self.player.hitbox.right + tile_size
                lance_rect.centery = self.player.hitbox.centery

            elif self.direction == 'left':
                lance_rect.width = tile_size * 1
                lance_rect.height = tile_size * 3
                lance_rect.right = self.player.hitbox.left - tile_size
                lance_rect.centery = self.player.hitbox.centery

            elif self.direction == 'down':
                lance_rect.width = tile_size * 3
                lance_rect.height = tile_size * 1
                lance_rect.top = self.player.hitbox.bottom + tile_size
                lance_rect.centerx = self.player.hitbox.centerx

            elif self.direction == 'up':
                lance_rect.width = tile_size * 3
                lance_rect.height = tile_size * 1
                lance_rect.bottom = self.player.hitbox.top - tile_size - 15
                lance_rect.centerx = self.player.hitbox.centerx

            return lance_rect

        # 🟢 SWORD / AXE / KHÁC: Đánh 1 ô tương tác trước mặt
        else:
            interaction_pos = self.player.get_interaction_pos()
            rect = pygame.Rect(0, 0, tile_size, tile_size)
            rect.center = interaction_pos
            return rect

    def rotate_frame(self, frame):
        if self.direction == 'left':
            return pygame.transform.flip(frame, True, False)
        elif self.direction == 'up':
            return pygame.transform.rotate(frame, 90)
        elif self.direction == 'down':
            return pygame.transform.rotate(frame, -90)
        return frame

    def deal_damage(self):
        # 🟢 1. Lấy thẳng total_attack từ Player (Nếu không thấy thì mặc định là 10)
        total_damage = getattr(self.player, 'total_attack_damage', 10)

        # 🟢 % sát thương cộng thêm khi mục tiêu là Boss (node "Áp Đảo" trong Cây Kỹ Năng)
        get_bonus = getattr(self.player, 'get_skill_tree_bonus', None)
        boss_dmg_bonus_pct = get_bonus('boss_dmg_bonus_pct') if get_bonus else 0

        # Trừ máu Cây
        for tree in self.player.tree_sprites.sprites():
            if hasattr(tree, 'hitbox') and self.rect.colliderect(tree.hitbox):
                tree.damaged()

        # Trừ máu Quái
        for enemy in self.player.enemy_sprites.sprites():
            if hasattr(enemy, 'hitbox') and getattr(enemy, 'alive', True):
                if self.rect.colliderect(enemy.hitbox):
                    if hasattr(enemy, 'damaged'):
                        is_boss = hasattr(enemy, 'get_occupied_tiles')
                        final_damage = int(total_damage * (1 + boss_dmg_bonus_pct)) if is_boss else total_damage
                        enemy.damaged(final_damage)

    def update(self, dt):
        self.alpha -= self.fade_speed * dt
        if self.alpha <= 0:
            self.kill()
        else:
            self.image.set_alpha(int(self.alpha))