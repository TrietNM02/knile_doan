import pygame
from untils.settings import *
from untils.spritesheet import load_spritesheet
from untils.npc_data import NPC_DATA

class NPC(pygame.sprite.Sprite):
    def __init__(self, npc_id, pos, groups, surf=None):
        super().__init__(groups)
        
        self.npc_id = npc_id
        self.config = NPC_DATA.get(npc_id, {})
        
        self.name = self.config.get('name', 'NPC')
        self.sprite_type = 'npc'
        self.z = LAYERS['main']

        # Thông số Animation & Scale
        self.npc_size = self.config.get('npc_size', 48)
        self.scale = self.config.get('scale', 2) # Scale về 0.25 cho ảnh 192x192
        
        self.frame_index = 0
        self.animation_speed = 0.15
        self.status = 'idle'
        self.animations_dict = {}

        # Load hình ảnh / Spritesheet
        animation_config = self.config.get('animation_config', None)
        is_single_sheet = self.config.get('is_single_sheet', True)

        if animation_config:
            self.import_spritesheet(is_single_sheet, animation_config)
            self.image = self.animations_dict[self.status][self.frame_index]
        elif surf:
            self.image = surf
        else:
            self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
            self.image.fill('yellow')

        # Tọa độ Hitbox chuẩn ô Grid
        self.hitbox = pygame.Rect(0, 0, TILE_SIZE, TILE_SIZE)
        self.hitbox.topleft = pos
        
        # 🟢 Căn center của hình đè đúng center của Hitbox
        self.rect = self.image.get_rect(center=self.hitbox.center)

        # Inventory
        self.inventory = self.config.get('shop_inventory', [])

    def import_spritesheet(self, is_single_sheet, animation_config):
        base_path = f'../assets/characters/npcs/{self.npc_id}/'
        
        for action, (row_index, total_frames) in animation_config.items():
            full_path = f"{base_path}{action}.png"
            try:
                raw_image = pygame.image.load(full_path).convert_alpha()
                temp_img_list = []
                for frame_index in range(total_frames):
                    # Truyền self.scale trực tiếp vào load_spritesheet
                    frame_surf = load_spritesheet(raw_image, self.npc_size, self.npc_size, row_index, frame_index, self.scale)
                    temp_img_list.append(frame_surf)
                    
                self.animations_dict[action] = temp_img_list
            except FileNotFoundError:
                print(f"[NPC Error] Thiếu file ảnh tại: {full_path}")

    def animate(self, dt):
        if self.status in self.animations_dict:
            current_animation = self.animations_dict[self.status]
            self.frame_index += self.animation_speed * dt * 60
            if self.frame_index >= len(current_animation):
                self.frame_index = 0
            
            self.image = current_animation[int(self.frame_index)]

            # Căn chân nhân vật vừa với đít hitbox
            self.rect.center = self.hitbox.center

    def interact(self):
        text = f"[{self.name.upper()}]: Chào buổi sáng! Hôm nay bạn muốn mua gì nào?"
        print(text)
        return text

    def update(self, dt):
        self.animate(dt)