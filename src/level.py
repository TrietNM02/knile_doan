import pygame
from settings import *
from player import Player
from sprites import Generic, Tree
from enemy import Enemy
from pytmx.util_pygame import load_pygame
from ui import UI
from ui_system import UIManager
from overlay import InventoryOverlay, SettingsOverlay

class Level:
    def __init__(self):

        # display surface
        self.display_surface = pygame.display.get_surface()
        self.current_time_of_day = 'noon'

        # setup sprites
        self.all_sprites = CameraGroup()
        self.collision_sprites = pygame.sprite.Group()
        self.tree_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()

        self.setup()

        # user interface
        self.ui = UI()

        # 🟢 Tạo UIManager Chuyên Nghiệp
        self.ui_manager = UIManager()
        self.ui_manager.register('inventory', InventoryOverlay(self.ui_manager, self.player))
        self.ui_manager.register('settings', SettingsOverlay(self.ui_manager))


    def setup(self):
        tmx_data = load_pygame('../data/map.tmx')

        for obj in tmx_data.get_layer_by_name('Decoration'):
            if obj.image:
                Generic(
                    pos = (obj.x, obj.y),
                    surf = obj.image,
                    groups = [self.all_sprites, self.collision_sprites]
                    )
            else:
                pass
        
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

        # Slime
        for obj in tmx_data.get_layer_by_name('Enemy'):
                monster_name = obj.name.lower()
                enemy = Enemy(
                    monster_name = monster_name,
                    pos = (obj.x, obj.y),
                    groups = [self.all_sprites, self.enemy_sprites],
                    collision_sprites = self.collision_sprites,
                    player = self.player
                )
                self.collision_sprites.add(enemy)
 
        Generic(
            pos = (0, 0), 
            surf = pygame.image.load('../assets/world/ground.png').convert_alpha(),
            groups = self.all_sprites,
            z = LAYERS['ground'])


    def check_enemy_turns(self):
        """Hàm quét qua toàn bộ quái vật và bắt chúng di chuyển sau khi Player đi xong"""
        for enemy in self.enemy_sprites.sprites():
            if enemy.alive and not enemy.is_moving:
                enemy.take_turn()

    def handle_event(self, event):
        # 1. ƯU TIÊN CHECK PHÍM TOGGLE (Mở / Đóng) TRƯỚC
        if event.type == pygame.KEYDOWN:
            # Bấm E: Nếu đang mở Inventory -> Đóng. Nếu chưa -> Mở Inventory
            if event.key == pygame.K_e:
                if self.ui_manager.is_menu_open() and isinstance(self.ui_manager.stack[-1], InventoryOverlay):
                    self.ui_manager.close_top()
                else:
                    self.ui_manager.open('inventory')
                return # Đã xử lý xong phím E

            # Bấm ESC: Đóng Menu hiện tại (nếu đang mở) hoặc Mở Settings
            elif event.key == pygame.K_ESCAPE:
                if self.ui_manager.is_menu_open():
                    self.ui_manager.close_top()
                else:
                    self.ui_manager.open('settings')
                return # Đã xử lý xong phím ESC

        # 2. BẤM CÁC NÚT KHÁC (Hover, Click chuột vào nút 'X', kéo thả...): Mới đưa cho UI xử lý
        self.ui_manager.handle_event(event)

    def end_player_turn(self):
        for enemy in self.enemy_sprites.sprites():
            if enemy.alive:
                enemy.take_turn()

    def run(self, dt):

        self.display_surface.fill('black')
        if not self.ui_manager.is_menu_open():
            self.all_sprites.update(dt) # Chỉ update World khi không mở Menu
            
        self.all_sprites.custom_draw(self.player)
        self.ui.display(self.player)

        # 🟢 Vẽ UI Manager (Đè lên tất cả)
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
            for sprite in sorted(self.sprites(), key = lambda sprite: sprite.rect.bottom):
                if sprite.z == layer:
                    offset_rect = sprite.rect.copy()
                    offset_rect.center -= self.offset
                    self.display_surface.blit(sprite.image, offset_rect)


                    if hasattr(sprite, 'hitbox'):
                        hitbox_offset_rect = sprite.hitbox.copy()
                        hitbox_offset_rect.center -= self.offset
                        pygame.draw.rect(self.display_surface, 'red', hitbox_offset_rect, 2)
                        
        interaction_pos = player.get_interaction_pos() 
        interaction_offset_pos = interaction_pos - self.offset
        pygame.draw.circle(self.display_surface, 'blue', (round(interaction_offset_pos.x), round(interaction_offset_pos.y)), 5)

        if hasattr(player, 'debug_lance_rect') and player.debug_lance_rect:
            # 1. Tạo một bản sao của hitbox thương để tránh làm hỏng dữ liệu gốc
            lance_offset_rect = player.debug_lance_rect.copy()
            
            # 2. Trừ đi offset của Camera để đưa về tọa độ màn hình thực tế
            lance_offset_rect.topleft -= self.offset
            
            # 3. Vẽ hitbox đã được xử lý offset lên màn hình
            pygame.draw.rect(self.display_surface, (255, 0, 0), lance_offset_rect, 2)

    
