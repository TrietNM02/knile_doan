import pygame
import random
from settings import *
from entity import Entity
from spritesheet import load_spritesheet


class Enemy(Entity):
    def __init__(self, monster_name, pos, groups, collision_sprites, player):
        super().__init__(groups)
        self.monster_name = monster_name
        self.collision_sprites = collision_sprites
        self.player = player

        # Stats
        info = monster_data[self.monster_name]
        self.health = info['health']
        self.exp = info['exp']
        self.attack_damage = info['damage']
        self.attack_type = info['attack_type']
        self.attack_sound = info['attack_sound']

        # Move & Grid setup
        self.speed = info['speed'] * 50
        self.tile_size = 48
        self.notice_radius = info['notice_radius']

        # 🟢 QUẢN LÝ TỌA ĐỘ GRID CHUẨN (Số nguyên ô bàn cờ)
        self.grid_x = int(pos[0] // self.tile_size)
        self.grid_y = int(pos[1] // self.tile_size)

        # Status & Graphic
        self.status = 'idle'
        self.facing = 'down'
        self.monster_size = info['monster_size']
        self.frame = 0
        self.flip = False
        self.z = LAYERS['main']

        self.flip_on_left = info.get('flip_on_left', False)
        self.flip_on_right = info.get('flip_on_right', False)
        is_single_sheet = info.get('single_sheet', True)
        animation_config = info.get('animations', {})
        self.import_spritesheet(is_single_sheet, animation_config)

        action_key = f"{self.status}_{self.facing}"
        self.image = self.animations_dict[action_key][self.frame]
        
        # Tọa độ thực tế dựa theo Grid
        pixel_pos = (self.grid_x * self.tile_size + self.tile_size // 2, 
                     self.grid_y * self.tile_size + self.tile_size // 2)
        
        self.rect = self.image.get_rect(center=pixel_pos)
        self.hitbox = pygame.Rect(0, 0, info['hitbox_width'], info['hitbox_height'])
        self.hitbox.center = pixel_pos
        self.pos = pygame.math.Vector2(self.hitbox.center)
        self.target_pos = pygame.math.Vector2(self.hitbox.center)

        self.alive = True
        self.is_moving = False 
        self.has_attacked = False

    def import_spritesheet(self, is_single_sheet, animation_config):
        self.animations_dict = {}
        base_path = f'../assets/characters/monsters/{self.monster_name}/'

        if is_single_sheet:
            full_path = f"{base_path}{self.monster_name}.png"
            raw_image = pygame.image.load(full_path).convert_alpha()
            for action, (row_index, total_frames) in animation_config.items():
                temp_img_list = []
                for frame_index in range(total_frames):
                    frame_surf = load_spritesheet(raw_image, self.monster_size, self.monster_size, row_index, frame_index, 2)
                    temp_img_list.append(frame_surf)
                self.animations_dict[action] = temp_img_list
        else:
            for action, (file_name, row_index, total_frames) in animation_config.items():
                temp_img_list = []
                full_path = f"{base_path}{file_name}.png"
                try:
                    raw_image = pygame.image.load(full_path).convert_alpha()
                    for frame_index in range(total_frames):
                        frame_surf = load_spritesheet(raw_image, self.monster_size, self.monster_size, row_index, frame_index, 2)
                        temp_img_list.append(frame_surf)
                    self.animations_dict[action] = temp_img_list
                except FileNotFoundError:
                    print(f"Thiếu file: {full_path}")

    def get_player_grid(self):
        """Lấy tọa độ ô Grid của Player"""
        p_x = int(self.player.hitbox.centerx // self.tile_size)
        p_y = int(self.player.hitbox.centery // self.tile_size)
        return p_x, p_y

    def is_tile_blocked(self, gx, gy):
        """Kiểm tra ô (gx, gy) có bị đâm tường hoặc đè quái/player khác không"""
        # Check Player
        px, py = self.get_player_grid()
        if (gx, gy) == (px, py):
            return True

        # Check Quái khác
        if hasattr(self.player, 'enemy_sprites') and self.player.enemy_sprites:
            for other in self.player.enemy_sprites.sprites():
                if other != self and other.alive:
                    if (other.grid_x, other.grid_y) == (gx, gy):
                        return True

        # Check va chạm vật cản Map (nếu có hàm check_future_collision)
        target_pixel = pygame.math.Vector2(gx * self.tile_size + self.tile_size // 2, 
                                           gy * self.tile_size + self.tile_size // 2)
        if hasattr(self, 'check_future_collision') and self.check_future_collision(target_pixel):
            return True

        return False

    # 🟢 BỘ NÃO LƯỢT ĐI CHUẨN ONEBIT ADVENTURE
    def take_turn(self):
        if not self.alive or self.is_moving:
            return

        px, py = self.get_player_grid()

        # Tính khoảng cách theo ô Grid (Manhattan Distance)
        dx = px - self.grid_x
        dy = py - self.grid_y
        grid_dist = abs(dx) + abs(dy)

        # ----------------------------------------------------
        # 1. KIỂM TRA ĐÁNH: Nếu Player đứng ngay 4 ô sát cạnh (|dx| + |dy| == 1)
        # ----------------------------------------------------
        if grid_dist == 1:
            self.direction = pygame.math.Vector2()
            self.is_moving = False
            
            # Xoay mặt đúng hướng Player
            if abs(dx) > abs(dy):
                self.facing = 'right' if dx > 0 else 'left'
                self.flip = self.flip_on_right if self.facing == 'right' else self.flip_on_left
            else:
                self.facing = 'down' if dy > 0 else 'up'

            self.status = 'attack'
            self.frame = 0
            self.has_attacked = False
            return

        # ----------------------------------------------------
        # 2. XỬ LÝ DI CHUYỂN (Thổi còi khi xa / Áp sát khi gần)
        # ----------------------------------------------------
        possible_dirs = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        notice_tiles = self.notice_radius // self.tile_size

        # 🟢 TRƯỜNG HỢP A: KHÔNG CÓ PLAYER XUNG QUANH (Quái đi lang thang 1 ô ngẫu nhiên)
        if grid_dist > notice_tiles:
            # Thêm lựa chọn (0,0) để quái có tỉ lệ đứng im thư giãn
            valid_wander_dirs = [(0, 0)] 
            
            for move_x, move_y in possible_dirs:
                target_gx = self.grid_x + move_x
                target_gy = self.grid_y + move_y
                if not self.is_tile_blocked(target_gx, target_gy):
                    valid_wander_dirs.append((move_x, move_y))
            
            best_dir = random.choice(valid_wander_dirs)

        # 🟢 TRƯỜNG HỢP B: PLAYER TRONG BÁN KÍNH (Quái tìm đường áp sát)
        else:
            best_dir = None
            min_step_dist = float('inf')

            for move_x, move_y in possible_dirs:
                target_gx = self.grid_x + move_x
                target_gy = self.grid_y + move_y

                if self.is_tile_blocked(target_gx, target_gy):
                    continue

                dist = abs(px - target_gx) + abs(py - target_gy)
                if dist < min_step_dist:
                    min_step_dist = dist
                    best_dir = (move_x, move_y)

        # ----------------------------------------------------
        # 3. THỰC HIỆN BƯỚC ĐI
        # ----------------------------------------------------
        if best_dir and best_dir != (0, 0):
            self.grid_x += best_dir[0]
            self.grid_y += best_dir[1]

            self.direction = pygame.math.Vector2(best_dir)
            self.set_facing_direction()

            self.target_pos = pygame.math.Vector2(
                self.grid_x * self.tile_size + self.tile_size // 2,
                self.grid_y * self.tile_size + self.tile_size // 2
            )
            self.is_moving = True

    def set_facing_direction(self):
        if self.direction.x > 0: 
            self.facing = 'right' 
            self.flip = self.flip_on_right
        elif self.direction.x < 0: 
            self.facing = 'left' 
            self.flip = self.flip_on_left
        elif self.direction.y > 0: 
            self.facing = 'down'
        elif self.direction.y < 0: 
            self.facing = 'up'

    def animate(self, dt):
        action_key = 'die' if self.status == 'die' else f'{self.status}_{self.facing}'
        speed_multiplier = 8 if self.status == 'die' else (16 if self.status == 'attack' else 5)
        
        self.frame += speed_multiplier * dt

        if self.frame >= len(self.animations_dict[action_key]):
            if self.status == 'die':
                self.kill()
                return
            elif self.status == 'attack':
                self.status = 'idle'
                self.has_attacked = False
                self.frame = 0
            else:
                self.frame = 0

        current_image = self.animations_dict[action_key][int(self.frame)]
        self.image = pygame.transform.flip(current_image, True, False) if self.flip else current_image

        self.rect.centerx = self.pos.x
        self.rect.bottom = self.pos.y + (self.tile_size / 2)

    def move(self, dt):
        if not self.is_moving:
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

        self.hitbox.center = round(self.pos.x), round(self.pos.y)

    def handle_attack(self):
        if self.status == 'attack' and not self.has_attacked:
            action_key = f"{self.status}_{self.facing}"
            impact_frame = len(self.animations_dict[action_key]) // 2
            
            if int(self.frame) >= impact_frame:
                if hasattr(self.player, 'damaged'):
                    self.player.damaged(self.attack_damage)
                self.has_attacked = True

    def update_status(self):
        if not self.alive or self.status == 'attack':
            return
        self.status = 'walk' if self.is_moving else 'idle'

    def damaged(self):
        if self.alive:
            self.health -= 2
        self.check_death()

    def check_death(self):
        if self.health <= 0 and self.alive:
            self.alive = False
            self.frame = 0
            self.status = 'die'
            self.hitbox = pygame.Rect(0, 0, 0, 0)
            self.direction = pygame.math.Vector2()

    def update(self, dt):
        self.animate(dt)
        if self.alive:
            self.handle_attack()
            self.move(dt)
            self.update_status()

    
        


    

    
        