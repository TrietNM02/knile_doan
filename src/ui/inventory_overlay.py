import pygame
import os
from untils.settings import *
from ui.ui_system import BaseOverlay, UIPanel, UIButton
from untils.support import load_effect_frames, get_skill_icon
from core.save_manager import SaveManager

class InventoryOverlay(BaseOverlay):
    def __init__(self, manager, player):
        super().__init__(manager)
        self.player = player

        # 1. Khung Main Panel
        self.width, self.height = 920, 580
        panel_rect = pygame.Rect(0, 0, self.width, self.height)
        panel_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        
        self.panel = UIPanel(panel_rect, bg_color=(160, 100, 75), border_color=(100, 60, 45), radius=0)
        self.components.append(self.panel)

        # Font
        self.font = pygame.font.Font(UI_FONT, UI_FONT_SIZE)
        self.small_font = pygame.font.Font(UI_FONT, 20)
        self.icon_font = pygame.font.Font(UI_FONT, 16)
        

        # 2. Nút Đóng 'X' ở góc trên bên phải bảng
        close_btn_size = 32
        close_btn_rect = pygame.Rect(
            panel_rect.right - close_btn_size - 8,
            panel_rect.top + 8,
            close_btn_size,
            close_btn_size
        )
        
        self.close_btn = UIButton(
            rect=close_btn_rect,
            text="X",
            callback=self.manager.close_top,
            font=self.font,
            bg_color=(180, 50, 50),     # Màu đỏ
            hover_color=(230, 60, 60)   # Đỏ sáng khi rê chuột vào
        )
        self.components.append(self.close_btn)

        # 3. Cấu hình Vị trí
        self.mid_x = panel_rect.left + self.width // 2
        self.slot_size = 48
        self.slot_padding = 12

        # Equipment Slots (Trái / Phải Player)
        left_center_x = panel_rect.left + (self.width // 4)
        left_center_y = panel_rect.top + (self.height // 2)

        # Ô trang bị Vũ khí bên trái
        self.equip_left_rect = pygame.Rect(0, 0, self.slot_size, self.slot_size)
        self.equip_left_rect.center = (left_center_x - 90, left_center_y)

        # Ô phụ bên phải
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

        # KÉO THẢ (DRAG & DROP) — tab BALO
        self.dragging_source = None  
        self.dragged_item_data = None  

        # 4. TAB BAR: BALO / CÂY KỸ NĂNG / LIÊN KẾT
        self.active_tab = 'bag'
        tab_labels = [('bag', 'BALO'), ('skill_tree', 'SKILL TREE'), ('skill_link', 'SKILL LINK')]
        tab_width, tab_height = 140, 34
        tab_gap = 6
        total_tabs_w = tab_width * len(tab_labels) + tab_gap * (len(tab_labels) - 1)
        tabs_start_x = panel_rect.centerx - total_tabs_w // 2
        tabs_y = panel_rect.top - tab_height - 4

        self.tab_buttons = []
        for tab_key, label in tab_labels:
            idx = len(self.tab_buttons)
            btn_rect = pygame.Rect(
                tabs_start_x + idx * (tab_width + tab_gap),
                tabs_y,
                tab_width, tab_height
            )
            btn = UIButton(
                rect=btn_rect,
                text=label,
                callback=(lambda k=tab_key: self._switch_tab(k)),
                font=self.font,
                bg_color=(120, 80, 55),
                hover_color=(160, 110, 75)
            )
            self.tab_buttons.append((tab_key, btn))
            self.components.append(btn)

        # 5. TAB "LIÊN KẾT" (Skill Link): 4 ô Slot (phím 1-4) + pool skill
        self.skill_slot_rects = {}  
        skill_slot_size = 60
        skill_slot_gap = 20
        total_skill_w = skill_slot_size * 4 + skill_slot_gap * 3
        skill_slots_start_x = panel_rect.centerx - total_skill_w // 2
        skill_slots_y = panel_rect.top + 70
        for i in range(4):
            slot_num = i + 1
            rect = pygame.Rect(
                skill_slots_start_x + i * (skill_slot_size + skill_slot_gap),
                skill_slots_y, skill_slot_size, skill_slot_size
            )
            self.skill_slot_rects[slot_num] = rect

        # Kéo-thả cho tab Skill Link
        self.dragging_skill_name = None       
        self.drag_source = None               

        # 6. TAB "CÂY KỸ NĂNG" (Skill Tree)
        self._skill_tree_node_rects = {}

    def _switch_tab(self, tab_key):
        """Đổi tab đang hiển thị, huỷ mọi trạng thái kéo-thả dở dang."""
        self.active_tab = tab_key
        self.dragging_source = None
        self.dragged_item_data = None
        self.dragging_skill_name = None
        self.drag_source = None

    def handle_event(self, event):
        # 1. Hover chuột
        if event.type == pygame.MOUSEMOTION and self.active_tab == 'bag':
            self.hovered_slot_index = -1
            for index, slot_rect in enumerate(self.grid_slots):
                if slot_rect.collidepoint(event.pos):
                    self.hovered_slot_index = index
                    break

        # 2. Click chuột trái
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.active_tab == 'bag':
                if self.equip_left_rect.collidepoint(event.pos):
                    if hasattr(self.player, 'inventory') and self.player.inventory.equipped_weapon:
                        self.dragging_source = 'equipment'
                        self.dragged_item_data = self.player.inventory.equipped_weapon

                elif self.hovered_slot_index != -1:
                    if hasattr(self.player, 'inventory'):
                        slot_data = self.player.inventory.slots[self.hovered_slot_index]
                        if slot_data:
                            self.dragging_source = self.hovered_slot_index
                            self.dragged_item_data = slot_data

            elif self.active_tab == 'skill_link':
                self._handle_skill_link_mousedown(event)

            elif self.active_tab == 'skill_tree':
                self._handle_skill_tree_click(event)

        # 3. Nhả chuột trái
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.active_tab == 'bag' and self.dragging_source is not None:
                self.process_drop(event.pos)
                self.dragging_source = None
                self.dragged_item_data = None
            elif self.active_tab == 'skill_link' and self.dragging_skill_name is not None:
                self._process_skill_drop(event.pos)
                self.dragging_skill_name = None
                self.drag_source = None

        return super().handle_event(event)

    def _handle_skill_link_mousedown(self, event):
        if event.button != 1:
            return

        mouse_pos = event.pos

        for boss_rect, skill_name in self.boss_skill_rects:
            if boss_rect.collidepoint(mouse_pos):
                self.dragging_skill_name = skill_name
                self.drag_source = 'boss_pool'
                return

        for (col_idx, row_idx), gray_rect in self.skill_link_slots.items():
            if gray_rect.collidepoint(mouse_pos):
                skill_in_slot = self.player.skill_link[col_idx][row_idx]
                if skill_in_slot:
                    self.dragging_skill_name = skill_in_slot
                    self.drag_source = (col_idx, row_idx)
                    return
                
    def _process_skill_drop(self, mouse_pos):
        if not self.dragging_skill_name:
            return

        target = None
        for (col_idx, row_idx), gray_rect in self.skill_link_slots.items():
            if gray_rect.collidepoint(mouse_pos):
                target = (col_idx, row_idx)
                break

        if target is None:
            if isinstance(self.drag_source, tuple):
                old_col, old_row = self.drag_source
                self.player.skill_link[old_col][old_row] = None
                self._shift_skills_up(old_col)
            self.dragging_skill_name = None
            self.drag_source = None
            return

        col_idx, row_idx = target

        above_skill = self.player.skill_link[col_idx][row_idx - 1] if row_idx > 0 else None
        is_dragging_from_slot_above = (
            isinstance(self.drag_source, tuple) and self.drag_source == (col_idx, row_idx - 1)
        )

        if row_idx > 0 and above_skill is None and not is_dragging_from_slot_above:
            self.dragging_skill_name = None
            self.drag_source = None
            return

        old_col = None
        for c in range(4):
            for r in range(3):
                if self.player.skill_link[c][r] == self.dragging_skill_name:
                    self.player.skill_link[c][r] = None
                    old_col = c

        self.player.skill_link[col_idx][row_idx] = self.dragging_skill_name

        if old_col is not None and old_col == col_idx:
            self._shift_skills_up(col_idx)

        self.dragging_skill_name = None
        self.drag_source = None

    def _shift_skills_up(self, col_idx):
        column = [s for s in self.player.skill_link[col_idx] if s is not None]
        while len(column) < 3:
            column.append(None)
        self.player.skill_link[col_idx] = column

    def process_drop(self, mouse_pos):
        inv = getattr(self.player, 'inventory', None)
        if not inv:
            return

        if isinstance(self.dragging_source, int):
            if self.equip_left_rect.collidepoint(mouse_pos):
                inv.equip_weapon_from_slot(self.dragging_source, self.player)
            elif self.hovered_slot_index == self.dragging_source:
                slot_data = inv.slots[self.dragging_source]
                if slot_data:
                    item_type = getattr(slot_data['item'], 'type', '')
                    if item_type == 'consumable':
                        inv.use_item_at_slot(self.dragging_source, self.player)

        elif self.dragging_source == 'equipment':
            for idx, slot_rect in enumerate(self.grid_slots):
                if slot_rect.collidepoint(mouse_pos):
                    inv.unequip_weapon(idx, self.player)
                    break

    def draw_item_render(self, surface, item_obj, amount, rect):
        item_id = item_obj.get('id') if isinstance(item_obj, dict) else getattr(item_obj, 'id', None)
        path = ITEM_DATABASE.get(item_id, {}).get('icon_path', '') if item_id else ''

        if path and os.path.exists(path):
            raw_img = pygame.image.load(path).convert_alpha()
            max_size = rect.width - 10
            img_w, img_h = raw_img.get_size()
            scale = min(max_size / img_w, max_size / img_h)
            new_size = (int(img_w * scale), int(img_h * scale))
            img = pygame.transform.smoothscale(raw_img, new_size)
            surface.blit(img, img.get_rect(center=rect.center))
        else:
            name = item_obj.get('name') if isinstance(item_obj, dict) else getattr(item_obj, 'name', '')
            name_surf = self.font.render(str(name)[:4], True, (255, 255, 255))
            surface.blit(name_surf, name_surf.get_rect(center=rect.center))

        if amount > 1:
            amt_surf = self.font.render(str(amount), True, (255, 255, 255))
            surface.blit(amt_surf, (rect.right - 14, rect.bottom - 16))

    def draw_tooltip(self, surface, item, mouse_pos):
        padding = 8
        item_name = getattr(item, 'name', item.id)
        item_type = getattr(item, 'type', 'item')
        text_str = f"{item_name} [{item_type.upper()}]"

        name_surf = self.font.render(text_str, True, (255, 255, 255))
        tt_width = name_surf.get_width() + padding * 2
        tt_height = name_surf.get_height() + padding * 2
        
        tt_rect = pygame.Rect(mouse_pos[0] + 15, mouse_pos[1] + 15, tt_width, tt_height)
        if tt_rect.right > SCREEN_WIDTH: tt_rect.right = mouse_pos[0] - 15
        if tt_rect.bottom > SCREEN_HEIGHT: tt_rect.bottom = mouse_pos[1] - 15

        pygame.draw.rect(surface, (20, 20, 20), tt_rect, border_radius=5)
        pygame.draw.rect(surface, (255, 215, 0), tt_rect, 2, border_radius=5)
        surface.blit(name_surf, (tt_rect.left + padding, tt_rect.top + padding))


    def _draw_skill_tooltip(self, surface, info, mouse_pos):
        lines = [
            info.get('name', ''),
            f"Hồi chiêu: {info.get('cooldown_turns', 0)} lượt",
            f"Năng lượng: {info.get('energy_cost', 0)}",
            f"Hệ số Dame: {info.get('damage_multiplier', 1.0)}x",
        ]
        line_surfs = [self.small_font.render(line, True, (255, 255, 255)) for line in lines]

        width = max(s.get_width() for s in line_surfs) + 16
        height = sum(s.get_height() for s in line_surfs) + 16
        tt_rect = pygame.Rect(mouse_pos[0] + 15, mouse_pos[1] + 15, width, height)

        if tt_rect.right > SCREEN_WIDTH: tt_rect.right = mouse_pos[0] - 15
        if tt_rect.bottom > SCREEN_HEIGHT: tt_rect.bottom = mouse_pos[1] - 15

        pygame.draw.rect(surface, (20, 20, 20), tt_rect, border_radius=5)
        pygame.draw.rect(surface, (255, 215, 0), tt_rect, 2, border_radius=5)

        y = tt_rect.top + 8
        for s in line_surfs:
            surface.blit(s, (tt_rect.left + 8, y))
            y += s.get_height()

    def draw(self):
        super().draw()

        if self.active_tab == 'bag':
            self._draw_bag_tab()
        elif self.active_tab == 'skill_tree':
            self._draw_skill_tree_tab()
        elif self.active_tab == 'skill_link':
            self._draw_skill_link_tab()

    def _draw_bag_tab(self):
        surface = self.display_surface
        mouse_pos = pygame.mouse.get_pos()

        pygame.draw.line(surface, (200, 0, 0), (self.mid_x, self.panel.rect.top), (self.mid_x, self.panel.rect.bottom), 3)

        if hasattr(self.player, 'image'):
            scaled_img = pygame.transform.scale(self.player.image, (96, 96))
            img_rect = scaled_img.get_rect(center=(self.panel.rect.left + (self.width // 4), self.panel.rect.top + (self.height // 2) - 40))
            surface.blit(scaled_img, img_rect)

        # RENDER GOLD BADGE
        gold_amount = getattr(self.player, 'gold', 0)
        gold_text = f"{gold_amount:,} Gold"  
        gold_surf = self.font.render(gold_text, True, (255, 215, 0)) 
        
        gold_rect = gold_surf.get_rect(center=(self.panel.rect.left + (self.width // 4), self.panel.rect.top + (self.height // 2) + 50))
        bg_badge = gold_rect.inflate(24, 12)
        shadow_badge = bg_badge.move(3, 3)

        pygame.draw.rect(surface, (10, 10, 10), shadow_badge, border_radius=6) 
        pygame.draw.rect(surface, (30, 30, 35), bg_badge, border_radius=6)     
        pygame.draw.rect(surface, (255, 215, 0), bg_badge, width=2, border_radius=6) 
        
        surface.blit(gold_surf, gold_rect)

        # Equipment Slots
        pygame.draw.rect(surface, (255, 215, 0), self.equip_left_rect, 3)
        pygame.draw.rect(surface, (255, 255, 255), self.equip_right_rect, 3)

        hovered_item = None

        if hasattr(self.player, 'inventory') and self.player.inventory.equipped_weapon:
            if self.dragging_source != 'equipment':
                eq_item = self.player.inventory.equipped_weapon['item']
                self.draw_item_render(surface, eq_item, 1, self.equip_left_rect)
                if self.equip_left_rect.collidepoint(mouse_pos):
                    hovered_item = eq_item

        # Grid Inventory Slots
        for index, slot_rect in enumerate(self.grid_slots):
            is_hovered = (index == self.hovered_slot_index)
            border_color = (255, 215, 0) if is_hovered else (0, 0, 0)
            border_width = 4 if is_hovered else 3

            pygame.draw.rect(surface, border_color, slot_rect, border_width)

            if hasattr(self.player, 'inventory') and index < len(self.player.inventory.slots):
                slot_data = self.player.inventory.slots[index]
                if slot_data and self.dragging_source != index:
                    item = slot_data['item']
                    if is_hovered:
                        hovered_item = item

                    self.draw_item_render(surface, item, slot_data['amount'], slot_rect)

        # Items Drag & Drop Rendering
        if self.dragged_item_data:
            drag_rect = pygame.Rect(0, 0, self.slot_size, self.slot_size)
            drag_rect.center = mouse_pos
            pygame.draw.rect(surface, (255, 215, 0), drag_rect, 2)
            self.draw_item_render(surface, self.dragged_item_data['item'], self.dragged_item_data['amount'], drag_rect)

        # Tooltip
        if hovered_item and not self.dragged_item_data:
            self.draw_tooltip(surface, hovered_item, mouse_pos)

    def _compute_skill_tree_layout(self):
        panel = self.panel.rect
        node_size = 40
        tier_gap_y = 78
        leaf_gap_x = 22

        children_map = {}
        for node_id, node in skill_tree_data.items():
            parent = node.get('parent')
            children_map.setdefault(parent, []).append(node_id)

        leaf_ids = [nid for nid in skill_tree_data if not children_map.get(nid)]
        leaf_count = max(len(leaf_ids), 1)
        total_leaf_width = leaf_count * node_size + (leaf_count - 1) * leaf_gap_x

        start_x = panel.centerx - total_leaf_width // 2 + node_size // 2

        positions = {}
        next_leaf_x = [start_x]

        def layout(node_id, depth):
            children = children_map.get(node_id, [])
            if not children:
                x = next_leaf_x[0]
                next_leaf_x[0] += node_size + leaf_gap_x
            else:
                child_xs = [layout(child_id, depth + 1) for child_id in children]
                x = sum(child_xs) / len(child_xs)
            y = panel.top + 65 + depth * tier_gap_y
            positions[node_id] = (x, y)
            return x

        layout('root', 0)
        return positions, node_size

    def _handle_skill_tree_click(self, event):
        for node_id, rect in self._skill_tree_node_rects.items():
            if rect.collidepoint(event.pos):
                success, message = self.player.unlock_skill_node(node_id)
                print(f"[SKILL TREE]: {message}")
                return

    def _draw_skill_tree_tooltip(self, surface, node, node_id, mouse_pos):
        is_unlocked = node_id in self.player.unlocked_skill_nodes
        lines = [node.get('name', node_id)]
        if node.get('description'):
            lines.append(node['description'])
        if node_id != 'root':
            lines.append("Đã mở khoá" if is_unlocked else f"Chi phí: {node.get('cost', 0)} skills point")

        line_surfs = [self.small_font.render(line, True, (255, 255, 255)) for line in lines]
        width = max(s.get_width() for s in line_surfs) + 16
        height = sum(s.get_height() for s in line_surfs) + 16
        tt_rect = pygame.Rect(mouse_pos[0] + 15, mouse_pos[1] + 15, width, height)

        if tt_rect.right > SCREEN_WIDTH: tt_rect.right = mouse_pos[0] - 15
        if tt_rect.bottom > SCREEN_HEIGHT: tt_rect.bottom = mouse_pos[1] - 15

        pygame.draw.rect(surface, (20, 20, 20), tt_rect, border_radius=5)
        pygame.draw.rect(surface, (255, 215, 0), tt_rect, 2, border_radius=5)

        y = tt_rect.top + 8
        for s in line_surfs:
            surface.blit(s, (tt_rect.left + 8, y))
            y += s.get_height()

    def _draw_skill_tree_tab(self):
        surface = self.display_surface
        mouse_pos = pygame.mouse.get_pos()
        panel = self.panel.rect

        title_surf = self.font.render("Skill Tree", True, (255, 255, 255))
        surface.blit(title_surf, (panel.left + 20, panel.top + 20))

        points_surf = self.font.render(f"Skills point: {self.player.skill_points}", True, (255, 215, 0))
        surface.blit(points_surf, (panel.right - points_surf.get_width() - 20, panel.top + 50))

        positions, node_size = self._compute_skill_tree_layout()
        self._skill_tree_node_rects = {}

        for node_id, node in skill_tree_data.items():
            parent_id = node.get('parent')
            if parent_id and parent_id in positions:
                px, py = positions[parent_id]
                cx, cy = positions[node_id]
                unlocked = node_id in self.player.unlocked_skill_nodes
                line_color = (255, 215, 0) if unlocked else (100, 85, 60)
                pygame.draw.line(surface, line_color,
                                  (px, py + node_size // 2), (cx, cy - node_size // 2), 2)

        hovered_node = None
        for node_id, (x, y) in positions.items():
            node = skill_tree_data[node_id]
            rect = pygame.Rect(0, 0, node_size, node_size)
            rect.center = (x, y)
            self._skill_tree_node_rects[node_id] = rect

            is_unlocked = node_id in self.player.unlocked_skill_nodes
            parent_id = node.get('parent')
            is_available = (parent_id is None) or (parent_id in self.player.unlocked_skill_nodes)

            if is_unlocked:
                bg_color, border_color = (70, 130, 60), (255, 215, 0)
            elif is_available:
                bg_color, border_color = (60, 60, 45), (200, 170, 90)
            else:
                bg_color, border_color = (35, 35, 35), (80, 80, 80)

            pygame.draw.rect(surface, bg_color, rect, border_radius=6)
            pygame.draw.rect(surface, border_color, rect, 2, border_radius=6)

            text_color = (255, 255, 255) if (is_unlocked or is_available) else (120, 120, 120)
            label_surf = self.icon_font.render(node.get('name', node_id)[:2], True, text_color)
            surface.blit(label_surf, label_surf.get_rect(center=rect.center))

            if rect.collidepoint(mouse_pos):
                hovered_node = node_id

        if hovered_node:
            self._draw_skill_tree_tooltip(surface, skill_tree_data[hovered_node], hovered_node, mouse_pos)

    def _draw_skill_link_tab(self):
        """Tab Liên Kết Kỹ Năng: Hiển thị 4 cột cây skill và Kho chứa skill boss."""
        surface = self.display_surface
        mouse_pos = pygame.mouse.get_pos()
        panel = self.panel.rect

        slot_size = 50
        gap_y = 15
        gap_x = 20
        col_width = 80
        col_height = 4 * slot_size + 3 * gap_y + 20

        start_x = panel.left + 30
        start_y = panel.top + 40

        self.skill_link_slots = {}
        self.boss_skill_rects = []

        unlocked_skills = [s for s in skill_data.keys() if s in getattr(self.player, 'unlocked_active_skills', set())]

        if not hasattr(self.player, 'skill_link'):
            self.player.skill_link = [[None for _ in range(3)] for _ in range(4)]

        # Lấy danh sách tất cả các skill đã được gắn vào Skill Link
        equipped_in_link = set()
        for c in range(4):
            for r in range(3):
                if self.player.skill_link[c][r]:
                    equipped_in_link.add(self.player.skill_link[c][r])

        # 1. VẼ 4 CỘT SKILL
        for col_idx in range(4):
            slot_num = col_idx + 1
            col_x = start_x + col_idx * (col_width + gap_x)

            col_rect = pygame.Rect(col_x, start_y, col_width, col_height)
            pygame.draw.rect(surface, (0, 150, 255), col_rect, 3)

            # --- Ô VÀNG ---
            yellow_x = col_x + (col_width - slot_size) // 2
            yellow_y = start_y + 10
            yellow_rect = pygame.Rect(yellow_x, yellow_y, slot_size, slot_size)

            pygame.draw.rect(surface, (60, 50, 20), yellow_rect)
            pygame.draw.rect(surface, (255, 215, 0), yellow_rect, 3)

            # KIỂM TRA FUSION SKILL
            column_skills = [s for s in self.player.skill_link[col_idx] if s is not None]
            fused_skill = None
            if hasattr(self.player, 'skill_manager'):
                fused_skill = self.player.skill_manager.check_skill_fusion(column_skills)

            if fused_skill:
                active_skill = fused_skill
            elif column_skills:
                active_skill = column_skills[0]
            else:
                active_skill = None

            self.player.skill_slots[slot_num] = active_skill

            if active_skill:
                info = skill_data.get(active_skill, {})
                # 🟢 Gọi hàm get_skill_icon chuẩn từ support.py
                icon = get_skill_icon(active_skill, info, yellow_rect.width, self.font)
                surface.blit(icon, icon.get_rect(center=yellow_rect.center))
                if yellow_rect.collidepoint(mouse_pos):
                    self._draw_skill_tooltip(surface, info, mouse_pos)
            else:
                text_surf = self.font.render(f"skill {slot_num}", True, (255, 215, 0))
                surface.blit(text_surf, text_surf.get_rect(center=yellow_rect.center))

            # --- 3 Ô XÁM XẾP DỌC ---
            prev_center = yellow_rect.center
            for row_idx in range(3):
                gray_y = yellow_y + (row_idx + 1) * (slot_size + gap_y)
                gray_rect = pygame.Rect(yellow_x, gray_y, slot_size, slot_size)

                self.skill_link_slots[(col_idx, row_idx)] = gray_rect

                # Đường nối
                pygame.draw.line(surface, (0, 0, 0), (prev_center[0], prev_center[1] + slot_size//2), (gray_rect.centerx, gray_rect.top), 4)
                prev_center = gray_rect.center

                is_unlocked_slot = (row_idx == 0) or (self.player.skill_link[col_idx][row_idx - 1] is not None)

                bg_color = (45, 45, 50) if is_unlocked_slot else (25, 25, 30)
                border_color = (120, 120, 130) if is_unlocked_slot else (60, 60, 70)
                pygame.draw.rect(surface, bg_color, gray_rect)
                pygame.draw.rect(surface, border_color, gray_rect, 2)

                current_skill = self.player.skill_link[col_idx][row_idx]
                if current_skill:
                    is_dragging = (self.dragging_skill_name == current_skill and getattr(self, 'drag_source', None) == (col_idx, row_idx))
                    if not is_dragging:
                        info = skill_data.get(current_skill, {})
                        # 🟢 Gọi hàm get_skill_icon chuẩn từ support.py
                        icon = get_skill_icon(current_skill, info, slot_size, self.font)
                        surface.blit(icon, icon.get_rect(center=gray_rect.center))
                        if gray_rect.collidepoint(mouse_pos):
                            self._draw_skill_tooltip(surface, info, mouse_pos)

        # 2. KHO SKILL BÊN PHẢI
        divider_x = start_x + 4 * (col_width + gap_x) + 10
        pygame.draw.line(surface, (150, 150, 150), (divider_x, panel.top + 20), (divider_x, panel.bottom - 20), 3)

        right_title_1 = self.font.render("Skills", True, (255, 255, 255))
        surface.blit(right_title_1, (divider_x + 20, start_y))

        grid_start_x = divider_x + 25
        grid_start_y = start_y + 65
        grid_cols = 3

        for i, skill_name in enumerate(unlocked_skills):
            r = i // grid_cols
            c = i % grid_cols
            bx = grid_start_x + c * (slot_size + 12)
            by = grid_start_y + r * (slot_size + 12)
            boss_rect = pygame.Rect(bx, by, slot_size, slot_size)

            self.boss_skill_rects.append((boss_rect, skill_name))

            is_equipped = skill_name in equipped_in_link
            bg_col = (20, 20, 25) if is_equipped else (40, 40, 45)
            border_col = (60, 60, 70) if is_equipped else (100, 100, 110)

            pygame.draw.rect(surface, bg_col, boss_rect)
            pygame.draw.rect(surface, border_col, boss_rect, 2)

            is_dragging = (self.dragging_skill_name == skill_name and getattr(self, 'drag_source', None) == 'boss_pool')
            if not is_dragging:
                info = skill_data.get(skill_name, {})
                # 🟢 Gọi hàm get_skill_icon chuẩn từ support.py
                icon = get_skill_icon(skill_name, info, slot_size, self.font)
                
                if is_equipped:
                    icon = icon.copy()
                    icon.set_alpha(80)

                surface.blit(icon, icon.get_rect(center=boss_rect.center))
                if boss_rect.collidepoint(mouse_pos):
                    self._draw_skill_tooltip(surface, info, mouse_pos)

        # 3. SKILL ĐANG KÉO DƯỚI CON TRỎ CHUỘT
        if self.dragging_skill_name:
            drag_rect = pygame.Rect(0, 0, slot_size, slot_size)
            drag_rect.center = mouse_pos
            info = skill_data.get(self.dragging_skill_name, {})
            # 🟢 Gọi hàm get_skill_icon chuẩn từ support.py
            icon = get_skill_icon(self.dragging_skill_name, info, slot_size, self.font)
            pygame.draw.rect(surface, (255, 215, 0), drag_rect, 2)
            surface.blit(icon, icon.get_rect(center=drag_rect.center))

