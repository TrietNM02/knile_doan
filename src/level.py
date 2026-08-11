import pygame
from settings import *
from support import *
from player import Player
from sprites import Generic, WaterFoam, Tree
from enemy import Enemy
from boss import Boss
from npc import NPC
from pytmx.util_pygame import load_pygame
from ui import UI
from ui_system import UIManager
from inventory_overlay import InventoryOverlay
from settings_overlay import SettingsOverlay, OptionsOverlay
from dialog import DialogBox
from shop_overplay import ShopOverlay


class Level:
    def __init__(self, game):

        self.game = game
        # display surface
        self.display_surface = pygame.display.get_surface()

        # particles
        self.explosion_frames = load_particle_frames()

        # setup sprites
        self.all_sprites = CameraGroup()
        self.collision_sprites = pygame.sprite.Group()
        self.tree_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()
        self.npc_sprites = pygame.sprite.Group()

        self.player = None

        self.setup()

        # user interface
        self.ui = UI()

        # 🟢 Tạo UIManager 
        self.ui_manager = UIManager()
        self.ui_manager.level = self  # 🟢 Gán thẳng level vào UIManager (để Save/Load dễ dàng)
        
        if self.player:
            self.ui_manager.player = self.player
            self.ui_manager.register('inventory', InventoryOverlay(self.ui_manager, self.player))

            # 🟢 Register thêm Shop Overlay vào UIManager
            self.shop_overlay = ShopOverlay(self.ui_manager, self.player)
            self.ui_manager.register('shop', self.shop_overlay)
        
        self.ui_manager.register('settings', SettingsOverlay(self.ui_manager))
        self.ui_manager.register('options', OptionsOverlay(self.ui_manager))

        self.dialog_box = DialogBox()

        self.current_day = 0

        

    def setup(self):
        tmx_data = load_pygame('../data/map.tmx')


        for obj in tmx_data.get_layer_by_name('Decoration'):
            if obj.image:
                Generic(
                    pos = (obj.x, obj.y),
                    surf = obj.image,
                    groups = [self.all_sprites, self.collision_sprites]
                    )

        # Collision (Chặn va chạm tàng hình)
        if 'Collision' in tmx_data.layernames:
            for x, y, surf in tmx_data.get_layer_by_name('Collision').tiles():
                Generic(
                    pos = (x * TILE_SIZE, y * TILE_SIZE), 
                    surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA), # Surface rỗng tàng hình
                    groups = self.collision_sprites # CHỈ cho vào collision_sprites!
                )

        # Water
        if 'Water' in tmx_data.layernames:
            for x, y, surf in tmx_data.get_layer_by_name('Water').tiles():
                Generic(
                    pos = (x * TILE_SIZE, y * TILE_SIZE),
                    surf = surf,
                    groups = self.all_sprites,
                    z = LAYERS['water']
                )

        # Water Foam
        if 'Water Foam' in tmx_data.layernames:
            foam_info = {
                        "frame_width": 144,
                        "frame_height": 144,
                        "cols": 16,
                        "rows": 1,
                        "total_frames": 16,
                        "scale": 1.0
                    }
            foam_frames = load_effect_frames('../assets/world/tileset/Water Foam.png', foam_info)
            for x, y, surf in tmx_data.get_layer_by_name('Water Foam').tiles():
                WaterFoam(
                    pos = (x * TILE_SIZE, y * TILE_SIZE),
                    frames = foam_frames,
                    groups = self.all_sprites
                )

        # Elevated
        if 'Elevated' in tmx_data.layernames:
            for x, y, surf in tmx_data.get_layer_by_name('Elevated').tiles():
                Generic(
                    pos = (x * TILE_SIZE, y * TILE_SIZE),
                    surf = surf,
                    groups = self.all_sprites,
                    z = LAYERS['floor']
                )

        # Rock Water
        if 'Rock Water' in tmx_data.layernames:
            for x, y, surf in tmx_data.get_layer_by_name('Rock Water').tiles():
                Generic(
                    pos = (x * TILE_SIZE, y * TILE_SIZE),
                    surf = surf,
                    groups = self.all_sprites,
                    z = LAYERS['floor']
                )
        
        for obj in tmx_data.get_layer_by_name('Trees'):
            if obj.image:
                Tree(
                    pos = (obj.x, obj.y), 
                    surf = obj.image,
                    groups = [self.all_sprites, self.collision_sprites, self.tree_sprites])
            else:
                pass

        # Entity

        # Player
        for obj in tmx_data.get_layer_by_name('Player'):
            if obj.name == 'Player':
                self.player = Player(
                    pos = (obj.x, obj.y), 
                    group = self.all_sprites, 
                    collision_sprites = self.collision_sprites, 
                    tree_sprites = self.tree_sprites,
                    enemy_sprites = self.enemy_sprites
                    )
                self.player.level = self
                self.collision_sprites.add(self.player)

        if 'NPC' in tmx_data.layernames:
            for obj in tmx_data.get_layer_by_name('NPC'):
                npc_id = obj.name.lower()
                npc_sprite = NPC(
                    npc_id=npc_id,
                    pos=(obj.x, obj.y),
                    groups=[self.all_sprites, self.collision_sprites, self.npc_sprites],
                )

        # Enemy
        self.spawn_points = []  # Danh sách lưu trữ điểm spawn quái vật
        if 'Enemy' in tmx_data.layernames:
            for obj in tmx_data.get_layer_by_name('Enemy'):
                monster_name = obj.name.lower()
                pos = (obj.x, obj.y)

                if 'boss' in monster_name:
                    # BOSS CHỈ SPAWN 1 LẦN DUY NHẤT LÚC ĐẦU GAME
                    Boss(
                        monster_name=monster_name,
                        pos=pos,
                        groups=[self.all_sprites, self.enemy_sprites],
                        collision_sprites=self.collision_sprites,
                        player=self.player,
                        explosion_frames=self.explosion_frames
                    )
                else:
                    # QUÁI THƯỜNG: Lưu lại điểm spawn để qua ngày mới hồi sinh
                    self.spawn_points.append({
                        'name': monster_name,
                        'pos': pos
                    })
        self.respawn_enemies()  # Gọi hàm respawn quái vật khi setup level
 
        Generic(
            pos = (0, 0), 
            surf = pygame.image.load('../assets/world/ground_grid.png').convert_alpha(),
            groups = self.all_sprites,
            z = LAYERS['ground'])

    def respawn_enemies(self):
        # 1. Xóa các quái THƯỜNG cũ còn sống trên map (Giữ lại Boss)
        for enemy in self.enemy_sprites.sprites():
            if not isinstance(enemy, Boss):
                enemy.kill()


        for spawn_point in self.spawn_points:
            monster_name = spawn_point['name']
            pos = spawn_point['pos']
            enemy = Enemy(
                monster_name=monster_name,
                pos=pos,
                groups=[self.all_sprites, self.enemy_sprites],
                collision_sprites=self.collision_sprites,
                player=self.player,
                explosion_frames=self.explosion_frames
            )
            self.collision_sprites.add(enemy)  # Thêm quái vật mới vào nhóm va chạm
            
    def check_enemy_turns(self):
        """Hàm quét qua toàn bộ quái vật và bắt chúng di chuyển sau khi Player đi xong"""
        for enemy in self.enemy_sprites.sprites():
            if enemy.alive and not enemy.is_moving:
                enemy.take_turn()

    def check_npc_interaction(self):
        if not self.player:
            return None

        # Quét NPC gần Player để tương tác
        interaction_rect = self.player.rect.inflate(60, 60)
        for npc in self.npc_sprites:
            if npc in self.all_sprites:  # Chỉ kiểm tra những NPC đang hiển thị trên map
                if interaction_rect.colliderect(npc.rect) or interaction_rect.colliderect(npc.hitbox):
                    if not self.dialog_box.active:
                        dialog_text = npc.interact()
                        self.dialog_box.show(dialog_text, npc)
                    return npc
                
        return None

    def handle_event(self, event):
        # 1. Nếu đang ngắm Skill (Aiming) -> Nhường sự kiện Click Chuột / ESC cho SkillManager xử lý trước!
        if hasattr(self, 'player') and self.player.skill_manager.is_aiming:
            # Truyền Camera Offset để tính đúng tọa độ ô chuột trên map
            camera_offset = self.all_sprites.offset
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                # Xả chiêu hoặc Hủy chiêu
                if self.player.skill_manager.handle_input(camera_offset):
                    return # Đã xử lý xong Skill, không làm gì thêm

        # 2. CHECK PHÍM TOGGLE MENU (E / ESC)
        if event.type == pygame.KEYDOWN:
            # 🟢 BẤM F ĐỂ NÓI CHUYỆN VỚI NPC
            if event.key == pygame.K_f:
                target_npc = self.check_npc_interaction() # Lấy NPC từ hàm check
                if target_npc:
                    self.shop_overlay.set_npc(target_npc) # Gán đúng NPC vào Shop
                    self.ui_manager.open('shop')          # Mở Shop Overlay
                return
            
            if event.key == pygame.K_e:
                if self.ui_manager.is_menu_open() and isinstance(self.ui_manager.stack[-1], InventoryOverlay):
                    self.ui_manager.close_top()
                else:
                    self.ui_manager.open('inventory')
                return

            elif event.key == pygame.K_ESCAPE:
                if self.ui_manager.is_menu_open():
                    self.ui_manager.close_top()
                else:
                    self.ui_manager.open('options')
                return

        # 3. UI Manager xử lý các nút bấm giao diện
        self.ui_manager.handle_event(event)

    def end_player_turn(self):
        for enemy in self.enemy_sprites.sprites():
            if enemy.alive:
                enemy.take_turn()

    def update_day_night_cycle(self):
        day_length = 100  # Ông thích ngày dài bao nhiêu bước thì chỉnh ở đây (ví dụ 100 bước)
        steps_in_day = int(self.player.steps) % day_length

        # 🟢 VÍ DỤ: 50 bước đầu là Buổi Sáng, sau 50 bước là Buổi Khác
        is_morning = steps_in_day < 50 

        # 🟢 CHỈ XỬ LÝ ẨN/HIỆN KHI CẦN THIẾT (Tránh lặp vô tận gây lag)
        for npc in self.npc_sprites:
            if is_morning and npc not in self.all_sprites:
                self.all_sprites.add(npc)
                self.collision_sprites.add(npc)
            elif not is_morning and npc in self.all_sprites:
                self.all_sprites.remove(npc)
                self.collision_sprites.remove(npc)

        # Chuyển ngày & hồi sinh quái giữ nguyên
        day = int(self.player.steps) // day_length
        if day > self.current_day:
            self.current_day = day
            self.respawn_enemies()

    def run(self, dt):

        self.update_day_night_cycle()  # Cập nhật chu kỳ ngày/đêm và respawn quái

        self.display_surface.fill('black')
        if not self.ui_manager.is_menu_open():
            self.all_sprites.update(dt) # Chỉ update World khi không mở Menu

            self.check_npc_interaction()  # Quét NPC gần Player để bật thoại tự
            
        self.all_sprites.custom_draw(self.player)
        self.ui.display(self.player)

        # 🟢 VẼ PREVIEW SKILL: Dùng offset từ self.all_sprites
        self.player.skill_manager.draw_preview(self.display_surface, self.all_sprites.offset)

        # 🟢 Vẽ bong bóng thoại ngay trên đầu NPC theo offset camera
        self.dialog_box.update()  # Cập nhật Timer đếm ngược
        self.dialog_box.draw(self.all_sprites.offset)

        # Vẽ UI Manager (Đè lên tất cả)
        self.ui_manager.update(dt)
        self.ui_manager.draw()


class CameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.offset = pygame.math.Vector2()

    def custom_draw(self, player):
        self.offset.x = player.rect.centerx - SCREEN_WIDTH / 2
        self.offset.y = player.rect.centery - SCREEN_HEIGHT / 2
        for layer in LAYERS.values():
            # 🟢 2. CHÈN VÀO ĐÂY: Vẽ ô màu đỏ cảnh báo (Nằm DƯỚI chân)
            for sprite in self.sprites():
                if hasattr(sprite, 'draw_warning_hitbox'):
                    sprite.draw_warning_hitbox(self.display_surface, self.offset)
                    
            for sprite in sorted(self.sprites(), key = lambda sprite: sprite.rect.bottom):
                if sprite.z == layer:
                    offset_rect = sprite.rect.copy()
                    offset_rect.center -= self.offset
                    self.display_surface.blit(sprite.image, offset_rect)

                    # VẼ HITBOX DEBUG
        #             if hasattr(sprite, 'hitbox'):
        #                 hitbox_offset_rect = sprite.hitbox.copy()
        #                 hitbox_offset_rect.center -= self.offset
        #                 pygame.draw.rect(self.display_surface, 'red', hitbox_offset_rect, 2)
                        
        # interaction_pos = player.get_interaction_pos() 
        # interaction_offset_pos = interaction_pos - self.offset
        # pygame.draw.circle(self.display_surface, 'blue', (round(interaction_offset_pos.x), round(interaction_offset_pos.y)), 5)

        # if hasattr(player, 'debug_lance_rect') and player.debug_lance_rect:
        #     # 1. Tạo một bản sao của hitbox thương để tránh làm hỏng dữ liệu gốc
        #     lance_offset_rect = player.debug_lance_rect.copy()
            
        #     # 2. Trừ đi offset của Camera để đưa về tọa độ màn hình thực tế
        #     lance_offset_rect.topleft -= self.offset
            
        #     # 3. Vẽ hitbox đã được xử lý offset lên màn hình
        #     pygame.draw.rect(self.display_surface, (255, 0, 0), lance_offset_rect, 2)

    
