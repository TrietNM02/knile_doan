import pygame
from settings import *

# ==========================================
# 1. BASE UI COMPONENTS (Thành phần giao diện)
# ==========================================
class UIElement:
    """Class cha của mọi phần tử UI (Button, Panel, Slot...)"""
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)
        self.visible = True

    def handle_event(self, event):
        pass

    def update(self, dt):
        pass

    def draw(self, surface):
        pass


class UIPanel(UIElement):
    """Khung nền UI"""
    def __init__(self, rect, bg_color=(35, 35, 45), border_color=(200, 200, 200), radius=12):
        super().__init__(rect)
        self.bg_color = bg_color
        self.border_color = border_color
        self.radius = radius

    def draw(self, surface):
        if not self.visible:
            return
        pygame.draw.rect(surface, self.bg_color, self.rect, border_radius=self.radius)
        if self.border_color:
            pygame.draw.rect(surface, self.border_color, self.rect, 3, border_radius=self.radius)


class UIButton(UIElement):
    """Nút bấm tương tác hỗ trợ Hover & Click Event"""
    def __init__(self, rect, text, callback, font, bg_color=(60, 60, 80), hover_color=(90, 90, 120)):
        super().__init__(rect)
        self.text = text
        self.callback = callback
        self.font = font
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.is_hovered = False

        self.text_surf = self.font.render(self.text, True, (255, 255, 255))
        self.text_rect = self.text_surf.get_rect(center=self.rect.center)

    def handle_event(self, event):
        if not self.visible:
            return False

        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered and self.callback:
                self.callback()
                return True # Đã tiêu thụ Event click
        return False

    def draw(self, surface):
        if not self.visible:
            return
        color = self.hover_color if self.is_hovered else self.bg_color
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, (220, 220, 220), self.rect, 2, border_radius=8)
        surface.blit(self.text_surf, self.text_rect)


# ==========================================
# 2. BASE OVERLAY (Class Cha Cho Các Menu)
# ==========================================
class BaseOverlay:
    """Khung sườn chung cho mọi Overlay/Menu trong game"""
    def __init__(self, manager):
        self.manager = manager
        self.display_surface = pygame.display.get_surface()
        self.font = pygame.font.Font(None, 30)
        self.components = []

    def on_enter(self):
        """Gọi khi Menu vừa được mở"""
        pass

    def on_exit(self):
        """Gọi khi Menu đóng"""
        pass

    def handle_event(self, event):
        """Truyền Event xuống cho các Component con"""
        for component in self.components:
            if component.handle_event(event):
                return True
        return False

    def update(self, dt):
        for component in self.components:
            component.update(dt)

    def draw_dim_background(self):
        """Làm tối game phía sau"""
        dim_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dim_surf.fill((0, 0, 0, 140))
        self.display_surface.blit(dim_surf, (0, 0))

    def draw(self):
        self.draw_dim_background()
        for component in self.components:
            component.draw(self.display_surface)


# ==========================================
# 3. UI MANAGER (Bộ Quản Lý Trung Tâm)
# ==========================================
class UIManager:
    """Quản lý Stack trạng thái Menu và luồng Input"""
    def __init__(self):
        self.overlays = {}
        self.stack = [] # Stack quản lý lớp Menu đang mở

    def register(self, name, overlay_instance):
        self.overlays[name] = overlay_instance

    def open(self, name):
        if name in self.overlays and self.overlays[name] not in self.stack:
            overlay = self.overlays[name]
            self.stack.append(overlay)
            overlay.on_enter()

    def close_top(self):
        if self.stack:
            top = self.stack.pop()
            top.on_exit()

    def is_menu_open(self):
        return len(self.stack) > 0

    def handle_event(self, event):
        """Chỉ cho phép Menu nằm TRÊN CÙNG của Stack nhận Event"""
        if self.stack:
            # Menu xử lý Event
            handled = self.stack[-1].handle_event(event)
            return True # Khóa Input không cho World/Player nhận
        return False

    def update(self, dt):
        if self.stack:
            self.stack[-1].update(dt)

    def draw(self):
        # Draw toàn bộ Menu trong Stack theo thứ tự dưới lên trên
        for overlay in self.stack:
            overlay.draw()