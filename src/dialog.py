import pygame
from settings import *
from timers import Timer  # 🟢 Import class Timer của ông vào

class DialogBox:
    def __init__(self):
        self.display_surface = pygame.display.get_surface()
        self.font = pygame.font.Font(UI_FONT, 14)
        self.text = ""
        self.target_sprite = None
        self.z = LAYERS['dialog']  # Đặt z-index để vẽ trên cùng
        
        # 🟢 Dùng Timer sẵn có (Ví dụ: hiện 5000ms = 5 giây rồi tự deactivate)
        self.timer = Timer(5000, self.hide)

    @property
    def active(self):
        return self.timer.active

    def show(self, text, target_sprite):
        # Nếu đang nói câu này với NPC này thì giữ nguyên timer
        if self.active and self.target_sprite == target_sprite and self.text == text:
            return

        self.text = text
        self.target_sprite = target_sprite
        self.timer.activate()  # 🟢 Kích hoạt Timer

    def hide(self):
        self.target_sprite = None

    def update(self):
        self.timer.update()  # 🟢 Cập nhật Timer đếm ngược

    def draw(self, camera_offset):
        if not self.active or not self.target_sprite:
            return

        # 1. Tính vị trí màn hình của NPC
        npc_screen_pos = self.target_sprite.rect.center - camera_offset

        # 2. Render Text & Tính kích thước bong bóng
        text_surf = self.font.render(self.text, True, (255, 255, 255))
        padding_x, padding_y = 12, 8
        
        box_width = text_surf.get_width() + (padding_x * 2)
        box_height = text_surf.get_height() + (padding_y * 2)

        # 3. Vị trí trên đầu NPC
        box_rect = pygame.Rect(0, 0, box_width, box_height)
        box_rect.midbottom = (npc_screen_pos[0], self.target_sprite.rect.top - camera_offset.y - 15)

        # 4. Vẽ Khung Nền Đen
        bg_surface = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        bg_surface.fill((0, 0, 0, 220))
        self.display_surface.blit(bg_surface, box_rect.topleft)
        pygame.draw.rect(self.display_surface, (255, 255, 255), box_rect, 2, border_radius=6)

        # 5. Vẽ Mũi Tên Chỉ Vào Đầu NPC
        arrow_points = [
            (box_rect.centerx - 6, box_rect.bottom),
            (box_rect.centerx + 6, box_rect.bottom),
            (box_rect.centerx, box_rect.bottom + 6)
        ]
        pygame.draw.polygon(self.display_surface, (255, 255, 255), arrow_points)

        # 6. Vẽ Chữ
        text_rect = text_surf.get_rect(center=box_rect.center)
        self.display_surface.blit(text_surf, text_rect)