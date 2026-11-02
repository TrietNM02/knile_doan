import pygame
import random
import copy
from entities.enemy import Enemy
from untils.settings import *

class Boss(Enemy):
    def __init__(self, monster_name, pos, groups, collision_sprites, player, explosion_frames):
        super().__init__(monster_name, pos, groups, collision_sprites, player, explosion_frames)
        
        # 🟢 1. CẤU HÌNH THÔNG SỐ BAN ĐẦU
        data = monster_data.get(monster_name, {})
        self.monster_name = monster_name
        self.body_size = data.get('body_size', 2)

        # ⚠️ FIX #1: deepcopy để mỗi Boss có bản skill riêng, tránh share cooldown
        # giữa nhiều instance cùng loại monster_name (vì data lấy từ dict toàn cục).
        self.skills = copy.deepcopy(data.get('skills', []))

        self.max_health = getattr(self, 'health', 100)
        self.phase = 1
        self.turn_counter = 0
        self.skill_cooldown = data.get('skill_cooldown', 4)
        self.notice_radius = data.get('notice_radius', 6)

        self.rest_turns = 0
        self.is_enraged = False
        self.animation_speed = 16

        # 🟢 2. TRẠNG THÁI SKILL & CẢNH BÁO
        self.current_skill = None
        self.is_preparing_stomp = False

        # ⚠️ FIX #4: đọc số lượt gồng chiêu từ config thay vì hardcode,
        # cho phép mỗi loại boss tùy biến độ khó riêng.
        self.stomp_max_charge = data.get('stomp_charge_turns', 2)
        self.stomp_charge_turns = self.stomp_max_charge
        self.stomp_warning_tiles = []


        # 🟢 3. TÍNH TOÁN GRID & HITBOX CHUẨN KÍCH THƯỚC (2x2 Grid Tiles)
        self.grid_x = int(pos[0] // self.tile_size)
        self.grid_y = int(pos[1] // self.tile_size)

        hitbox_size = self.tile_size * self.body_size
        self.hitbox = pygame.Rect(
            self.grid_x * self.tile_size, 
            self.grid_y * self.tile_size, 
            hitbox_size, 
            hitbox_size
        )
        
        self.pos = pygame.math.Vector2(self.hitbox.center)
        self.target_pos = pygame.math.Vector2(self.pos)
        self.sync_image_with_hitbox()

    # ==========================================
    # 📐 VẬT LÝ & LƯỚI VA CHẠM (GRID & HITBOX)
    # ==========================================\

    def sync_image_with_hitbox(self):
        """Đồng bộ Hitbox với vị trí thực tế và ghim chân Sprite vào đáy Hitbox."""
        self.hitbox.center = (round(self.pos.x), round(self.pos.y))
        self.rect.center = self.hitbox.center
        # self.rect.bottom = self.hitbox.bottom

    def get_occupied_tiles(self, gx, gy):
        """Lấy danh sách các ô Grid mà thân hình Boss đang đè lên."""
        return [(gx + x, gy + y) for x in range(self.body_size) for y in range(self.body_size)]

    def is_tile_blocked(self, gx, gy):
        """Chỉ chặn nếu vị trí MỚI làm Boss ĐÈ LÊN TRỰC TIẾP ô của Player."""
        new_occupied_tiles = self.get_occupied_tiles(gx, gy)
        px, py = self.get_player_grid()

        # Nếu ô Boss chuẩn bị chiếm CÓ CHỨA đúng ô Player đang đứng -> Mới chặn
        if (px, py) in new_occupied_tiles:
            return True

        # Kiểm tra quái khác
        # ⚠️ FIX #5: check TOÀN BỘ các ô mà enemy khác đang chiếm (dùng
        # get_occupied_tiles + body_size của nó), thay vì chỉ 1 ô (grid_x, grid_y).
        # Cách cũ khiến 2 boss body_size > 1 có thể đè hitbox lên nhau.
        if hasattr(self.player, 'enemy_sprites') and self.player.enemy_sprites:
            for other in self.player.enemy_sprites.sprites():
                if other != self and getattr(other, 'alive', False):
                    other_size = getattr(other, 'body_size', 1)
                    other_tiles = [
                        (other.grid_x + x, other.grid_y + y)
                        for x in range(other_size) for y in range(other_size)
                    ]
                    if any(tile in new_occupied_tiles for tile in other_tiles):
                        return True

        # ⚠️ FIX #6 (NGUYÊN NHÂN CHÍNH khiến Boss không chịu tiến gần):
        # KHÔNG dùng check_future_collision() kế thừa từ Entity nữa. Hàm đó tự
        # tạo future_hitbox = self.hitbox.copy() -> với Boss, self.hitbox đã to
        # bằng CẢ THÂN (body_size x body_size ô, vd 96x96px). Khi ta gọi hàm đó
        # cho TỪNG Ô LẺ (target_pixel = tâm 1 ô), nó lại test một hình chữ nhật
        # to bằng cả thân Boss đặt tâm vào ô lẻ đó -> vùng test bị phóng đại,
        # lấn ra ngoài phạm vi ô Boss thực sự sắp chiếm gần 1 ô mỗi phía. Vì
        # Player cũng nằm trong collision_sprites, Boss bị "đụng" giả với
        # Player dù còn cách 1-2 ô, khiến nó dừng lại quá sớm và giữ đúng
        # khoảng cách cố định như bạn thấy.
        #
        # Sửa: build đúng 1 rect footprint (kích thước thật = body_size ô)
        # tại vị trí grid mới, test 1 lần duy nhất, bỏ qua Player/quái khác
        # (đã được check riêng theo grid ở trên).
        if self.check_boss_footprint_collision(gx, gy):
            return True

        return False

    def check_boss_footprint_collision(self, gx, gy):
        """Kiểm tra va chạm giữa TOÀN BỘ diện tích thân Boss (đúng kích thước
        thật body_size x body_size ô) với vật cản map (tường, cây, decoration...).
        Không tính Player/quái khác vì đã được kiểm tra riêng bằng grid."""
        footprint = pygame.Rect(
            gx * self.tile_size,
            gy * self.tile_size,
            self.tile_size * self.body_size,
            self.tile_size * self.body_size
        )
        for sprite in self.collision_sprites.sprites():
            if sprite is self.player or sprite is self:
                continue
            if hasattr(sprite, 'hitbox') and sprite.hitbox.colliderect(footprint):
                return True
        return False

    # ==========================================
    # 🧠 BỘ NÃO LƯỢT ĐI (AI TURN-BASED LOGIC)
    # ==========================================
    def take_turn(self):
        if not getattr(self, 'alive', True) or self.is_moving:
            return

        # 🟢 KHÓA HÀNH ĐỘNG: Nếu đang trong thời gian nghỉ sau khi dùng chiêu
        if self.rest_turns > 0:
            self.rest_turns -= 1
            self.status = 'idle'
            self.direction = pygame.math.Vector2()
            self.is_moving = False
            return

        px, py = self.get_player_grid()
        boss_tiles = self.get_occupied_tiles(self.grid_x, self.grid_y)
        min_grid_dist = min(abs(px - tx) + abs(py - ty) for tx, ty in boss_tiles)

        self._face_towards_player(px, py)

        # ⚠️ FIX #3: nếu đang gồng chiêu, KHÔNG được hủy ngang xương chỉ vì
        # Player chạy ra khỏi notice_radius. Chiêu đã gồng phải được thi triển
        # cho hết (né bằng cách chạy ra xa rồi chạy lại là exploit).
        # -> Check is_preparing_stomp TRƯỚC check notice_radius.
        if self.is_preparing_stomp:
            self.stomp_charge_turns -= 1
            if self.stomp_charge_turns <= 0:
                self.execute_current_skill()
            else:
                self.status = 'idle'
            return

        # 1. Player nằm ngoài tầm phát hiện -> Khóa cứng Boss
        if min_grid_dist > self.notice_radius:
            self._reset_action_states()
            return

        # 3. Cập nhật Cooldown & Tiến trình lượt
        self.update_skill_cooldowns()
        self.turn_counter += 1

        # 4. 🔥 KIỂM TRA KỀ SÁT (giống hệt nhánh melee bên dưới, tính trước để
        # dùng làm điều kiện cổng cho skill)
        is_adjacent = False
        for tx, ty in boss_tiles:
            # Khoảng cách Manhattan: |x1 - x2| + |y1 - y2| == 1 (Chỉ tính 4 ô kề cạnh: Trên, Dưới, Trái, Phải)
            if abs(tx - px) + abs(ty - py) == 1:
                is_adjacent = True
                break

        # ⚠️ FIX (giống OneBit Adventure): Boss CHỈ được cân nhắc ra skill khi
        # Player đã đứng KỀ SÁT (is_adjacent) VÀ skill đã hết cooldown. Trước
        # đây skill có thể kích hoạt khi Player còn cách xa (lọt vào vùng đệm
        # AOE 2 ô), khiến boss dừng lại "câu giờ" từ xa thay vì phải áp sát
        # mới được dùng chiêu gây sát thương diện rộng.
        skill_ready = self.turn_counter >= self.skill_cooldown

        if is_adjacent and skill_ready:
            selected_skill, warning_tiles = self.choose_skill(px, py)
            if selected_skill:
                self.turn_counter = 0
                self._prepare_skill(selected_skill, warning_tiles)
                return

            # Dynamic Fallback: Nếu không khai báo mảng skills trong settings.py
            if not self.skills:
                default_aoe = self.get_stomp_aoe_tiles(self.grid_x, self.grid_y)
                if (px, py) in default_aoe:
                    self.turn_counter = 0
                    self._prepare_skill({'name': 'stomp'}, default_aoe)
                    return

        # 5. 🔥 ĐÁNH THƯỜNG CẬN CHIẾN (không ra skill lượt này -> đánh melee bình thường)
        if is_adjacent:
            self.direction = pygame.math.Vector2()
            self.is_moving = False
            self.status = 'attack'
            self.frame = 0
            
            # Quay mặt trực tiếp vào Player trước khi quạt đòn
            self._face_towards_player(px, py)
            
            if hasattr(self.player, 'damaged'):
                damage = getattr(self, 'attack_damage', 10)
                self.player.damaged(damage)
            return

        # 6. Di chuyển áp sát Player
        self._move_towards_player(px, py)

    def _reset_action_states(self):
        """Reset trạng thái về Idle khi không có mục tiêu."""
        self.status = 'idle'
        self.is_preparing_stomp = False
        self.stomp_warning_tiles.clear()
        self.current_skill = None
        self.direction = pygame.math.Vector2()
        self.is_moving = False

    def _prepare_skill(self, skill, warning_tiles):
        """Chuyển Boss sang trạng thái gồng chiêu và bật viền cảnh báo."""
        # 1. Thiết lập skill hiện tại và vùng ảnh hưởng (AOE)
        self.current_skill = skill
        self.stomp_warning_tiles = warning_tiles
        
        # 2. Cấu hình số lượt gồng chiêu (đọc từ config, xem FIX #4 ở __init__)
        self.stomp_charge_turns = self.stomp_max_charge
        
        # 3. Kích hoạt cờ gồng chiêu và reset bộ đếm lượt
        self.is_preparing_stomp = True
        self.turn_counter = 0

        # 4. Cài lại thời gian hồi chiêu (Cooldown) nếu skill khai báo dưới dạng dict
        if isinstance(skill, dict) and 'cooldown' in skill:
            skill['cd_timer'] = skill['cooldown']

    def _face_towards_player(self, px, py):
        """Tính toán và xoay mặt Boss về phía Player dựa trên tọa độ Grid."""
        # Tính khoảng cách từ tâm Boss đến Player
        boss_center_x = self.grid_x + (self.body_size / 2.0)
        boss_center_y = self.grid_y + (self.body_size / 2.0)

        dx = px - boss_center_x
        dy = py - boss_center_y

        # So sánh khoảng cách X và Y để chọn hướng chính (Trái/Phải/Lên/Down)
        if abs(dx) > abs(dy):
            self.facing = 'right' if dx > 0 else 'left'
        else:
            self.facing = 'down' if dy > 0 else 'up'

    def _move_towards_player(self, px, py):
        """Chỉ dừng khi đã CHẠM MẶT (0 ô trống). Còn 1 ô trống (chấm xanh) là BẮT BUỘC BƯỚC TIẾP."""
        boss_tiles = self.get_occupied_tiles(self.grid_x, self.grid_y)
        
        # Kiểm tra xem Boss đã đứng kề sát cạnh Player chưa
        is_touching = any(abs(tx - px) + abs(ty - py) == 1 for tx, ty in boss_tiles)
        
        if is_touching:
            self.is_moving = False
            self.direction = pygame.math.Vector2()
            return

        # Sử dụng A* pathfinding cho Boss
        path = self.find_path_a_star(
            self.grid_x, self.grid_y, px, py,
            is_blocked_callback=lambda gx, gy: self.is_tile_blocked(gx, gy),
            max_iter=300
        )

        best_dir = None
        if path:
            next_tile = path[0]
            move_x = next_tile[0] - self.grid_x
            move_y = next_tile[1] - self.grid_y
            if not self.is_tile_blocked(self.grid_x + move_x, self.grid_y + move_y):
                best_dir = (move_x, move_y)

        # Fallback an toàn nếu không tìm thấy đường bằng A*
        if not best_dir:
            possible_dirs = [(0, -1), (0, 1), (-1, 0), (1, 0)]
            min_dist = float('inf')

            for move_x, move_y in possible_dirs:
                next_gx = self.grid_x + move_x
                next_gy = self.grid_y + move_y

                if self.is_tile_blocked(next_gx, next_gy):
                    continue

                next_tiles = self.get_occupied_tiles(next_gx, next_gy)
                dist = min(abs(tx - px) + abs(ty - py) for tx, ty in next_tiles)
                
                if dist < min_dist:
                    min_dist = dist
                    best_dir = (move_x, move_y)

        # Thực hiện bước di chuyển
        if best_dir:
            self.grid_x += best_dir[0]
            self.grid_y += best_dir[1]
            self.direction = pygame.math.Vector2(best_dir)

            if best_dir[0] < 0: self.facing = 'left'
            elif best_dir[0] > 0: self.facing = 'right'
            elif best_dir[1] < 0: self.facing = 'up'
            elif best_dir[1] > 0: self.facing = 'down'

            self.target_pos = pygame.math.Vector2(
                (self.grid_x + self.body_size / 2.0) * self.tile_size,
                (self.grid_y + self.body_size / 2.0) * self.tile_size
            )
            self.is_moving = True

    # ==========================================
    # ⚔️ HỆ THỐNG SKILL & TÍNH VÙNG ẢNH HƯỞNG
    # ==========================================
    def update_skill_cooldowns(self):
        """Giảm thời gian hồi chiêu của các kỹ năng sau mỗi lượt."""
        for skill in self.skills:
            if isinstance(skill, dict) and skill.get('cd_timer', 0) > 0:
                skill['cd_timer'] -= 1

    def choose_skill(self, px, py):
        """Chọn skill khả thi nhất có Player đang đứng trong vùng ảnh hưởng."""
        if not self.skills:
            return None, []

        for skill in self.skills:
            if isinstance(skill, dict) and skill.get('cd_timer', 0) <= 0:
                warning_tiles = self.get_skill_target_tiles(skill.get('name', 'stomp'), px, py)
                if (px, py) in warning_tiles:
                    return skill, warning_tiles
        return None, []

    def get_stomp_aoe_tiles(self, gx, gy):
        """Tính toán vùng AOE bao phủ 1 ô xung quanh toàn bộ thân hình Boss."""
        aoe_tiles = []
        for x in range(gx - 2, gx + self.body_size + 2):
            for y in range(gy - 2, gy + self.body_size + 2):
                aoe_tiles.append((x, y))
        return aoe_tiles

    def get_fire_breath_tiles(self, gx, gy):
        """
        ⚠️ FIX #2: thêm vùng AOE cho fire_breath (trước đây bị thiếu nên
        skill này không bao giờ được choose_skill() chọn).
        Ở đây thiết kế đơn giản: 1 hàng/cột 3 ô dài theo hướng đang facing
        Boss, xuất phát từ rìa thân hình. Tuỳ chỉnh lại theo ý đồ thiết kế thật.
        """
        facing = getattr(self, 'facing', 'down')
        length = 4
        tiles = []

        if facing == 'left':
            start_x, start_y = gx - 1, gy
            for i in range(length):
                for y in range(self.body_size):
                    tiles.append((start_x - i, start_y + y))
        elif facing == 'right':
            start_x, start_y = gx + self.body_size, gy
            for i in range(length):
                for y in range(self.body_size):
                    tiles.append((start_x + i, start_y + y))
        elif facing == 'up':
            start_x, start_y = gx, gy - 1
            for i in range(length):
                for x in range(self.body_size):
                    tiles.append((start_x + x, start_y - i))
        else:  # 'down'
            start_x, start_y = gx, gy + self.body_size
            for i in range(length):
                for x in range(self.body_size):
                    tiles.append((start_x + x, start_y + i))

        return tiles

    def get_skill_target_tiles(self, skill_name, px, py):
        """Trả về danh sách các ô chịu ảnh hưởng của loại skill tương ứng."""
        if skill_name == 'stomp':
            return self.get_stomp_aoe_tiles(self.grid_x, self.grid_y)
        elif skill_name in ['cleave', 'slash']:
            return [(px, py)]
        elif skill_name == 'fire_breath':
            # ⚠️ FIX #2: case còn thiếu trước đây
            return self.get_fire_breath_tiles(self.grid_x, self.grid_y)
        return []

    def execute_current_skill(self):
        """Thi triển chiêu thức, xả sát thương nếu Player đứng trong vùng đỏ."""
        px, py = self.get_player_grid()
        
        skill_name = 'stomp'
        if isinstance(self.current_skill, dict):
            skill_name = self.current_skill.get('name', 'stomp')

        self.status = skill_name
        self.frame = 0

        # Kiểm tra va chạm vùng nổ sát thương
        if (px, py) in self.stomp_warning_tiles:
            if hasattr(self.player, 'damaged'):
                damage_mult = 2.0 if skill_name == 'fire_breath' else 1.5
                self.player.damaged(int(getattr(self, 'attack_damage', 10) * damage_mult))

        # Reset sau khi tung chiêu
        self.is_preparing_stomp = False
        self.stomp_warning_tiles.clear()
        self.current_skill = None
        self.rest_turns = 3
        self.stomp_charge_turns = self.stomp_max_charge

    # ==========================================
    # 🎨 ANIMATION, DI CHUYỂN & GIAO DIỆN (UI)
    # ==========================================
    def move(self, dt):
        """Trượt mượt mà đến ô mục tiêu (Smooth Tile Interpolation)."""
        if not self.is_moving:
            return

        to_target = self.target_pos - self.pos
        distance = to_target.magnitude()
        move_distance = getattr(self, 'speed', 100) * dt

        if move_distance >= distance:
            self.pos = pygame.math.Vector2(self.target_pos)
            self.is_moving = False
            self.direction = pygame.math.Vector2()
            if not self.status.startswith('stomp'):
                self.status = 'idle'
        else:
            self.pos += to_target.normalize() * move_distance
            if not self.status.startswith('stomp'):
                self.status = 'walk'

        self.sync_image_with_hitbox()

    def animate(self, dt):
        """Cập nhật frame Animation mượt mà chuẩn định dạng Dict."""
        facing = getattr(self, 'facing', None)
        action_key = f"{self.status}_{facing}" if facing else self.status

        if action_key not in self.animations_dict:
            action_key = self.status

        if action_key in self.animations_dict and self.animations_dict[action_key]:
            frames = self.animations_dict[action_key]
            self.frame += self.animation_speed * dt
            
            if self.frame >= len(frames):
                if self.status == 'die':
                    self.kill()
                    return
                self.frame = 0
                if self.status in ['stomp', 'attack']:
                    self.status = 'idle'
                
            
            self.image = frames[int(self.frame)]

        self.sync_image_with_hitbox()

    def draw_warning_hitbox(self, surface, camera_offset):
        """Vẽ viền ô cảnh báo chuẩn OneBit, trong suốt hoàn toàn không che đất/cỏ."""
        if not self.is_preparing_stomp or not self.stomp_warning_tiles:
            return

        # Đổi màu viền dựa theo lượt gồng
        # Lượt cuối (chuẩn bị nổ): Viền đỏ tươi đậm
        # Các lượt trước: Viền đỏ sẫm mờ hơn
        if self.stomp_charge_turns == 1:
            border_color = (255, 30, 30)      # Đỏ tươi báo động
            line_width = 3                    # Nét viền dày hơn
        else:
            border_color = (200, 50, 50)      # Đỏ vừa
            line_width = 2

        # Vẽ trực tiếp viền từng ô lên màn hình (Không tô nền đỏ)
        for (gx, gy) in self.stomp_warning_tiles:
            screen_x = gx * self.tile_size - camera_offset.x
            screen_y = gy * self.tile_size - camera_offset.y
            
            # Chỉ vẽ duy nhất 1 khung viền chữ nhật cho mỗi ô tile
            pygame.draw.rect(
                surface, 
                border_color, 
                (screen_x, screen_y, self.tile_size, self.tile_size), 
                width=line_width
            )

        # Hiển thị số lượt đếm ngược trên đầu Boss ([2] -> [1])
        font = pygame.font.Font(None, 26)
        text_str = "!" if self.stomp_charge_turns == 1 else str(self.stomp_charge_turns)
        text_color = (255, 230, 0) if self.stomp_charge_turns == 1 else (255, 255, 255)
        
        text_surf = font.render(text_str, True, text_color)
        
        # Đặt tâm số đếm ngay trên đầu Boss
        boss_center_x = (self.grid_x + self.body_size / 2) * self.tile_size - camera_offset.x
        boss_center_y = (self.grid_y - 0.5) * self.tile_size - camera_offset.y
        text_rect = text_surf.get_rect(center=(boss_center_x, boss_center_y))

        # Khung nền nhỏ bọc số đếm cho dễ nhìn
        bg_rect = text_rect.inflate(10, 6)
        pygame.draw.rect(surface, (0, 0, 0), bg_rect, border_radius=3)
        pygame.draw.rect(surface, (255, 0, 0), bg_rect, width=1, border_radius=3)
        surface.blit(text_surf, text_rect)

    def draw_boss_ui(self, surface):
        """Vẽ thanh máu Boss hoành tráng ở đỉnh màn hình."""
        if not getattr(self, 'alive', True):
            return

        bar_width, bar_height = 360, 18
        x = (surface.get_width() - bar_width) // 2
        y = 25

        # Nền thanh máu
        pygame.draw.rect(surface, (20, 20, 20), (x, y, bar_width, bar_height), border_radius=5)

        # Phần trăm máu
        health_ratio = max(0, self.health / self.max_health)
        bar_color = (200, 40, 40) if not self.is_enraged else (255, 110, 0)
        pygame.draw.rect(surface, bar_color, (x, y, bar_width * health_ratio, bar_height), border_radius=5)
        pygame.draw.rect(surface, (220, 220, 220), (x, y, bar_width, bar_height), width=2, border_radius=5)

        # Tên Boss
        font = pygame.font.Font(None, 26)
        title_text = f"{self.monster_name.upper()} BOSS" + (" [ENRAGED]" if self.is_enraged else "")
        text_surf = font.render(title_text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=(surface.get_width() // 2, y - 12))
        surface.blit(text_surf, text_rect)

    def draw_warning(self, surface, camera_offset):
        """Wrapper vẽ cảnh báo gọi từ Level class."""
        self.draw_warning_hitbox(surface, camera_offset)

    def update(self, dt):
        """Vòng lặp cập nhật chính của Boss mỗi Frame."""
        self.animate(dt)
        if self.is_moving:
            self.move(dt)
        else:
            self.sync_image_with_hitbox()