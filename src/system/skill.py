import pygame
import os
import math
from untils.settings import *
from untils.spritesheet import *
from untils.support import *

class SkillManager:
    """Bộ脑 quản lý Kỹ năng: Nhắm chiêu, Vẽ Highlight, Cooldown & Xả chiêu"""
    def __init__(self, player, skill_data, fusion_recipes):
        self.player = player
        self.skill_data = skill_data
        self.fusion_recipes = fusion_recipes
        self.is_aiming = False
        self.selected_skill = None
        self.aim_tile = (0, 0)
        
        # Quản lý Cooldown từng Skill (Số lượt còn lại)
        self.cooldowns = {skill_name: 0 for skill_name in skill_data}

    def start_aiming(self, skill_name):
        # 1. Nếu truyền vào là số slot (1, 2, 3, 4), lấy skill name tương ứng
        if isinstance(skill_name, int):
            skill_name = self.get_active_skill_for_slot(skill_name)

        if not skill_name or skill_name not in self.skill_data:
            return

        # 2. Check hồi chiêu
        if self.cooldowns.get(skill_name, 0) > 0:
            print(f"[SKILL]: {self.skill_data[skill_name]['name']} còn {self.cooldowns[skill_name]} lượt hồi!")
            return

        # 3. Check năng lượng
        skill_info = self.skill_data[skill_name]
        effective_cost = self._get_effective_energy_cost(skill_info['energy_cost'])
        if self.player.energy < effective_cost:
            print("[SKILL]: Không đủ Năng Lượng!")
            return

        # 4. Thi triển hoặc Bật chế độ Ngắm
        if skill_info.get('cast_type') == 'instant':
            player_gx = int(self.player.hitbox.centerx // self.player.tile_size)
            player_gy = int(self.player.hitbox.centery // self.player.tile_size)
            self.cast_skill(skill_name, (player_gx, player_gy))
        else:
            self.is_aiming = True
            self.selected_skill = skill_name

    def _get_effective_energy_cost(self, base_cost):
        """Áp dụng % giảm năng lượng tiêu hao từ Cây Kỹ Năng (nếu có node
        'energy_cost_reduction_pct' đã mở khoá)."""
        get_bonus = getattr(self.player, 'get_skill_tree_bonus', None)
        reduction_pct = get_bonus('energy_cost_reduction_pct') if get_bonus else 0
        return max(0, int(base_cost * (1 - reduction_pct)))

    def handle_input(self, camera_offset=pygame.math.Vector2()):
        if not self.is_aiming:
            return False

        mx, my = pygame.mouse.get_pos()
        world_x = mx + camera_offset.x
        world_y = my + camera_offset.y

        gx = int(world_x // self.player.tile_size)
        gy = int(world_y // self.player.tile_size)
        self.aim_tile = (gx, gy)

        mouse_click = pygame.mouse.get_just_pressed()
        keys = pygame.key.get_just_pressed()

        # CLICK TRÁI -> XẢ CHIÊU!
        if mouse_click[0]:
            # Kiểm tra khoảng cách tầm thi triển (range_tiles)
            player_center = self.player.hitbox.center if hasattr(self.player, 'hitbox') else self.player.rect.center
            pgx = int(player_center[0] // self.player.tile_size)
            pgy = int(player_center[1] // self.player.tile_size)

            info = skill_data[self.selected_skill]
            # Nếu không tìm thấy skill (hoặc selected_skill là None), dừng xử lý ngay
            if not info:
                print(f"⚠️ [LỖI]: Không tìm thấy dữ liệu cho skill '{self.selected_skill}'!")
                return
            max_range = info.get('range_tiles', 99)
            dist = max(abs(gx - pgx), abs(gy - pgy)) # Khoảng cách ô Chebyshev

            if dist > max_range:
                print(f"[SKILL]: Mục tiêu vượt quá tầm thi triển ({dist}/{max_range} ô)!")
                return True

            self.cast_skill(self.selected_skill, self.aim_tile)
            return True

        # CLICK PHẢI HOẶC ESC -> HỦY CHIÊU
        if mouse_click[2] or keys[pygame.K_ESCAPE]:
            self.cancel_aiming()
            return True

        return True 

    def check_skill_fusion(self, installed_skills):
        if not installed_skills:
            installed_skills = []

        active_set = set(s for s in installed_skills if s)
        
        for recipe_pair, fused_skill in self.fusion_recipes.items():
            if active_set == set(recipe_pair):
                return fused_skill  # Trả về ID chiêu mới (vd: 'flame_slam')
                
        return None  # Không khớp công thức nào

    def get_active_skill_for_slot(self, slot_index):
        """Lấy ID skill thực sự tại slot (hỗ trợ cả Skill Link dạng list lẫn dạng đơn)"""
        slot_data = self.player.skill_slots.get(slot_index)
        
        if not slot_data:
            return None

        # Nếu slot_data là danh sách các skill gắn vào cột (dành cho Skill Link / Fusion)
        if isinstance(slot_data, list):
            fused_skill = self.check_skill_fusion(slot_data)
            if fused_skill:
                return fused_skill
            
            for skill_id in slot_data:
                if skill_id:
                    return skill_id
            return None

        # Nếu slot_data chỉ là 1 tên skill (dạng string)
        if isinstance(slot_data, str):
            return slot_data

        return None

    def cast_skill(self, skill_name, target_tile):
        info = skill_data[skill_name]
        skill_type = info.get('type')
        tgx, tgy = target_tile

        # ⚠️ FIX #3a: Kiểm tra ô đáp Nhảy Dậm TRƯỚC khi trừ Energy/Cooldown,
        # để Player không bị mất tài nguyên khi cú nhảy bị chặn (huỷ chiêu).
        if skill_type == 'jump_aoe' and self._is_landing_tile_blocked(tgx, tgy):
            print(f"[SKILL]: Ô đáp ({tgx},{tgy}) bị chặn, không thể Nhảy Dậm tới đó!")
            return

        # KHÓA PLAYER NGAY LẬP TỨC
        self.player.is_casting = True

        # 🟢 Áp dụng bonus từ Cây Kỹ Năng: giảm % mana tiêu hao + giảm thẳng cooldown
        self.player.energy -= self._get_effective_energy_cost(info['energy_cost'])
        get_bonus = getattr(self.player, 'get_skill_tree_bonus', None)
        cooldown_reduction = int(get_bonus('cooldown_reduction_flat')) if get_bonus else 0
        self.cooldowns[skill_name] = max(0, info['cooldown_turns'] - cooldown_reduction)

        # sound
        game_sound = getattr(self.player, 'game_sound', None)
        if game_sound:
            game_sound.play_sfx(skill_name)

        player_center = self.player.hitbox.center if hasattr(self.player, 'hitbox') else self.player.rect.center
        tgx, tgy = target_tile
        target_pixel = (tgx * self.player.tile_size + self.player.tile_size // 2,
                        tgy * self.player.tile_size + self.player.tile_size // 2)

        skill_type = info.get('type')

        # 1. NẾU LÀ CHIÊU DẬM NHẢY
        # ⚠️ Thay vì dịch chuyển tức thời (teleport) Player tới ô đích ngay
        # tại đây, giờ tạo 1 JumpEffect để Player "nhảy" theo đường vòng cung
        # (parabol) trong self.duration giây. JumpEffect sẽ tự lo việc đặt lại
        # grid_x/grid_y, gây AOE, mở khoá is_casting và gọi end_turn() khi
        # tiếp đất xong — cast_skill() KHÔNG được gọi end_turn() ở đây nữa.
        if skill_type == 'jump_aoe':
            if self.player.groups():
                JumpEffect(self.player, skill_name, target_tile, self.player.groups()[0])

            self.cancel_aiming()
            # 🛑 CHÚ Ý: Không gọi self.player.end_turn() ở đây! JumpEffect sẽ
            # tự gọi khi Player tiếp đất xong (giống cơ chế của Projectile).

        # 2. NẾU LÀ CHIÊU BẮN ĐẠN (projectile) -> CHƯA END TURN NGHĨA LÀ QUÁI CHƯA ĐƯỢC CHẠY
        elif skill_type == 'projectile':
            if self.player.groups():
                Projectile(player_center, target_pixel, skill_name, target_tile, self.player, self.player.groups()[0])
            
            self.cancel_aiming()
            # 🛑 CHÚ Ý: Bỏ lệnh self.player.end_turn() ở đây! Để Projectile tự gọi khi chạm đích.

        elif skill_type == 'place_zone':
            pgx = int(self.player.hitbox.centerx // self.player.tile_size)
            pgy = int(self.player.hitbox.centery // self.player.tile_size)
            affected_tiles = SkillEffect.get_affected_tiles(tgx, tgy, info, (pgx, pgy))
            
            # Lấy chính xác biến sát thương tổng của Player
            player_damage = getattr(self.player, 'total_attack_damage', 10)
            
            # Tính damage mỗi lượt theo hệ số zone_damage_multiplier
            multiplier = info.get('zone_damage_multiplier', 1.0)
            dpt = info.get('damage_per_turn', int(player_damage * multiplier))

            zone = ZoneEffect(
                tiles=affected_tiles,
                duration=info.get('duration_turns', 2),
                damage_per_turn=dpt,
                user=self.player,
                groups=self.player.groups()[0],
                skill_name=skill_name
            )

            if not hasattr(self.player, 'active_zones'):
                self.player.active_zones = []
            self.player.active_zones.append(zone)

            self.cancel_aiming()
            self.player.is_casting = False
            if hasattr(self.player, 'end_turn'):
                self.player.end_turn()

        # 3. CÁC CHIÊU CÒN LẠI (Instant: Chém Quét, Xoáy Kiếm, Thổi Gió...)
        else:
            if self.player.groups():
                SkillEffect(self.player, skill_name, target_tile, 0, self.player.groups()[0])

            self.cancel_aiming()

            # ⚠️ FIX: Trước đây is_casting KHÔNG BAO GIỜ được mở khoá lại ở
            # nhánh này (chỉ Projectile mới tự mở khoá) -> dùng xong Thổi Gió
            # (hay Chém Quét/Xoáy Kiếm) là Player bị khoá cứng vĩnh viễn,
            # không thể di chuyển/hành động gì nữa. Giờ mở khoá ngay khi chiêu
            # đã xử lý xong (các chiêu này gây tác dụng tức thời, không cần
            # chờ animation bay như Projectile hay JumpEffect).
            self.player.is_casting = False

            if hasattr(self.player, 'end_turn'):
                self.player.end_turn()

    def cancel_aiming(self):
        self.is_aiming = False
        self.selected_skill = None

    def _is_landing_tile_blocked(self, gx, gy):
        """⚠️ FIX #3a: Kiểm tra ô đích của Nhảy Dậm có bị tường/vật cản hoặc
        quái khác (kể cả Boss nhiều ô) chiếm hay không, trước khi cho Player
        'nhảy' tới đó. Trước đây code chỉ kiểm tra KHOẢNG CÁCH (range_tiles)
        chứ không kiểm tra ô đích có hợp lệ để đứng hay không, nên Player có
        thể nhảy thẳng vào tường hoặc chồng lên Boss."""
        target_pixel = pygame.math.Vector2(
            gx * self.player.tile_size + self.player.tile_size // 2,
            gy * self.player.tile_size + self.player.tile_size // 2
        )
        if hasattr(self.player, 'check_future_collision') and self.player.check_future_collision(target_pixel):
            return True

        enemy_group = getattr(self.player, 'enemy_sprites', None)
        if enemy_group:
            for enemy in enemy_group.sprites():
                if not getattr(enemy, 'alive', True):
                    continue
                if hasattr(enemy, 'get_occupied_tiles') and hasattr(enemy, 'grid_x') and hasattr(enemy, 'grid_y'):
                    if (gx, gy) in enemy.get_occupied_tiles(enemy.grid_x, enemy.grid_y):
                        return True
                elif hasattr(enemy, 'grid_x') and hasattr(enemy, 'grid_y'):
                    if (enemy.grid_x, enemy.grid_y) == (gx, gy):
                        return True
        return False

    def update_cooldowns(self):
        for skill_name in self.cooldowns:
            if self.cooldowns[skill_name] > 0:
                self.cooldowns[skill_name] -= 1

    def draw_preview(self, surface, camera_offset=pygame.math.Vector2()):
        if not self.is_aiming or not self.selected_skill:
            return

        info = skill_data.get(self.selected_skill)
        if not info: return

        gx, gy = self.aim_tile

        # Vị trí Player
        player_center = self.player.hitbox.center if hasattr(self.player, 'hitbox') else self.player.rect.center
        pgx = int(player_center[0] // self.player.tile_size)
        pgy = int(player_center[1] // self.player.tile_size)

        affected_tiles = SkillEffect.get_affected_tiles(gx, gy, info, (pgx, pgy))

        # Kiểm tra nằm ngoài range_tiles thì đổi màu cảnh báo
        max_range = info.get('range_tiles', 99)
        dist = max(abs(gx - pgx), abs(gy - pgy))
        is_out_of_range = dist > max_range

        color = (255, 50, 50, 120) if not is_out_of_range else (100, 100, 100, 120)

        overlay = pygame.Surface((self.player.tile_size, self.player.tile_size), pygame.SRCALPHA)
        overlay.fill(color)

        for tile_x, tile_y in affected_tiles:
            px = tile_x * self.player.tile_size - camera_offset.x
            py = tile_y * self.player.tile_size - camera_offset.y

            surface.blit(overlay, (px, py))
            rect = pygame.Rect(px, py, self.player.tile_size, self.player.tile_size)
            border_color = (255, 0, 0) if not is_out_of_range else (150, 150, 150)
            pygame.draw.rect(surface, border_color, rect, 2)

class Projectile(pygame.sprite.Sprite):
    """Viên đạn tận dụng hàm load_spritesheet có sẵn + hỗ trợ cả thư mục ảnh lẻ & 1 ảnh tĩnh"""

    def __init__(self, start_pos, target_pos, skill_name, target_tile, user, groups):
        super().__init__(groups)
        self.user = user
        self.skill_name = skill_name
        self.target_tile = target_tile
        self.info = skill_data[skill_name]
        self.z = LAYERS.get("main", 3)

        self.pos = pygame.math.Vector2(start_pos)
        self.target_pos = pygame.math.Vector2(target_pos)
        self.total_distance = (self.target_pos - self.pos).length()
        self.parabol_height = 50

        # Load danh sách frame đạn
        projectile_path = self.info.get("effect_path", "")
        self.frames = load_effect_frames(projectile_path, self.info)
        self.frame_index = 0

        if self.frames:
            self.image = self.frames[0]
        else:
            # Fallback hình tròn nếu không load được ảnh
            self.image = pygame.Surface((16, 16), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (255, 100, 0), (8, 8), 6)

        # 2. Tính hướng và khoảng cách bay
        direction_vec = self.target_pos - self.pos
        distance = direction_vec.length()

        if distance > 0:
            self.direction = direction_vec.normalize()
        else:
            self.direction = pygame.math.Vector2(1, 0)

        # Tính góc xoay (Pygame dùng độ, trục Y ngược chiều so với hệ tọa độ thông thường)
        self.angle = math.degrees(math.atan2(-self.direction.y, self.direction.x))

        self.speed = self.info.get("speed", 800)
        self.rect = self.image.get_rect(center=self.pos)

        # -------------------------------------------------------------
        # 🔥 TÍNH TỐC ĐỘ ANIMATION THEO QUÃNG ĐƯỜNG BAY
        # -------------------------------------------------------------
        if len(self.frames) > 0 and distance > 0:
            flight_time = distance / self.speed  # Thời gian đạn bay (giây)
            # Số frame chuyển đổi trong 1 giây để khớp chính xác thời gian bay
            self.anim_speed = len(self.frames) / flight_time
            print(self.anim_speed)
        else:
            self.anim_speed = 10  # Giá trị mặc định nếu không tính được

        # Cập nhật rect theo ảnh đã xoay
        if self.frames:
            self.image = pygame.transform.rotate(self.frames[0], self.angle)
        else:
            self.image = pygame.Surface((16, 16), pygame.SRCALPHA)

        self.rect = self.image.get_rect(center=self.pos)


    def update(self, dt):
        # 1. Chạy Animation đồng bộ theo thời gian bay
        if len(self.frames) > 1:
            self.frame_index += self.anim_speed * dt

            if self.frame_index >= len(self.frames):
                self.frame_index = len(self.frames) - 1

            current_frame = self.frames[int(self.frame_index)]
            self.image = pygame.transform.rotate(current_frame, self.angle)

        # 2. Di chuyển đạn
        self.pos += self.direction * self.speed * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))

        # 3. Chạm target -> Kích nổ & KẾT THÚC LƯỢT PLAYER
        if (self.target_pos - self.pos).length() < 10:
            if self.user.groups():
                SkillEffect(
                    self.user,
                    self.skill_name,
                    self.target_tile,
                    self.angle,
                    self.user.groups()[0],
                )
            
            # ĐẠN BAY ĐẾN NƠI MỚI MỞ KHÓA PLAYER VÀ HẾT LƯỢT PLAYER!
            self.user.is_casting = False
            if hasattr(self.user, 'end_turn'):
                self.user.end_turn()

            self.kill()

class JumpEffect(pygame.sprite.Sprite):
    """Điều khiển Player 'nhảy' theo đường VÒNG CUNG (parabol) từ vị trí hiện
    tại tới ô đáp trong self.duration giây, thay vì dịch chuyển tức thời
    (teleport). Khi tiếp đất xong: đặt lại grid_x/grid_y cho đúng, tạo
    SkillEffect gây AOE tại ô đáp, rồi mở khoá is_casting + gọi end_turn()
    (giống cơ chế Projectile tự gọi khi bay tới đích)."""

    def __init__(self, user, skill_name, target_tile, groups):
        super().__init__(groups)
        self.user = user
        self.skill_name = skill_name
        self.target_tile = target_tile
        self.info = skill_data[skill_name]
        self.z = LAYERS.get('main', 3)

        self.start_pos = pygame.math.Vector2(user.pos)
        tgx, tgy = target_tile
        self.end_pos = pygame.math.Vector2(
            tgx * user.tile_size + user.tile_size // 2,
            tgy * user.tile_size + user.tile_size // 2
        )

        # Thời gian nhảy & độ cao vòng cung có thể tự cấu hình theo skill_data
        # (thêm 'jump_duration'/'jump_arc_height' vào skill_data nếu muốn tinh
        # chỉnh riêng), mặc định 0.4 giây và cao 40px.
        self.duration = self.info.get('jump_duration', 0.4)
        self.arc_height = self.info.get('jump_arc_height', 40)
        self.elapsed = 0.0

        # Sprite này không cần tự hiển thị gì (bản thân Player đã hiển thị
        # animation của nó) — chỉ dùng để được Group gọi update(dt) mỗi frame.
        self.image = pygame.Surface((1, 1), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.end_pos)

        # Khoá hẳn hệ di chuyển bước-ô bình thường của Player trong lúc nhảy
        self.user.is_casting = True
        self.user.is_moving = False

    def update(self, dt):
        self.elapsed += dt
        t = min(self.elapsed / self.duration, 1.0) if self.duration > 0 else 1.0

        # Nội suy tuyến tính vị trí thực (logic) X/Y theo thời gian
        current = self.start_pos.lerp(self.end_pos, t)

        # Công thức parabol chuẩn: 4*h*t*(1-t) -> bằng 0 ở t=0 và t=1, đỉnh
        # cao nhất = arc_height ở giữa quãng đường (t=0.5)
        arc_offset = 4 * self.arc_height * t * (1 - t)

        # Vị trí LOGIC (dùng cho hitbox/grid) không có vòng cung
        self.user.pos = current
        if hasattr(self.user, 'hitbox'):
            self.user.hitbox.center = (round(current.x), round(current.y))

        # Vị trí HIỂN THỊ (rect) mới có vòng cung -> tạo cảm giác nhấc bổng
        # lên rồi rơi xuống. Đặt SAU animate() của Player trong cùng 1 frame
        # (JumpEffect được thêm vào group sau Player nên chạy update() sau).
        if hasattr(self.user, 'rect'):
            self.user.rect.centerx = round(current.x)
            self.user.rect.centery = round(current.y - arc_offset)

        if t >= 1.0:
            self._finish()

    def _finish(self):
        gx, gy = self.target_tile

        # 1. Cập nhật tọa độ lưới
        if hasattr(self.user, 'grid_x'): self.user.grid_x = gx
        if hasattr(self.user, 'grid_y'): self.user.grid_y = gy
        
        # 2. Cập nhật tọa độ Vector
        self.user.pos = pygame.math.Vector2(self.end_pos)
        
        # 🟢 Cập nhật Hitbox: Đảm bảo ĐÁY (bottom) của hitbox chạm đúng mốc Y kết thúc
        if hasattr(self.user, 'hitbox'): 
            # Nếu end_pos của bạn là tâm ô, đáy hitbox phải cộng thêm nửa chiều cao ô (TILE_SIZE // 2)
            # Hoặc gán chính xác theo logic Hitbox của bạn:
            self.user.hitbox.center = (round(self.end_pos.x), round(self.end_pos.y))
        
        # 🟢 Chuyển state về idle TRƯỚC để cập nhật lại ảnh sprite chuẩn
        if hasattr(self.user, 'state'):
            self.user.state = 'idle'

        # 🟢 Cập nhật lại khung hình ảnh (image) ngay lập tức
        if hasattr(self.user, 'animate'):
            self.user.animate(0) # Buộc load lại frame 0 của 'idle'

        # 🟢 Đồng bộ lại rect theo hitbox
        if hasattr(self.user, 'update_rect_to_hitbox'):
            self.user.update_rect_to_hitbox()

        # 1. GÂY SÁT THƯƠNG DẬM BAN ĐẦU (1.4x)
        if self.user.groups():
            SkillEffect(self.user, self.skill_name, self.target_tile, 0, self.user.groups()[0])

        # 2. TẠO THẢM LỬA NẾU CÓ CHỈ SỐ BURN (Flame Slam)
        if 'zone_damage_multiplier' in self.info:
            affected_tiles = SkillEffect.get_affected_tiles(gx, gy, self.info, (gx, gy))

            player_dmg = getattr(self.user, 'total_attack_damage', 10)
            zone_dmg = int(player_dmg * self.info['zone_damage_multiplier'])

            zone = ZoneEffect(
                tiles=affected_tiles,
                duration=self.info.get('duration_turns', 2),
                damage_per_turn=zone_dmg,
                user=self.user,
                groups=self.user.groups()[0],
                skill_name=self.skill_name,
            )

            if not hasattr(self.user, 'active_zones'):
                self.user.active_zones = []
            self.user.active_zones.append(zone)

        # 3. Mở khoá Player + Kết thúc lượt
        self.user.is_casting = False
        if hasattr(self.user, 'end_turn'):
            self.user.end_turn()

        self.kill()

class ZoneEffect(pygame.sprite.Sprite):
    def __init__(self, tiles, duration, damage_per_turn, user, groups, skill_name, zone_color=None):
        super().__init__(groups)
        self.tiles = tiles
        self.duration = duration
        self.user = user
        self.skill_name = skill_name
        self.z = LAYERS.get('floor', 2)

        info = skill_data.get(skill_name, {})

        # 1. Tính toán sát thương
        if damage_per_turn is not None and damage_per_turn > 0:
            self.damage = damage_per_turn
        else:
            player_dmg = getattr(user, 'total_attack_damage', 10)
            multiplier = info.get('zone_damage_multiplier', 1.0)
            self.damage = int(player_dmg * multiplier)

        # 2. CẮT FRAMES TỪ SPRITESHEET (Giữ frame_width & frame_height)
        self.spawn_frames = []
        self.loop_frames = []
        self.end_frames = []

        # Nếu skill khai báo file startup/end riêng
        if 'startup_path' in info:
            startup_info = info.get('startup_info', info)
            startup_frames = load_effect_frames(info['startup_path'], startup_info)
            if startup_frames:
                self.spawn_frames = startup_frames[:4]
                self.loop_frames  = startup_frames[4:]

            if 'end_path' in info:
                end_info = info.get('end_info', info)
                self.end_frames = load_effect_frames(info['end_path'], end_info)
        else:
            # Nếu truyền frame_width = 128, frame_height = 128 trong info
            effect_path = info.get('effect_path', info.get('impact_effect_path', ''))
            all_frames = load_effect_frames(effect_path, info)

            if all_frames:
                spawn_count = info.get('spawn_count', 0)
                end_count = info.get('end_count', 0)

                if spawn_count > 0 or end_count > 0:
                    self.spawn_frames = all_frames[:spawn_count]
                    if end_count > 0:
                        self.loop_frames = all_frames[spawn_count:-end_count]
                        self.end_frames = all_frames[-end_count:]
                    else:
                        self.loop_frames = all_frames[spawn_count:]
                else:
                    self.loop_frames = all_frames

        # 3. Quản lý trạng thái animation (SPAWN -> IDLE -> DISAPPEAR)
        self.state = 'SPAWN' if self.spawn_frames else 'IDLE'
        self.frame_index = 0
        self.anim_speed = info.get('speed', 12)
        self.zone_color = zone_color or info.get('zone_color', (255, 60, 0, 130))

        # 4. Kích thước vùng vẽ lên bản đồ
        tile_size = user.tile_size
        self.min_x = min(t[0] for t in tiles)
        self.min_y = min(t[1] for t in tiles)
        max_x = max(t[0] for t in tiles)
        max_y = max(t[1] for t in tiles)

        width = (max_x - self.min_x + 1) * tile_size
        height = (max_y - self.min_y + 1) * tile_size

        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft=(self.min_x * tile_size, self.min_y * tile_size))

        self.deal_zone_damage()

    def update(self, dt):
        current_frame = None

        # --- GIAI ĐOẠN 1: SPAWN ---
        if self.state == 'SPAWN':
            self.frame_index += self.anim_speed * dt
            if self.frame_index >= len(self.spawn_frames):
                self.state = 'IDLE'
                self.frame_index = 0
            elif self.spawn_frames:
                idx = int(self.frame_index) % len(self.spawn_frames)
                current_frame = self.spawn_frames[idx]

        # --- GIAI ĐOẠN 2: IDLE ---
        if self.state == 'IDLE':
            if self.loop_frames:
                # 1. Tăng frame_index theo thời gian
                self.frame_index += self.anim_speed * dt
                
                # 2. CHIA LẤY DƯ NGAY LẬP TỨC để index luôn nằm trong khoảng 0 -> len - 1
                self.frame_index %= len(self.loop_frames)
                
                # 3. Lấy frame chuẩn xác (không bao giờ bị Out of Index hay None)
                current_frame = self.loop_frames[int(self.frame_index)]

        # --- GIAI ĐOẠN 3: DISAPPEAR ---
        elif self.state == 'DISAPPEAR':
            self.frame_index += self.anim_speed * dt
            if not self.end_frames or self.frame_index >= len(self.end_frames):
                self.kill()
                return
            else:
                idx = int(self.frame_index) % len(self.end_frames)
                current_frame = self.end_frames[idx]

        # --- RENDER LÊN MÀN HÌNH ---
        self.image.fill((0, 0, 0, 0)) # Reset nền trong suốt

        # 💡 KIỂM TRA CHẮC CHẮN current_frame LÀ PHÙ HỢP (KHÔNG PHẢI NONE)
        if current_frame is not None:
            scale_width = int(self.image.get_width()) # Độ rộng mong muốn
            scale_height = self.image.get_height()

            scaled_frame = pygame.transform.scale(current_frame, (scale_width, scale_height))
            
            # Căn giữa hình ảnh vào trung tâm Surface của Zone
            offset_x = (self.image.get_width() - scale_width) // 2
            
            self.image.blit(scaled_frame, (offset_x, 0))
        else:
            # Vẽ màu dự phòng nếu không tìm thấy frame
            tile_size = self.user.tile_size
            for tgx, tgy in self.tiles:
                rel_x = (tgx - self.min_x) * tile_size
                rel_y = (tgy - self.min_y) * tile_size
                rect = pygame.Rect(rel_x, rel_y, tile_size, tile_size)
                pygame.draw.rect(self.image, self.zone_color, rect)

    def deal_zone_damage(self):
        enemy_group = getattr(self.user, 'enemy_sprites', None)
        if not enemy_group: 
            return
        for enemy in enemy_group.sprites():
            if not getattr(enemy, 'alive', True): 
                continue
            center = enemy.hitbox.center if hasattr(enemy, 'hitbox') else enemy.rect.center
            egx = int(center[0] // self.user.tile_size)
            egy = int(center[1] // self.user.tile_size)

            if (egx, egy) in self.tiles and self.damage > 0 and hasattr(enemy, 'damaged'):
                enemy.damaged(self.damage)

    def on_turn_end(self):
        self.duration -= 1
        if self.duration > 0:
            self.deal_zone_damage()
        else:
            if self.end_frames:
                self.state = 'DISAPPEAR'
                self.frame_index = 0
            else:
                self.kill()

class PushSlideEffect(pygame.sprite.Sprite):
    """Cho Quái TRƯỢT MƯỢT từ vị trí cũ sang vị trí mới sau khi bị Thổi Gió
    đẩy lùi, thay vì set thẳng hitbox/rect khiến quái 'dịch chuyển' tức thời
    (teleport) — nhìn giống bị bốc từ chỗ này thả thẳng qua chỗ kia, dễ bị
    tưởng nhầm là "đẩy chéo" vì cú snap quá đột ngột."""

    def __init__(self, enemy, start_pixel, end_pixel, groups, duration=0.25):
        super().__init__(groups)
        self.enemy = enemy
        self.start_pos = pygame.math.Vector2(start_pixel)
        self.end_pos = pygame.math.Vector2(end_pixel)
        self.duration = duration
        self.elapsed = 0.0
        self.z = LAYERS.get('main', 3)

        # Sprite này không tự hiển thị gì (bản thân Quái đã có hình riêng),
        # chỉ mượn Group để được gọi update(dt) mỗi frame.
        self.image = pygame.Surface((1, 1), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.end_pos)

        # Khoá hệ di chuyển bước-ô bình thường của Quái trong lúc bị đẩy trượt
        if hasattr(enemy, 'is_moving'):
            enemy.is_moving = False

    def update(self, dt):
        # Nếu Quái đã chết/bị xoá giữa chừng thì tự huỷ theo, không update nữa
        if not getattr(self.enemy, 'alive', True) or not self.enemy.groups():
            self.kill()
            return

        self.elapsed += dt
        t = min(self.elapsed / self.duration, 1.0) if self.duration > 0 else 1.0
        current = self.start_pos.lerp(self.end_pos, t)

        if hasattr(self.enemy, 'pos'):
            self.enemy.pos = pygame.math.Vector2(current)
        if hasattr(self.enemy, 'hitbox'):
            self.enemy.hitbox.center = (round(current.x), round(current.y))
        if hasattr(self.enemy, 'rect'):
            self.enemy.rect.centerx = round(current.x)
            self.enemy.rect.centery = round(current.y)

        if t >= 1.0:
            # Chốt lại đúng vị trí cuối để không lệch do sai số nội suy
            if hasattr(self.enemy, 'pos'):
                self.enemy.pos = pygame.math.Vector2(self.end_pos)
            if hasattr(self.enemy, 'target_pos'):
                self.enemy.target_pos = pygame.math.Vector2(self.end_pos)
            if hasattr(self.enemy, 'hitbox'):
                self.enemy.hitbox.center = (round(self.end_pos.x), round(self.end_pos.y))
            if hasattr(self.enemy, 'rect'):
                self.enemy.rect.centerx = self.enemy.hitbox.centerx
                self.enemy.rect.bottom = self.enemy.hitbox.bottom
            self.kill()

class EdgeEffect(pygame.sprite.Sprite):
    """1 hiệu ứng nhỏ đặt tại 1 CẠNH của hitbox (trên/dưới/trái/phải) — dùng
    cho Thổi Gió (wind_blast): hiển thị 4 hiệu ứng quanh 4 cạnh Player thay
    vì 1 hiệu ứng lẻ tại ô chuột đang chỉ."""

    def __init__(self, frames, anim_speed, center_pixel, angle, groups):
        super().__init__(groups)
        self.frames = frames
        self.anim_speed = anim_speed
        self.angle = angle
        self.frame_index = 0
        self.duration = 0.3
        self.elapsed = 0.0
        self.z = LAYERS.get('main', 3)

        if self.frames:
            self.image = pygame.transform.rotate(self.frames[0], self.angle)
        else:
            # Không có ảnh hiệu ứng thật -> tạo màu xanh nhạt gợi gió để test
            self.image = pygame.Surface((32, 32), pygame.SRCALPHA)
            self.image.fill((170, 225, 255, 170))

        self.rect = self.image.get_rect(center=center_pixel)

    def update(self, dt):
        if self.frames:
            self.frame_index += self.anim_speed * dt
            if self.frame_index >= len(self.frames):
                self.kill()
                return
            current_frame = self.frames[int(self.frame_index)]
            self.image = pygame.transform.rotate(current_frame, self.angle)
            self.rect = self.image.get_rect(center=self.rect.center)
        else:
            # Luôn có đồng hồ đếm ngược riêng để tự kill() kể cả khi thiếu
            # file ảnh hiệu ứng — tránh sprite tồn tại vĩnh viễn.
            self.elapsed += dt
            if self.elapsed >= self.duration:
                self.kill()

class SkillEffect(pygame.sprite.Sprite):
    def __init__(self, user, skill_name, target_tile, angle, groups):
        super().__init__(groups)
        self.user = user
        self.info = skill_data[skill_name]
        self.z = LAYERS['main']
        self.angle = angle

        self.anim_speed = self.info.get("impact_speed", 20)
        self.duration = 0.3
        self.elapsed = 0.0

        impact_info = self.info.copy()
        if "impact_cols" in self.info:
            impact_info['cols'] = self.info['impact_cols']
            impact_info['rows'] = self.info['impact_rows']
            impact_info['total_frames'] = self.info['impact_total_frames']

        # Lấy vị trí Player làm mốc
        player_center = user.hitbox.center if hasattr(user, 'hitbox') else user.rect.center
        pgx = int(player_center[0] // user.tile_size)
        pgy = int(player_center[1] // user.tile_size)

        gx, gy = target_tile
        self.affected_tiles = self.get_affected_tiles(gx, gy, self.info, (pgx, pgy))

        impact_path = self.info.get(
            'impact_effect_path', self.info.get("effect_path", "")
            )
        self.frames = load_effect_frames(impact_path , self.info)
        self.frame_index = 0

        # ⚠️ FIX (hiệu ứng Thổi Gió hiện sai vị trí): push_back luôn gây sát
        # thương ở vùng QUANH PLAYER, không liên quan gì tới ô chuột đang chỉ
        # (target_tile). Trước đây mọi skill đều hiển thị 1 sprite DUY NHẤT
        # tại target_tile -> Thổi Gió hiện hiệu ứng ngay chỗ chuột chỉ, sai
        # hẳn vị trí thật gây sát thương. Giờ: push_back hiển thị 4 hiệu ứng
        # nhỏ tại 4 CẠNH hitbox Player (trên/dưới/trái/phải), sprite gốc này
        # chỉ lo tính sát thương, không tự vẽ gì lên màn hình.
        if self.info.get('type') == 'push_back':
            self._spawn_hitbox_edge_effects(user, groups)
            self.image = pygame.Surface((1, 1), pygame.SRCALPHA)
            self.rect = self.image.get_rect(center=player_center)
            self.deal_damage()
            return

        pixel_pos = (gx * user.tile_size + user.tile_size // 2, gy * user.tile_size + user.tile_size // 2)

        if self.frames:
            # 🔥 XOAY ẢNH IMPACT TRƯỚC KHI GÁN
            self.image = pygame.transform.rotate(self.frames[0], self.angle)
        else:
            self.image = pygame.Surface((32, 32), pygame.SRCALPHA)

        self.rect = self.image.get_rect(center=pixel_pos)

        # Tính toán & Gây sát thương ngay lập tức
        self.deal_damage()

        if self.frames:
            self.image = self.frames[0]
            self.rect = self.image.get_rect(center=pixel_pos)
        else:
            # 🔴 NẾU KHÔNG CÓ CÓ ẢNH -> Tạo 1 ô màu hiển thị tạm 0.3 giây để test!
            self.image = pygame.Surface((user.tile_size, user.tile_size), pygame.SRCALPHA)
            self.image.fill((255, 200, 0, 180)) # Màu vàng trong suốt
            self.rect = self.image.get_rect(center=pixel_pos)
            self.duration = 0.3 # Hiện trong 0.3 giây rồi tắt

    def _spawn_hitbox_edge_effects(self, user, groups):
        """Tạo 4 EdgeEffect đặt đúng tại 4 CẠNH hitbox Player (trên, dưới,
        trái, phải) — mỗi cạnh 1 hiệu ứng nhỏ, dùng chung frame ảnh đã load
        ở self.frames (không load lại 4 lần cho tốn)."""
        hitbox = user.hitbox if hasattr(user, 'hitbox') else user.rect
        edge_specs = [
            ((hitbox.centerx, hitbox.top), 90),      # Cạnh trên
            ((hitbox.centerx, hitbox.bottom), -90),  # Cạnh dưới
            ((hitbox.left, hitbox.centery), 180),    # Cạnh trái
            ((hitbox.right, hitbox.centery), 0),     # Cạnh phải
        ]
        for center_pixel, edge_angle in edge_specs:
            EdgeEffect(self.frames, self.anim_speed, center_pixel, edge_angle, groups)

    @staticmethod
    def get_affected_tiles(center_gx, center_gy, skill_info, player_tile=(0,0)):
        """Tính danh sách ô bị ảnh hưởng dựa theo `type` của Skill"""
        tiles = []
        skill_type = skill_info.get('type', 'projectile')
        pgx, pgy = player_tile

        # 1. FireBall (Fireball) -> Bắn đơn mục tiêu vào ô chỉ định
        if skill_type == 'projectile' and (skill_info.get('name') == 'FireBall' or skill_info.get('name') == 'WaterBall'):
            tiles.append((center_gx, center_gy))

        # 2. Jump Stomp (Jump Stomp) -> Dậm nhảy gây sát thương diện rộng 3x3 quanh ô tiếp đất
        elif skill_type == 'jump_aoe':
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    tiles.append((center_gx + dx, center_gy + dy))

        # 3. Wind Blast (Wind Blast) -> Gây hiệu ứng xung quanh Player hoặc hướng nhắm (3x3 quanh Player)
        elif skill_type == 'push_back':
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx != 0 or dy != 0:
                        tiles.append((pgx + dx, pgy + dy))

        elif skill_type == 'place_zone':
            # ⚠️ FIX: điều kiện cũ dùng biến 'tgx' chưa từng định nghĩa
            # (NameError) và so tên 'Vòi Rồng Nước' không khớp tên thật
            # trong settings.py ('Water Spout'), nên luôn rơi vào nhánh else
            # (chỉ 1 ô) dù comment ghi rõ thiết kế là "Chọn vị trí 3x3".
            # Nhánh 'place_zone' hiện chỉ có water_spout dùng -> luôn quét
            # 3x3 quanh tâm cho đúng thiết kế, bỏ hẳn điều kiện rối rắm cũ.
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    tiles.append((center_gx + dx, center_gy + dy))

        

        # 4. WaterBall (Waterball) -> Bắn xuyên theo đường thẳng từ Player tới chiều dài range_tiles
        # elif skill_type == 'projectile' and skill_info.get('name') == 'WaterBall':
        #     range_len = skill_info.get('range_tiles', 4)
        #     dx = center_gx - pgx
        #     dy = center_gy - pgy

        #     # Xác định hướng bắn chính (Ngang hoặc Dọc)
        #     step_x = 0
        #     step_y = 0
        #     if abs(dx) >= abs(dy):
        #         step_x = 1 if dx > 0 else (-1 if dx < 0 else 0)
        #     else:
        #         step_y = 1 if dy > 0 else (-1 if dy < 0 else 0)

        #     if step_x == 0 and step_y == 0:
        #         step_x = 1 # Mặc định bắn sang phải nếu trùng ô

        #     for i in range(1, range_len + 1):
        #         tiles.append((pgx + step_x * i, pgy + step_y * i))

        # Mặc định (fallback)
        else:
            tiles.append((center_gx, center_gy))

        return tiles

    def deal_damage(self):
        player_total_damage = getattr(self.user, 'total_attack_damage', 10)

        # 🟢 Áp dụng % sát thương Skill cộng thêm từ Cây Kỹ Năng
        get_bonus = getattr(self.user, 'get_skill_tree_bonus', None)
        skill_dmg_bonus_pct = get_bonus('skill_dmg_pct') if get_bonus else 0
        boss_dmg_bonus_pct = get_bonus('boss_dmg_bonus_pct') if get_bonus else 0

        base_skill_damage = int(player_total_damage * self.info['damage_multiplier'] * (1 + skill_dmg_bonus_pct))
        enemy_group = getattr(self.user, 'enemy_sprites', None)

        print(f"🎯 [SKILL CAST]: '{self.info['name']}' - Các ô bị đánh: {self.affected_tiles}")

        if not enemy_group or len(enemy_group.sprites()) == 0:
            return

        # Lấy vị trí Player để phục vụ đẩy lùi (Wind Blast)
        player_center = self.user.hitbox.center if hasattr(self.user, 'hitbox') else self.user.rect.center
        pgx = int(player_center[0] // self.user.tile_size)
        pgy = int(player_center[1] // self.user.tile_size)

        for enemy in enemy_group.sprites():
            if not getattr(enemy, 'alive', True):
                continue

            is_boss = hasattr(enemy, 'get_occupied_tiles') and hasattr(enemy, 'grid_x') and hasattr(enemy, 'grid_y')
            if is_boss:
                enemy_tiles = enemy.get_occupied_tiles(enemy.grid_x, enemy.grid_y)
            else:
                enemy_center = enemy.hitbox.center if hasattr(enemy, 'hitbox') else enemy.rect.center
                egx = int(enemy_center[0] // self.user.tile_size)
                egy = int(enemy_center[1] // self.user.tile_size)
                enemy_tiles = [(egx, egy)]

            # Kiểm tra trúng chiêu
            if any(tile in self.affected_tiles for tile in enemy_tiles):
                # +% sát thương riêng khi mục tiêu là Boss (node "Áp Đảo")
                skill_damage = int(base_skill_damage * (1 + boss_dmg_bonus_pct)) if is_boss else base_skill_damage

                print(f"💥 [HIT!] Đánh trúng {getattr(enemy, 'monster_name', 'Quái')}! Gây {skill_damage} damage.")
                
                # 1. Trừ máu quái
                if hasattr(enemy, 'damaged'):
                    enemy.damaged(skill_damage)

                # 2. Xử lý hiệu ứng ĐẨY LÙI (Push Back) cho Skill Thổi Gió
                if self.info.get('type') == 'push_back':
                    push_dist = self.info.get('push_distance', 3)

                    if hasattr(enemy, 'grid_x') and hasattr(enemy, 'grid_y'):
                        raw_dx = enemy.grid_x - pgx
                        raw_dy = enemy.grid_y - pgy
                        if abs(raw_dx) >= abs(raw_dy):
                            dir_x = 1 if raw_dx >= 0 else -1
                            dir_y = 0
                        else:
                            dir_x = 0
                            dir_y = 1 if raw_dy >= 0 else -1

                        final_gx, final_gy = enemy.grid_x, enemy.grid_y
                        for step in range(1, push_dist + 1):
                            next_gx = enemy.grid_x + dir_x * step
                            next_gy = enemy.grid_y + dir_y * step
                            if hasattr(enemy, 'is_tile_blocked') and enemy.is_tile_blocked(next_gx, next_gy):
                                break
                            final_gx, final_gy = next_gx, next_gy

                        enemy.grid_x, enemy.grid_y = final_gx, final_gy

                        body_size = getattr(enemy, 'body_size', 1)
                        half_footprint = (self.user.tile_size * body_size) // 2

                        start_pixel = enemy.hitbox.center if hasattr(enemy, 'hitbox') else enemy.rect.center
                        new_ex = enemy.grid_x * self.user.tile_size + half_footprint
                        new_ey = enemy.grid_y * self.user.tile_size + half_footprint

                        if self.user.groups():
                            PushSlideEffect(enemy, start_pixel, (new_ex, new_ey), self.user.groups()[0])
                        elif hasattr(enemy, 'hitbox'):
                            enemy.hitbox.center = (new_ex, new_ey)
                            enemy.rect.center = enemy.hitbox.center

                        if hasattr(enemy, 'target_pos'):
                            enemy.target_pos = pygame.math.Vector2(new_ex, new_ey)
                        if hasattr(enemy, 'is_moving'):
                            enemy.is_moving = False

                        print(f"💨 [PUSH BACK]: Đẩy lùi {getattr(enemy, 'monster_name', 'Quái')} tới ô ({final_gx},{final_gy})!")


    def update(self, dt):
        # Chạy animation nổ tại chỗ rồi biến mất
        if len(self.frames) > 0:
            # 🔥 🔥 TĂNG TỐC ĐỘ ANIMATION IMPACT (Ví dụ: 30 fps thay vì 15)
            self.frame_index += self.anim_speed * dt  

            if self.frame_index >= len(self.frames):
                self.kill() # Nổ xong thì xóa
            else:
                # Lấy frame hiện tại
                current_frame = self.frames[int(self.frame_index)]
                # 🔥 XOAY FRAME NÀY THEO HƯỚNG ĐẠN
                self.image = pygame.transform.rotate(current_frame, self.angle)
                # Cập nhật lại rect vì ảnh xoay có kích thước khác
                self.rect = self.image.get_rect(center=self.rect.center)
        else:
            # ⚠️ FIX: trước đây nếu không có frame ảnh (thiếu asset), sprite
            # này TỒN TẠI VĨNH VIỄN vì không nhánh nào gọi kill() cả — giờ tự
            # đếm ngược self.duration (0.3s) rồi tự biến mất.
            self.elapsed += dt
            if self.elapsed >= self.duration:
                self.kill()