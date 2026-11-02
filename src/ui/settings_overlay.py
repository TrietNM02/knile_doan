import pygame
from untils.settings import *

from ui.ui_system import BaseOverlay, UIPanel, UIButton
from core.save_manager import SaveManager

import pygame
from untils.settings import *
from ui.ui_system import BaseOverlay, UIPanel, UIButton

class SettingsOverlay(BaseOverlay):
    """Bảng Cài đặt Âm thanh / Đồ họa thực sự"""
    def __init__(self, manager):
        super().__init__(manager)

        panel_rect = pygame.Rect(0, 0, 450, 300)
        panel_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.panel = UIPanel(panel_rect, bg_color=(25, 30, 40))
        self.components.append(self.panel)

        # Nút Back quay lại
        back_btn_rect = pygame.Rect(0, 0, 120, 36)
        back_btn_rect.center = (panel_rect.centerx, panel_rect.bottom - 40)
        self.back_btn = UIButton(back_btn_rect, "BACK", self.manager.close_top, self.font)
        self.components.append(self.back_btn)

        # Lấy âm lượng hiện tại (từ 0.0 đến 1.0)
        self.music_volume = pygame.mixer.music.get_volume()
        
        # Tọa độ thanh Slider
        self.bar_rect = pygame.Rect(self.panel.rect.left + 40, self.panel.rect.top + 130, 370, 16)
        self.is_dragging = False

    def handle_event(self, event):
        # 1. Xử lý Click & Kéo chuột trên thanh Volume
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.bar_rect.collidepoint(event.pos):
                self.is_dragging = True
                self.update_volume_from_mouse(event.pos[0])

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.is_dragging = False

        elif event.type == pygame.MOUSEMOTION and self.is_dragging:
            self.update_volume_from_mouse(event.pos[0])

        return super().handle_event(event)

    def update_volume_from_mouse(self, mouse_x):
        # Tính tỷ lệ âm lượng dựa trên vị trí con chuột trên thanh
        relative_x = mouse_x - self.bar_rect.left
        new_vol = relative_x / self.bar_rect.width
        self.set_volume(new_vol)

    def set_volume(self, volume):
        # Giới hạn volume từ 0.0 đến 1.0
        self.music_volume = max(0.0, min(1.0, volume))
        # Áp dụng vào Pygame Music Mixer
        pygame.mixer.music.set_volume(self.music_volume)

    def draw(self):
        super().draw()
        # Tiêu đề
        title_surf = self.font.render("SETTINGS", True, (255, 255, 255))
        self.display_surface.blit(title_surf, title_surf.get_rect(centerx=self.panel.rect.centerx, top=self.panel.rect.top + 20))

        # Hiển thị % âm lượng
        vol_text = self.font.render(f"Music Volume: {int(self.music_volume * 100)}%", True, (200, 200, 200))
        self.display_surface.blit(vol_text, (self.panel.rect.left + 40, self.panel.rect.top + 90))

        # Vẽ nền thanh Slider (màu xám)
        pygame.draw.rect(self.display_surface, (60, 60, 60), self.bar_rect, border_radius=6)
        
        # Vẽ phần thanh đã kéo (màu vàng)
        fill_width = int(self.bar_rect.width * self.music_volume)
        if fill_width > 0:
            fill_rect = pygame.Rect(self.bar_rect.left, self.bar_rect.top, fill_width, self.bar_rect.height)
            pygame.draw.rect(self.display_surface, (255, 215, 0), fill_rect, border_radius=6)

        # Vẽ nút tròn con trượt
        knob_x = self.bar_rect.left + fill_width
        knob_center = (knob_x, self.bar_rect.centery)
        pygame.draw.circle(self.display_surface, (255, 255, 255), knob_center, 12)
        pygame.draw.circle(self.display_surface, (200, 200, 200), knob_center, 12, width=2)

class OptionsOverlay(BaseOverlay):
    """Bảng Pause Menu chính khi bấm ESC"""
    def __init__(self, manager):
        super().__init__(manager)

        panel_rect = pygame.Rect(0, 0, 400, 360)
        panel_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.panel = UIPanel(panel_rect, bg_color=(30, 40, 50))
        self.components.append(self.panel)

        # 1. Nút RESUME
        btn_resume = pygame.Rect(0, 0, 200, 40)
        btn_resume.center = (panel_rect.centerx, panel_rect.top + 80)
        self.resume_btn = UIButton(btn_resume, "RESUME", self.manager.close_top, self.font)
        self.components.append(self.resume_btn)

        # 2. Nút SAVE GAME
        btn_save = pygame.Rect(0, 0, 200, 40)
        btn_save.center = (panel_rect.centerx, panel_rect.top + 140)
        self.save_btn = UIButton(btn_save, "SAVE GAME", self.on_save_clicked, self.font)
        self.components.append(self.save_btn)

        # 3. Nút SETTINGS (Mở bảng chỉnh âm lượng/âm thanh)
        btn_settings = pygame.Rect(0, 0, 200, 40)
        btn_settings.center = (panel_rect.centerx, panel_rect.top + 200)
        self.settings_btn = UIButton(btn_settings, "SETTINGS", self.on_settings_clicked, self.font)
        self.components.append(self.settings_btn)

        # 4. Nút MAIN MENU
        btn_menu = pygame.Rect(0, 0, 200, 40)
        btn_menu.center = (panel_rect.centerx, panel_rect.top + 260)
        self.main_menu_btn = UIButton(btn_menu, "MAIN MENU", self.on_main_menu_clicked, self.font)
        self.components.append(self.main_menu_btn)

    def on_settings_clicked(self):
        self.manager.open('settings')

    def on_save_clicked(self):
        player = None

        if hasattr(self.manager, 'player'):
            player = self.manager.player
        elif hasattr(self.manager, 'level') and hasattr(self.manager.level, 'player'):
            player = self.manager.level.player
        elif hasattr(self.manager, 'game'):
            game = self.manager.game
            if hasattr(game, 'level') and hasattr(game.level, 'player'):
                player = game.level.player
            elif hasattr(game, 'player'):
                player = game.player

        if player:
            success = SaveManager.save_game(player, level=self.manager.level)
            if success:
                print("[UI]: Đã lưu game thành công!")
                self.manager.close_top()
        else:
            print("[UI ERROR]: Không tìm thấy object Player để lưu!")

    def on_main_menu_clicked(self):
        if hasattr(self.manager, 'close_all'):
            self.manager.close_all()
        else:
            self.manager.close_top()

        game = None
        if hasattr(self.manager, 'game'):
            game = self.manager.game
        elif hasattr(self.manager, 'level') and hasattr(self.manager.level, 'game'):
            game = self.manager.level.game

        if game and hasattr(game, 'return_to_main_menu'):
            game.return_to_main_menu()
        elif game:
            game.level = None
            game.state = 'menu'
            print("[UI]: Đã quay lại Main Menu!")
        else:
            print("[UI ERROR]: Không tìm thấy tham chiếu Game để về Menu!")

    def draw(self):
        super().draw()
        title_surf = self.font.render("OPTIONS", True, (255, 255, 255))
        title_rect = title_surf.get_rect(centerx=self.panel.rect.centerx, top=self.panel.rect.top + 20)
        self.display_surface.blit(title_surf, title_rect)