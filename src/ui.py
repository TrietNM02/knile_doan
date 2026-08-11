import pygame
import os
from settings import *
from support import load_effect_frames, get_skill_icon

class UI:
    def __init__(self):

        # General setup
        self.display_surface = pygame.display.get_surface()
        self.font = pygame.font.Font(UI_FONT, UI_FONT_SIZE)

        # Bar setup
        self.health_bar_rect = pygame.Rect(10, 10, HEALTH_BAR_WIDTH, BAR_HEIGHT)
        self.energy_bar_rect = pygame.Rect(10, 34, ENERGY_BAR_WIDTH, BAR_HEIGHT)

        # 🟢 Lớp phủ đổi màu Map (Day/Night Overlay)
        self.day_night_surface = pygame.Surface(self.display_surface.get_size(), pygame.SRCALPHA)

        # Convert weapon dictionary
        self.weapon_graphics = {}
        for weapon_name, weapon in weapon_data.items():
            path = weapon['graphic']
            self.weapon_graphics[weapon_name] = pygame.image.load(path).convert_alpha()

        # Font cho Skill Bar
        self._skill_cd_font = pygame.font.Font(None, 26)
        self._skill_key_font = pygame.font.Font(None, 16)


    def show_bar(self, current, max_amount, bg_rect, color):
        # 1. Vẽ thanh nền và thanh chỉ số
        pygame.draw.rect(self.display_surface, UI_BG_COLOR, bg_rect)

        ratio = current / max_amount if max_amount > 0 else 0
        current_width = bg_rect.width * ratio
        current_rect = bg_rect.copy()
        current_rect.width = current_width

        pygame.draw.rect(self.display_surface, color, current_rect)
        pygame.draw.rect(self.display_surface, UI_BORDER_COLOR, bg_rect, 3)

        # 🟢 2. HIỂN THỊ CHỈ SỐ SỐ BÊN CẠNH THANH (Ví dụ: 80 / 100)
        text_str = f"{int(current)} / {int(max_amount)}"
        text_surf = self.font.render(text_str, True, TEXT_COLOR)
        
        # Đặt vị trí chữ cách mép phải của thanh bar 10px
        text_rect = text_surf.get_rect(midleft=(bg_rect.right + 10, bg_rect.centery))
        
        # (Tùy chọn) Vẽ ô nền nhỏ đằng sau chữ cho dễ nhìn
        bg_text_rect = text_rect.inflate(8, 4)
        pygame.draw.rect(self.display_surface, UI_BG_COLOR, bg_text_rect)
        pygame.draw.rect(self.display_surface, UI_BORDER_COLOR, bg_text_rect, 1)

        # Blit chữ chỉ số lên màn hình
        self.display_surface.blit(text_surf, text_rect)

    def show_exp(self, exp):
        text_surf = self.font.render(str(int(exp)), False, TEXT_COLOR)
        x = self.display_surface.get_size()[0] - 20
        y = self.display_surface.get_size()[1] - 20
        text_rect = text_surf.get_rect(bottomright = (x, y))

        pygame.draw.rect(self.display_surface, UI_BG_COLOR, text_rect.inflate(20, 20))
        self.display_surface.blit(text_surf, text_rect)
        pygame.draw.rect(self.display_surface, UI_BORDER_COLOR, text_rect.inflate(20, 20), 3)

    def draw_day_night(self, steps):
        self.day_night_surface.fill(MAP_COLORS['noon'])  # Reset lớp phủ trước khi vẽ lại
        
        cycle = (int(steps) // 50) % 2  
        if cycle == 1: # Ban đêm -> Phủ màu tối
            self.day_night_surface.fill((MAP_COLORS['evening']))
            self.display_surface.blit(self.day_night_surface, (0, 0))

    def show_steps(self, steps):
        text_surf = self.font.render(str(int(steps)), False, TEXT_COLOR)
        x = self.display_surface.get_size()[0] - 20
        y = 20
        text_rect = text_surf.get_rect(topright = (x, y))
    
        pygame.draw.rect(self.display_surface, UI_BG_COLOR, text_rect.inflate(20, 20))
        self.display_surface.blit(text_surf, text_rect)
        pygame.draw.rect(self.display_surface, UI_BORDER_COLOR, text_rect.inflate(20, 20), 3)

    def selection_box(self, left, top, has_switched):
        bg_rect = pygame.Rect(left, top, ITEM_BOX_SIZE, ITEM_BOX_SIZE)
        pygame.draw.rect(self.display_surface, UI_BG_COLOR, bg_rect)
        if has_switched:
            pygame.draw.rect(self.display_surface, UI_BORDER_COLOR_ACTIVE, bg_rect, 3)
        else:
            pygame.draw.rect(self.display_surface, UI_BORDER_COLOR, bg_rect, 3)
        return bg_rect

    def weapon_overlay(self, weapon_name):
        bg_rect = self.selection_box(10, 630, False)
        if weapon_name and weapon_name in self.weapon_graphics:
            weapon_surf = self.weapon_graphics[weapon_name]
            weapon_rect = weapon_surf.get_rect(center=bg_rect.center)
            self.display_surface.blit(weapon_surf, weapon_rect)

    def draw_skill_bar(self, player):
        skill_manager = getattr(player, 'skill_manager', None)
        skill_slots = getattr(player, 'skill_slots', None)
        if not skill_manager or not skill_slots:
            return

        ordered_slot_numbers = sorted(skill_slots.keys())
        slot_size = 64
        gap = 12
        total_w = slot_size * len(ordered_slot_numbers) + gap * (len(ordered_slot_numbers) - 1)
        screen_w, screen_h = self.display_surface.get_size()
        start_x = (screen_w - total_w) // 2
        y = screen_h - slot_size - 15

        for i, slot_num in enumerate(ordered_slot_numbers):
            x = start_x + i * (slot_size + gap)
            slot_rect = pygame.Rect(x, y, slot_size, slot_size)

            # Vẽ khung nền
            pygame.draw.rect(self.display_surface, UI_BG_COLOR, slot_rect)
            
            # 🟢 Lấy ID skill hoạt động thông qua hàm quản lý
            active_skill_name = skill_manager.get_active_skill_for_slot(slot_num)
            
            # Kiểm tra xem slot có phải là skill dung hợp (Fusion) hay không
            installed_list = skill_slots.get(slot_num, [])
            fused_skill = None
            if hasattr(skill_manager, 'check_skill_fusion') and isinstance(installed_list, list):
                fused_skill = skill_manager.check_skill_fusion(installed_list)

            is_fused = fused_skill is not None
            border_color = (255, 215, 0) if is_fused else UI_BORDER_COLOR
            pygame.draw.rect(self.display_surface, border_color, slot_rect, 3)

            # Nhãn phím tắt (1-4)
            key_surf = self._skill_key_font.render(str(slot_num), True, 'gold')
            self.display_surface.blit(key_surf, (slot_rect.left + 3, slot_rect.top + 2))

            if not active_skill_name or active_skill_name not in skill_data:
                continue

            info = skill_data[active_skill_name]

            # Vẽ Icon Kỹ Năng
            icon_surf = get_skill_icon(active_skill_name, info, slot_size, self.font)
            icon_rect = icon_surf.get_rect(center=slot_rect.center)
            self.display_surface.blit(icon_surf, icon_rect)

            # Cooldown Overlay
            cd_remaining = skill_manager.cooldowns.get(active_skill_name, 0)
            if cd_remaining > 0:
                dark_overlay = pygame.Surface((slot_size, slot_size), pygame.SRCALPHA)
                dark_overlay.fill((0, 0, 0, 150))
                self.display_surface.blit(dark_overlay, slot_rect)

                cd_surf = self._skill_cd_font.render(str(cd_remaining), True, 'white')
                cd_rect = cd_surf.get_rect(center=slot_rect.center)
                self.display_surface.blit(cd_surf, cd_rect)

    def display(self, player):
        max_health = getattr(player, 'max_health', player.stats['health'])
        max_energy = getattr(player, 'max_energy', player.stats['energy'])
        self.show_bar(player.health, max_health, self.health_bar_rect, HEALTH_COLOR)
        self.show_bar(player.energy, max_energy, self.energy_bar_rect, ENERGY_COLOR)

        steps = getattr(player, 'steps', 0)
        self.show_steps(steps)
        self.draw_day_night(steps)

        self.show_exp(player.exp)
        self.weapon_overlay(player.selected_weapon)

        self.draw_skill_bar(player)