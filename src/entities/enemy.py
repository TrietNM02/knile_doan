import pygame
import random
from untils.settings import *
from entities.entity import Entity
from untils.spritesheet import load_spritesheet
from untils.particle import ParticleEffect
import heapq


class Enemy(Entity):
    def __init__(self, monster_name, pos, groups, collision_sprites, player, explosion_frames=None):
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

        # particles
        self.explosion_frames = info.get('particle_frames', [])

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
        self.scale_image_sheet = info.get('scale', 2)

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
                    frame_surf = load_spritesheet(raw_image, self.monster_size, self.monster_size, row_index, frame_index, self.scale_image_sheet)
                    temp_img_list.append(frame_surf)
                self.animations_dict[action] = temp_img_list
        else:
            for action, (file_name, row_index, total_frames) in animation_config.items():
                temp_img_list = []
                full_path = f"{base_path}{file_name}.png"
                try:
                    raw_image = pygame.image.load(full_path).convert_alpha()
                    for frame_index in range(total_frames):
                        frame_surf = load_spritesheet(raw_image, self.monster_size, self.monster_size, row_index, frame_index, self.scale_image_sheet)
                        temp_img_list.append(frame_surf)
                    self.animations_dict[action] = temp_img_list
                except FileNotFoundError:
                    print(f"Thiếu file: {full_path}")

    def get_player_grid(self):
        """Lấy tọa độ ô Grid của Player"""
        p_x = int(self.player.hitbox.centerx // self.tile_size)
        p_y = int(self.player.hitbox.centery // self.tile_size)
        return p_x, p_y
    
    def find_path_a_star(self, start_gx, start_gy, target_gx, target_gy, is_blocked_callback, max_iter=300):
        """
        Thuật toán tìm đường A* trên lưới ô (Grid).
        - start_gx, start_gy: Tọa độ ô bắt đầu của quái
        - target_gx, target_gy: Tọa độ ô đích (Player)
        - is_blocked_callback(gx, gy): Hàm kiểm tra ô (gx, gy) có bị cản hay không
        Trả về danh sách các bước đi [(gx, gy), ...] từ start đến target.
        """
        start = (start_gx, start_gy)
        goal = (target_gx, target_gy)

        if start == goal:
            return []

        open_set = []
        h_start = abs(start[0] - goal[0]) + abs(start[1] - goal[1])
        heapq.heappush(open_set, (h_start, 0, start, []))

        closed_set = set()
        iterations = 0

        while open_set and iterations < max_iter:
            iterations += 1
            current_f, current_g, current_pos, path = heapq.heappop(open_set)

            if current_pos == goal:
                return path

            if current_pos in closed_set:
                continue
            closed_set.add(current_pos)

            gx, gy = current_pos
            neighbors = [(gx, gy - 1), (gx, gy + 1), (gx - 1, gy), (gx + 1, gy)]

            for nxt in neighbors:
                if nxt in closed_set:
                    continue
                
                # Ô đích (goal) là ô player đứng (được phép tiếp cận sát cạnh),
                # nhưng các ô trung gian không được bị block bởi vật cản.
                if nxt != goal and is_blocked_callback(nxt[0], nxt[1]):
                    continue

                tentative_g = current_g + 1
                h = abs(nxt[0] - goal[0]) + abs(nxt[1] - goal[1])
                f = tentative_g + h

                heapq.heappush(open_set, (f, tentative_g, nxt, path + [nxt]))

        return []

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
            path = self.find_path_a_star(
                self.grid_x, self.grid_y, px, py,
                is_blocked_callback=lambda gx, gy: self.is_tile_blocked(gx, gy),
                max_iter=200
            )
            
            best_dir = None
            if path:
                next_tile = path[0]
                if next_tile != (px, py):
                    move_x = next_tile[0] - self.grid_x
                    move_y = next_tile[1] - self.grid_y
                    best_dir = (move_x, move_y)
            
            # Fallback an toàn: Nếu A* không tìm đường được, dùng thuật toán Manhattan cũ
            if not best_dir:
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
        action_key = f"{self.status}_{self.facing}"
        
        # Safe-guard: Nếu không có key thích hợp, fallback về idle_down
        if action_key not in self.animations_dict:
            action_key = 'die' if 'die' in self.animations_dict else f'idle_{self.facing}'
            if action_key not in self.animations_dict:
                action_key = list(self.animations_dict.keys())[0]

        speed_multiplier = 8 if self.status == 'die' else (16 if self.status == 'attack' else 12)
        self.frame += speed_multiplier * dt

        frames = self.animations_dict[action_key]

        if self.frame >= len(frames):
            if self.status == 'die':
                self.kill()
                return
            elif self.status == 'attack':
                self.status = 'idle'
                self.has_attacked = False
                self.frame = 0.0
            else:
                self.frame = 0.0

        current_image = frames[min(int(self.frame), len(frames) - 1)]
        self.image = pygame.transform.flip(current_image, True, False) if self.flip else current_image

        # Cập nhật vị trí hiển thị theo hitbox chính xác
        self.rect.centerx = self.hitbox.centerx
        self.rect.bottom = self.hitbox.bottom + (self.tile_size // 2 - self.hitbox.height // 2)

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

    def damaged(self, amount = 2):
        if not self.alive:
            return
            
        self.health -= amount
        if self.health <= 0:
            self.die()

    def die(self):
        """Xử lý sự kiện chết: Nổ bùm chíu + Biến mất chuẩn xịn"""
        self.alive = False
        self.direction = pygame.math.Vector2()
        self.is_moving = False

        # 🟡 LẤY TIỀN THƯỞNG VÀ KÍCH HOẠT VIRTUAL EFFECT (VFX)
        gold_reward = monster_data.get(self.monster_name, {}).get('gold', 10)
        
        if hasattr(self.player, 'add_gold'):
            # Truyền vị trí vị trí quái để spawn hiệu ứng số chữ bay lên
            death_pos = self.rect.center
            self.player.add_gold(gold_reward, spawn_vfx_pos=death_pos)

        # 🟢 THƯỞNG SKILL POINT + HỌC SKILL nếu đây là BOSS (nhận diện qua
        # get_occupied_tiles — hàm chỉ có ở class Boss, quái thường không có).
        if hasattr(self, 'get_occupied_tiles') and hasattr(self.player, 'on_boss_defeated'):
            self.player.on_boss_defeated(self.monster_name)

        # 1. Tắt va chạm với Player ngay lập tức
        if self in self.collision_sprites:
            self.collision_sprites.remove(self)

        # 2. PHÂN LOẠI XỬ LÝ CHẾT
        if 'die' in self.animations_dict:
            # 🟢 Trường hợp 1: Có animation 'die' -> Chuyển status để diễn hoạt ảnh gục ngã
            self.status = 'die'
            self.frame = 0.0
        else:
            # 🔴 Trường hợp 2: KHÔNG CÓ animation 'die' -> Nổ Particle rồi biến mất ngay
            target_groups = self.groups()
            if hasattr(self.player, 'level'):
                target_groups = self.player.level.all_sprites

            # Lấy frames nổ (nếu rỗng thì tự động gọi hàm load)
            frames = self.explosion_frames if self.explosion_frames else load_particle_frames()
            if frames:
                try:
                    ParticleEffect(self.rect.center, frames, target_groups)
                except Exception as e:
                    print(f"[LỖI PARTICLE]: {e}")

            # Biến mất khỏi màn hình ngay lập tức
            self.kill()
 
    def update(self, dt):
        self.animate(dt)
        if self.alive:
            self.handle_attack()
            self.move(dt)
            self.update_status()