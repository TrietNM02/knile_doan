import pygame
from untils.settings import *

class ShopOverlay:
    def __init__(self, ui_manager, player):
        self.ui_manager = ui_manager
        self.player = player
        self.display_surface = pygame.display.get_surface()
        self.font = pygame.font.Font(UI_FONT, 18)
        self.npc = None

        self.rect = pygame.Rect(0, 0, 500, 350)
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.z = LAYERS['ui_overlay']  # Đặt z-index để vẽ trên cùng

        self.buy_buttons = []

    # 🟢 THÊM HÀM NÀY: UIManager sẽ tự gọi khi mở Menu
    def on_enter(self):
        pass

    # 🟢 BỔ SUNG THÊM HÀM NÀY LÔN CHO CHẮC (Nếu UIManager có gọi khi đóng UI):
    def on_exit(self):
        pass

    def set_npc(self, npc):
        self.npc = npc

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE):
                self.ui_manager.close_top()

        # 2. Xử lý Click Chuột Trái Mua Hàng
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            for btn_rect, item_id, price in self.buy_buttons:
                if btn_rect.collidepoint(mouse_pos):
                    self.buy_item(item_id, price)
                    break

    def buy_item(self, item_id, price):
        """Hàm xử lý trừ tiền và thêm vật phẩm vào Inventory của Player"""
        if not self.player:
            return

        # Kiểm tra điều kiện đủ tiền
        if self.player.gold >= price:
            # Trừ tiền
            if self.player.spend_gold(price):
                # Thêm món đồ vào túi đồ
                self.player.add_item(item_id, 1)
                item_name = ITEM_DATABASE.get(item_id, {}).get('name', item_id)
                print(f"[SHOP]: Bạn đã mua thành công {item_name} với giá {price}G!")
        else:
            print("[SHOP]: Không đủ vàng để mua món đồ này!")

    def update(self, dt):
        pass

    def draw(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.display_surface.blit(overlay, (0, 0))

        shop_bg = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        shop_bg.fill((30, 30, 30, 240))
        self.display_surface.blit(shop_bg, self.rect.topleft)
        pygame.draw.rect(self.display_surface, (255, 215, 0), self.rect, 3, border_radius=10)

        npc_name = self.npc.name.upper() if (self.npc and hasattr(self.npc, 'name')) else "CỬA HÀNG"
        title_surf = self.font.render(f"--- CỬA HÀNG ({npc_name}) ---", True, (255, 215, 0))
        self.display_surface.blit(title_surf, (self.rect.x + 30, self.rect.y + 20))

        player_gold = getattr(self.player, 'gold', 0)
        gold_surf = self.font.render(f"Tiền hiện có: {player_gold} Gold", True, (255, 255, 100))
        self.display_surface.blit(gold_surf, (self.rect.x + 30, self.rect.y + 60))

        self.buy_buttons = []
        mouse_pos = pygame.mouse.get_pos()

        if self.npc and hasattr(self.npc, 'inventory'):
            y_pos = self.rect.y + 110
            for item_id in self.npc.inventory:
                # Lấy dữ liệu chi tiết từ ITEM_DATABASE nếu có
                item_info = ITEM_DATABASE.get(item_id, {})
                item_name = item_info.get('name', str(item_id).capitalize())
                price = item_info.get('price', 50) # Mặc định 50G nếu không khai báo giá

                # Tên item & Giá
                info_text = f"• {item_name} - Giá: {price}G"
                item_surf = self.font.render(info_text, True, (255, 255, 255))
                self.display_surface.blit(item_surf, (self.rect.x + 30, y_pos + 5))

                # Nút MUA hàng
                btn_rect = pygame.Rect(self.rect.right - 120, y_pos, 85, 30)
                is_hover = btn_rect.collidepoint(mouse_pos)
                
                # Màu nút
                can_afford = player_gold >= price
                btn_color = (60, 160, 60) if can_afford else (100, 100, 100)
                if is_hover and can_afford:
                    btn_color = (80, 200, 80)

                pygame.draw.rect(self.display_surface, btn_color, btn_rect, border_radius=6)
                pygame.draw.rect(self.display_surface, (255, 255, 255), btn_rect, 1, border_radius=6)

                btn_text = self.font.render("MUA", True, (255, 255, 255))
                self.display_surface.blit(btn_text, btn_text.get_rect(center=btn_rect.center))

                # Lưu rect nút mua
                self.buy_buttons.append((btn_rect, item_id, price))

                y_pos += 45
        else:
            empty_surf = self.font.render("Không có vật phẩm nào!", True, (150, 150, 150))
            self.display_surface.blit(empty_surf, (self.rect.x + 40, self.rect.y + 120))

        hint_surf = self.font.render("[ ESC để đóng ]", True, (180, 180, 180))
        self.display_surface.blit(hint_surf, (self.rect.x + 30, self.rect.bottom - 40))