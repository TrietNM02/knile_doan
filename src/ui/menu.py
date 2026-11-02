import pygame
import sys
from untils.settings import *
from core.save_manager import SaveManager
from ui.ui_system import UIManager
from ui.settings_overlay import SettingsOverlay

class Menu:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 40)
        self.title_font = pygame.font.Font(None, 60)

        # Danh sách các nút
        self.options = ['New Game', 'Load Game', 'Settings', 'Quit']
        self.buttons = []
        self.create_buttons()

        # 🟢 Tạo UIManager riêng cho Main Menu
        self.ui_manager = UIManager()
        self.ui_manager.register('settings', SettingsOverlay(self.ui_manager))

    def create_buttons(self):
        screen_center_x = SCREEN_WIDTH // 2
        start_y = 250
        button_width = 220
        button_height = 50
        spacing = 20

        for index, text in enumerate(self.options):
            rect = pygame.Rect(0, 0, button_width, button_height)
            rect.center = (screen_center_x, start_y + index * (button_height + spacing))
            self.buttons.append({
                'text': text,
                'rect': rect,
                'action': text.lower().replace(' ', '_')
            })

    def draw(self):
        self.screen.fill((20, 20, 30))

        title_surf = self.title_font.render("KNILE", True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 120))
        self.screen.blit(title_surf, title_rect)

        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            is_hover = button['rect'].collidepoint(mouse_pos)
            bg_color = (70, 70, 90) if is_hover else (40, 40, 50)
            text_color = (255, 215, 0) if is_hover else (200, 200, 200)

            pygame.draw.rect(self.screen, bg_color, button['rect'], border_radius=8)
            pygame.draw.rect(self.screen, (100, 100, 120), button['rect'], width=2, border_radius=8)

            text_surf = self.font.render(button['text'], True, text_color)
            text_rect = text_surf.get_rect(center=button['rect'].center)
            self.screen.blit(text_surf, text_rect)

        # 🟢 Vẽ UI Manager nếu đang mở Settings
        if self.ui_manager.is_menu_open():
            self.ui_manager.draw()

    def update(self, dt):
        # Update UI Manager (nếu dùng hiệu ứng animation)
        self.ui_manager.update(dt)

    def handle_event(self, event):
        # Nếu bảng Settings đang mở, nhường event cho UIManager xử lý (bao gồm click nút BACK)
        if self.ui_manager.is_menu_open():
            self.ui_manager.handle_event(event)
            return None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            for button in self.buttons:
                if button['rect'].collidepoint(mouse_pos):
                    action = button['action']
                    
                    if action == 'new_game':
                        return 'start_game'
                    
                    elif action == 'load_game':
                        save_data = SaveManager.load_game()
                        if save_data:
                            return {'action': 'load_game', 'data': save_data}
                        else:
                            print("[MENU]: Không tìm thấy file lưu game!")
                        
                    elif action == 'settings':
                        # Mở overlay settings
                        self.ui_manager.open('settings')
                        
                    elif action == 'quit':
                        pygame.quit()
                        sys.exit()
        return None