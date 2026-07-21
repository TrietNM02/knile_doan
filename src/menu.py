import pygame
import sys
from settings import *

class Menu:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 40)
        self.title_font = pygame.font.Font(None, 60)

        # Danh sách các nút
        self.options = ['New Game', 'Load Game', 'Settings', 'Quit']
        self.buttons = []
        self.create_buttons()

    def create_buttons(self):
        # Thiết lập kích thước và vị trí các nút ở chính giữa màn hình
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
                'action': text.lower().replace(' ', '_') # Tạo id hành động: 'new_game', 'load_game', ...
            })

    def draw(self):
        # Nền menu
        self.screen.fill((20, 20, 30))

        # Tiêu đề game
        title_surf = self.title_font.render("KNILE", True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 120))
        self.screen.blit(title_surf, title_rect)

        # Vẽ các nút
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            # Effect khi di chuột vào nút (Hover)
            is_hover = button['rect'].collidepoint(mouse_pos)
            bg_color = (70, 70, 90) if is_hover else (40, 40, 50)
            text_color = (255, 215, 0) if is_hover else (200, 200, 200)

            # Vẽ khung nút
            pygame.draw.rect(self.screen, bg_color, button['rect'], border_radius=8)
            pygame.draw.rect(self.screen, (100, 100, 120), button['rect'], width=2, border_radius=8)

            # Vẽ chữ trên nút
            text_surf = self.font.render(button['text'], True, text_color)
            text_rect = text_surf.get_rect(center=button['rect'].center)
            self.screen.blit(text_surf, text_rect)

    def handle_event(self, event):
        """Xử lý sự kiện click chuột trong Menu"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: # Click chuột trái
            mouse_pos = event.pos
            for button in self.buttons:
                if button['rect'].collidepoint(mouse_pos):
                    action = button['action']
                    
                    if action == 'new_game':
                        return 'start_game' # Chuyển trạng thái để vào Game
                    
                    elif action == 'load_game':
                        print("Load Game clicked (Chức năng chưa phát triển)")
                        
                    elif action == 'settings':
                        print("Settings clicked (Chức năng chưa phát triển)")
                        
                    elif action == 'quit':
                        pygame.quit()
                        sys.exit()
        return None