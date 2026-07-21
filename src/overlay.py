import pygame
from settings import *
from ui_system import BaseOverlay, UIPanel, UIButton

class InventoryOverlay(BaseOverlay):
    def __init__(self, manager, player):
        super().__init__(manager)
        self.player = player

        # 1. Khung Main Panel
        self.width, self.height = 700, 450
        panel_rect = pygame.Rect(0, 0, self.width, self.height)
        panel_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        
        self.panel = UIPanel(panel_rect, bg_color=(160, 100, 75), border_color=(100, 60, 45), radius=0)
        self.components.append(self.panel)

        # 2. 🔴 Nút Đóng 'X' ở góc trên bên phải bảng
        close_btn_size = 32
        close_btn_rect = pygame.Rect(
            panel_rect.right - close_btn_size - 8,
            panel_rect.top + 8,
            close_btn_size,
            close_btn_size
        )
        
        # Nút X có callback là self.manager.close_top (tự đóng menu khi click)
        self.close_btn = UIButton(
            rect=close_btn_rect,
            text="X",
            callback=self.manager.close_top,
            font=self.font,
            bg_color=(180, 50, 50),     # Màu đỏ
            hover_color=(230, 60, 60)   # Đỏ sáng khi rê chuột vào
        )
        self.components.append(self.close_btn)

        # 2. Cấu hình Vị trí
        self.mid_x = panel_rect.left + self.width // 2
        self.slot_size = 48
        self.slot_padding = 12

        # Equipment Slots (Trái / Phải Player)
        left_center_x = panel_rect.left + (self.width // 4)
        left_center_y = panel_rect.top + (self.height // 2)

        self.equip_left_rect = pygame.Rect(0, 0, self.slot_size, self.slot_size)
        self.equip_left_rect.center = (left_center_x - 90, left_center_y)

        self.equip_right_rect = pygame.Rect(0, 0, self.slot_size, self.slot_size)
        self.equip_right_rect.center = (left_center_x + 90, left_center_y)

        # Lưới 16 ô Balo Grid (4x4)
        self.grid_slots = []
        grid_start_x = self.mid_x + 35
        grid_start_y = panel_rect.top + 50

        for row in range(4):
            for col in range(4):
                x = grid_start_x + col * (self.slot_size + self.slot_padding)
                y = grid_start_y + row * (self.slot_size + self.slot_padding)
                self.grid_slots.append(pygame.Rect(x, y, self.slot_size, self.slot_size))

        self.hovered_slot_index = -1

    def handle_event(self, event):
        # 🟢 Bắt sự kiện di chuyển chuột để detect Hover
        if event.type == pygame.MOUSEMOTION:
            self.hovered_slot_index = -1
            for index, slot_rect in enumerate(self.grid_slots):
                if slot_rect.collidepoint(event.pos):
                    self.hovered_slot_index = index
                    break

        # 🟢 Bắt sự kiện Click chuột (Sử dụng item / Trang bị)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Click trái
                if self.hovered_slot_index != -1:
                    # Dùng item tại slot đó
                    if hasattr(self.player, 'use_item_at_slot'):
                        self.player.use_item_at_slot(self.hovered_slot_index)

        return super().handle_event(event)

    def draw_tooltip(self, surface, item, mouse_pos):
        """🟢 Vẽ bảng thông tin Item đi theo con trỏ chuột"""
        padding = 8
        name_surf = self.font.render(item.name if hasattr(item, 'name') else item.id, True, (255, 255, 255))
        
        # Kích thước Tooltip Box
        tt_width = name_surf.get_width() + padding * 2
        tt_height = name_surf.get_height() + padding * 2
        
        tt_rect = pygame.Rect(mouse_pos[0] + 15, mouse_pos[1] + 15, tt_width, tt_height)
        
        # Giữ Tooltip không bị tràn ra ngoài màn hình
        if tt_rect.right > SCREEN_WIDTH: tt_rect.right = mouse_pos[0] - 15
        if tt_rect.bottom > SCREEN_HEIGHT: tt_rect.bottom = mouse_pos[1] - 15

        # Vẽ nền & viền Tooltip
        pygame.draw.rect(surface, (20, 20, 20), tt_rect, border_radius=5)
        pygame.draw.rect(surface, (255, 215, 0), tt_rect, 2, border_radius=5) # Viền vàng
        surface.blit(name_surf, (tt_rect.left + padding, tt_rect.top + padding))

    def draw(self):
        super().draw()
        surface = self.display_surface
        mouse_pos = pygame.mouse.get_pos()

        # 1. Đường vạch phân chia đỏ
        pygame.draw.line(surface, (200, 0, 0), (self.mid_x, self.panel.rect.top), (self.mid_x, self.panel.rect.bottom), 3)

        # 2. Preview Player & Equipment Slots
        if hasattr(self.player, 'image'):
            scaled_img = pygame.transform.scale(self.player.image, (96, 96))
            img_rect = scaled_img.get_rect(center=(self.panel.rect.left + (self.width // 4), self.panel.rect.top + (self.height // 2)))
            surface.blit(scaled_img, img_rect)

        pygame.draw.rect(surface, (255, 255, 255), self.equip_left_rect, 3)
        pygame.draw.rect(surface, (255, 255, 255), self.equip_right_rect, 3)

        # 3. Render 16 Slots Grid + Hover Effect
        hovered_item = None
        for index, slot_rect in enumerate(self.grid_slots):
            is_hovered = (index == self.hovered_slot_index)
            
            # Màu viền: Vàng (Hover) hoặc Đen (Bình thường)
            border_color = (255, 215, 0) if is_hovered else (0, 0, 0)
            border_width = 4 if is_hovered else 3
            
            pygame.draw.rect(surface, border_color, slot_rect, border_width)

            # Render Item inside Slot
            if hasattr(self.player, 'inventory') and index < len(self.player.inventory.slots):
                slot_data = self.player.inventory.slots[index]
                if slot_data:
                    item = slot_data['item']
                    if is_hovered: hovered_item = item # Lưu lại item đang hover để vẽ tooltip

                    if hasattr(item, 'image'):
                        item_img = pygame.transform.scale(item.image, (48, 48))
                        surface.blit(item_img, item_img.get_rect(center=slot_rect.center))
                    else:
                        amount_surf = self.font.render(str(slot_data['amount']), True, (255, 255, 255))
                        surface.blit(amount_surf, amount_surf.get_rect(center=slot_rect.center))

        # 4. Vẽ Tooltip lên trên cùng nếu đang Hover vào ô có Item
        if hovered_item:
            self.draw_tooltip(surface, hovered_item, mouse_pos)


class SettingsOverlay(BaseOverlay):
    def __init__(self, manager):
        super().__init__(manager)

        # Panel chính
        panel_rect = pygame.Rect(0, 0, 400, 250)
        panel_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.panel = UIPanel(panel_rect, bg_color=(30, 40, 50))
        self.components.append(self.panel)

        # Nút Resume
        btn_rect = pygame.Rect(0, 0, 150, 40)
        btn_rect.center = (panel_rect.centerx, panel_rect.centery + 30)
        self.resume_btn = UIButton(btn_rect, "RESUME", self.manager.close_top, self.font)
        self.components.append(self.resume_btn)

    def draw(self):
        super().draw()
        title_surf = self.font.render("SETTINGS", True, (255, 255, 255))
        title_rect = title_surf.get_rect(centerx=self.panel.rect.centerx, top=self.panel.rect.top + 20)
        self.display_surface.blit(title_surf, title_rect)