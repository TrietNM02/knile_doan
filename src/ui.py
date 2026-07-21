import pygame
from settings import *

class UI:
    def __init__(self):

        # general
        self.display_surface = pygame.display.get_surface()
        self.font = pygame.font.Font(UI_FONT, UI_FONT_SIZE)

        # bar setup
        self.health_bar_rect = pygame.Rect(10, 10, HEALTH_BAR_WIDTH, BAR_HEIGHT)
        self.energy_bar_rect = pygame.Rect(10, 34, ENERGY_BAR_WIDTH, BAR_HEIGHT)

        # convert weapon dictionary
        self.weapon_graphics = []
        for weapon in weapon_data.values():
            path = weapon['graphic']
            weapon = pygame.image.load(path).convert_alpha()
            self.weapon_graphics.append(weapon)


    def show_bar(self, current, max_amount, bg_rect, color):
        # draw bg
        pygame.draw.rect(self.display_surface, UI_BG_COLOR, bg_rect)

        # converting stat to pixel
        ratio = current / max_amount
        current_width = bg_rect.width * ratio
        current_rect = bg_rect.copy()
        current_rect.width = current_width

        # drawing the bar
        pygame.draw.rect(self.display_surface, color, current_rect)
        pygame.draw.rect(self.display_surface, UI_BORDER_COLOR, bg_rect, 3)

    def show_exp(self, exp):
        text_surf = self.font.render(str(int(exp)), False, TEXT_COLOR)
        x = self.display_surface.get_size()[0] - 20
        y = self.display_surface.get_size()[1] - 20
        text_rect = text_surf.get_rect(bottomright = (x, y))

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

    def weapon_overlay(self, weapon_index, has_switched):
        bg_rect = self.selection_box(10, 630, has_switched)
        weapon_surf = self.weapon_graphics[weapon_index]
        weapon_rect = weapon_surf.get_rect(center = bg_rect.center)

        self.display_surface.blit(weapon_surf, weapon_rect)

    def draw_big_inventory(self, surface, player):
        # 1. Làm tối nền game phía sau
        dark_overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        dark_overlay.fill((0, 0, 0, 160))
        surface.blit(dark_overlay, (0, 0))

        # 2. Vẽ bảng nền Inventory chính (Màu nâu theo hình của ông)
        inv_width, inv_height = 700, 500  # Tăng chiều rộng để chứa cả 2 bên
        screen_w, screen_h = surface.get_size()
        inv_rect = pygame.Rect((screen_w - inv_width) // 2, (screen_h - inv_height) // 2, inv_width, inv_height)
        
        BG_BROWN = (170, 110, 75) # Màu nâu nền
        pygame.draw.rect(surface, BG_BROWN, inv_rect, border_radius=5)
        
        # 3. Vẽ đường kẻ màu xanh chia đôi bảng ở chính giữa
        center_x = inv_rect.centerx
        pygame.draw.line(surface, (0, 162, 232), (center_x, inv_rect.top), (center_x, inv_rect.bottom), width=4)

        # ================= KHU VỰC TRÁI: TRANG BỊ (EQUIPMENT) =================
        # Tâm của khu vực bên trái để vẽ hình nộm nhân vật
        left_zone_center_x = inv_rect.left + (inv_width // 4)
        
        # Vẽ hình nộm nhân vật bằng các hình tròn/bầu dục cơ bản (giống ảnh phác thảo của ông)
        # Đầu
        pygame.draw.circle(surface, 'black', (left_zone_center_x, inv_rect.top + 140), 20, width=3)
        # Thân
        body_rect = pygame.Rect(left_zone_center_x - 15, inv_rect.top + 165, 30, 60)
        pygame.draw.ellipse(surface, 'black', body_rect, width=3)
        # Chân trái / phải
        pygame.draw.circle(surface, 'black', (left_zone_center_x - 15, inv_rect.top + 235), 12, width=3)
        pygame.draw.circle(surface, 'black', (left_zone_center_x + 15, inv_rect.top + 235), 12, width=3)

        # Các ô trang bị bên trái (Màu đen)
        equip_slot_size = 55
        # Tọa độ các ô bên trái hình nộm
        left_slots = [
            pygame.Rect(left_zone_center_x - 85, inv_rect.top + 110, equip_slot_size, equip_slot_size), # Ô 1
            pygame.Rect(left_zone_center_x - 85, inv_rect.top + 180, equip_slot_size, equip_slot_size), # Ô 2
            pygame.Rect(left_zone_center_x - 85, inv_rect.top + 250, equip_slot_size, equip_slot_size), # Ô 3
        ]
        # Tọa độ các ô bên phải hình nộm
        right_slots = [
            pygame.Rect(left_zone_center_x + 35, inv_rect.top + 110, equip_slot_size, equip_slot_size), # Ô 4
            pygame.Rect(left_zone_center_x + 35, inv_rect.top + 180, equip_slot_size, equip_slot_size), # Ô 5
            pygame.Rect(left_zone_center_x + 35, inv_rect.top + 250, equip_slot_size, equip_slot_size), # Ô 6
        ]

        for slot in left_slots + right_slots:
            pygame.draw.rect(surface, 'black', slot, width=3)


        # ================= KHU VỰC PHẢI: LƯỚI Ô TRỐNG (INVENTORY) =================
        # Định hình lưới 5 hàng x 4 cột = 20 ô (Theo đúng hình vẽ của ông)
        cols = 4
        rows = 5
        slot_size = 55
        gap = 15
        
        # Tính toán vị trí bắt đầu vẽ lưới sao cho nó nằm gọn bên phải đường kẻ xanh
        grid_w = (slot_size * cols) + (gap * (cols - 1))
        grid_h = (slot_size * rows) + (gap * (rows - 1))
        
        right_zone_left = center_x + (inv_width // 4) - (grid_w // 2)
        start_y = inv_rect.top + (inv_height - grid_h) // 2

        font_amount = pygame.font.Font(None, 18)
        font_name = pygame.font.Font(None, 16)

        # Đổi balo của player thành 20 ô để khớp với lưới mới
        if player.inventory.total_slots != 20:
            player.inventory.total_slots = 20
            # Cập nhật độ dài danh sách ô chứa nếu cần
            while len(player.inventory.slots) < 20:
                player.inventory.slots.append(None)

        # Duyệt vẽ 20 ô vuông màu xanh lam (Cyan)
        for i in range(20):
            row = i // cols
            col = i % cols
            
            x = right_zone_left + col * (slot_size + gap)
            y = start_y + row * (slot_size + gap)
            slot_rect = pygame.Rect(x, y, slot_size, slot_size)

            # Vẽ ô vuông viền xanh lam theo đúng hình mẫu
            pygame.draw.rect(surface, (0, 162, 232), slot_rect, width=3)

            # Vẽ vật phẩm bên trong nếu có
            slot_data = player.inventory.slots[i]
            if slot_data is not None:
                item = slot_data['item']
                amount = slot_data['amount']

                # Tên vật phẩm viết gọn
                short_name = item.name[:5] + '.' if len(item.name) > 5 else item.name
                name_surf = font_name.render(short_name, True, 'white')
                surface.blit(name_surf, name_surf.get_rect(center = slot_rect.center))

                # Số lượng vật phẩm
                amount_surf = font_amount.render(f"x{amount}", True, 'gold')
                surface.blit(amount_surf, amount_surf.get_rect(bottomright = (slot_rect.right - 3, slot_rect.bottom - 3)))

    def display(self, player):
        self.show_bar(player.health, player.stats['health'], self.health_bar_rect, HEALTH_COLOR)
        self.show_bar(player.energy, player.stats['energy'], self.energy_bar_rect, ENERGEY_COLOR)

        self.show_exp(player.exp)

        self.weapon_overlay(player.weapon_index, player.timers['weapon switch'].active)
        # self.selection_box(80, 635)
