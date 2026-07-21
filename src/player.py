import pygame

from settings import *

from spritesheet import load_spritesheet
from timers    import Timer
from entity    import Entity
from weapon    import Weapon
from item      import Item
from inventory import Inventory


class Player(Entity):
    def __init__(self, pos, group, collision_sprites, tree_sprites, enemy_sprites):
        super().__init__(group)

        # animation
        self.state = 'idle'
        self.facing = 'down'
        self.action = f'{self.state}_{self.facing}'
        self.flip = False
        self.import_spritesheet()

        self.image = self.animations_dict[self.action][self.frame]
        self.rect = self.image.get_rect(center = pos)
        self.z = LAYERS['main']

        # collision & Grid setup
        self.tile_size = 48
        self.hitbox = pygame.Rect(0, 0, 36, 36)
        self.hitbox.center = pos
        
        # Đồng bộ rect (hình ảnh) khớp với đáy của hitbox
        self.rect.centerx = self.hitbox.centerx
        self.rect.bottom = self.hitbox.bottom
        
        self.collision_sprites = collision_sprites
        self.pos = pygame.math.Vector2(self.hitbox.center)

        # moving
        self.is_moving = False
        self.target_pos = pygame.math.Vector2(self.pos)

        # Timer
        self.timers = {
            'weapon use': Timer(200, self.weapon_use), # Giảm timer xuống để đòn đánh dứt khoát hơn
            'weapon switch': Timer(250),
            'turn_cooldown': Timer(150),
        }

        # weapons
        self.weapons = ['sword', 'lance', 'axe']
        self.weapon_index = 0
        self.selected_weapon = self.weapons[self.weapon_index]
        self.can_switch_weapon = True

        # interaction
        self.attacking = False
        self.tree_sprites = tree_sprites
        self.enemy_sprites = enemy_sprites
        self.level = None

        # stats
        self.stats = {
            'health': 100,
            'energy': 60,
            'attack': 10,
            'magic': 4,
            'speed': 300 # Đẩy tốc độ trượt ô lên 300 cho mượt chuẩn OneBit
        }
        self.health = self.stats['health'] * 0.5
        self.energy = self.stats['energy'] * 0.8
        self.exp = 123

        # inventory
        self.inventory = Inventory(total_slots=16)
        self.add_item('potion_red', 2)

    def weapon_use(self):
        if self.selected_weapon == 'sword':
            interaction_pos = self.get_interaction_pos()

            for tree in self.tree_sprites.sprites():
                if hasattr(tree, 'hitbox'):
                    if tree.hitbox.collidepoint(interaction_pos):
                        tree.damaged()

            for enemy in self.enemy_sprites.sprites():
                if hasattr(enemy, 'hitbox') and enemy.alive:
                    if enemy.hitbox.collidepoint(interaction_pos):
                        enemy.damaged()

        elif self.selected_weapon == 'lance':
            direction_str = self.action.split('_')[1]
            tile_size = self.tile_size
            lance_rect = self.hitbox.copy() 

            if direction_str == 'right':
                lance_rect.width = tile_size * 1
                lance_rect.height = tile_size * 3
                lance_rect.left = self.hitbox.right + tile_size
                lance_rect.centery = self.hitbox.centery

            elif direction_str == 'left':
                lance_rect.width = tile_size * 1
                lance_rect.height = tile_size * 3
                lance_rect.right = self.hitbox.left - tile_size
                lance_rect.centery = self.hitbox.centery

            elif direction_str == 'down':
                lance_rect.width = tile_size * 3
                lance_rect.height = tile_size * 1
                lance_rect.top = self.hitbox.bottom + tile_size
                lance_rect.centerx = self.hitbox.centerx

            elif direction_str == 'up':
                lance_rect.width = tile_size * 3
                lance_rect.height = tile_size * 1
                lance_rect.bottom = self.hitbox.top - tile_size - 15
                lance_rect.centerx = self.hitbox.centerx

            if self.groups():
                Weapon(lance_rect, direction_str, self.groups()[0])

            for enemy in self.enemy_sprites.sprites():
                if hasattr(enemy, 'hitbox') and enemy.alive:
                    if lance_rect.colliderect(enemy.hitbox):
                        enemy.damaged()

            self.debug_lance_rect = lance_rect
        
        self.action = self.action.replace('attack_', 'idle_')

        # Gọi lượt đi cho quái khi chém xong
        self.end_turn()

    def get_interaction_pos(self):
        direction_str = self.action.split('_')[1]
        return self.pos + PLAYER_WEAPON_OFFSET[direction_str]

    def add_item(self, item_id, amount=1):
        self.inventory.add_item(item_id, ITEM_DATABASE, amount)

    def use_item(self, item_id):
        for index, slot in enumerate(self.inventory.slots):
            if slot is not None and slot['item'].id == item_id:
                self.inventory.use_item_at_slot(index, self)
                return

    def use_item_at_slot(self, slot_index):
        self.inventory.use_item_at_slot(slot_index, self)

    def damaged(self, amount):
        self.health -= amount

    def import_spritesheet(self):
        sheet_path = '../assets/characters/player/player.png'
        raw_image = pygame.image.load(sheet_path)

        self.animations_dict = {}
        animation_steps = {
            'idle_down':    (0, 6),
            'idle_right':   (1, 6),
            'idle_left':    (1, 6),
            'idle_up':      (2, 6),
            'walk_down':    (3, 6),
            'walk_right':   (4, 6),
            'walk_left':    (4, 6),
            'walk_up':      (5, 6),
            'attack_down':  (6, 4),
            'attack_right': (7, 4),
            'attack_left':  (7, 4),
            'attack_up':    (8, 4),
            'die':          (9, 3),
        }

        for action, (row_index, total_frames) in animation_steps.items():
            temp_img_list = []
            for frame_index in range(total_frames):
                frame_surf = load_spritesheet(raw_image, 48, 48, row_index, frame_index, 2)
                temp_img_list.append(frame_surf)
            self.animations_dict[action] = temp_img_list

    def animate(self, dt):
        speed_multiplier = 16 if 'attack' in self.action else 6
        self.frame += speed_multiplier * dt
        if self.frame >= len(self.animations_dict[self.action]):
            if 'attack' in self.action:
                self.frame = len(self.animations_dict[self.action]) - 1
            else:
                self.frame = 0

        current_image = self.animations_dict[self.action][int(self.frame)]
        self.image = pygame.transform.flip(current_image, True, False) if self.flip else current_image

        self.rect.centerx = self.hitbox.centerx
        self.rect.bottom = self.hitbox.bottom

    def trigger_attack(self):
        """Hàm dùng chung để kích hoạt tấn công dứt khoát"""
        self.timers['weapon use'].activate()
        self.direction = pygame.math.Vector2()
        self.frame = 0
        self.state = 'attack'
        self.attacking = True

    def input(self):
        if self.is_moving or self.timers['weapon use'].active or self.timers['turn_cooldown'].active:
            return

        keys = pygame.key.get_just_pressed()

        # 1. ĐẤM THỦ CÔNG (SPACE)
        if keys[pygame.K_SPACE]:
            if not self.attacking and not self.timers['weapon use'].active:
                self.trigger_attack()
            return
        else:
            self.attacking = False

        # 2. ĐỔI VŨ KHÍ & DÙNG ITEM
        if keys[pygame.K_q] and not self.timers['weapon switch'].active:
            self.timers['weapon switch'].activate()
            self.weapon_index = (self.weapon_index + 1) % len(self.weapons)
            self.selected_weapon = self.weapons[self.weapon_index]

        if keys[pygame.K_h]:
            self.use_item('potion_red')

        # 3. DI CHUYỂN / BUMP ATTACK (ONEBIT ADVENTURE STYLE)
        input_dir = pygame.math.Vector2()

        if keys[pygame.K_w]:
            input_dir.y = -1
            self.facing = 'up'
            self.flip = False
        elif keys[pygame.K_s]:
            input_dir.y = 1
            self.facing = 'down'
            self.flip = False
        elif keys[pygame.K_a]:
            input_dir.x = -1
            self.facing = 'left'
            self.flip = True
        elif keys[pygame.K_d]:
            input_dir.x = 1
            self.facing = 'right'
            self.flip = False

        # Nếu người chơi bấm phím điều hướng
        if input_dir.magnitude() > 0:
            potential_target = self.pos + input_dir * self.tile_size

            # 🟢 CHECK TẤN CÔNG BẰNG DI CHUYỂN (BUMP ATTACK): Đâm thẳng vào quái
            enemy_to_attack = None
            for enemy in self.enemy_sprites.sprites():
                if enemy.alive:
                    if (enemy.pos == potential_target or 
                        (hasattr(enemy, 'target_pos') and enemy.target_pos == potential_target)):
                        enemy_to_attack = enemy
                        break

            # Nếu ô phía trước có Quái -> Đứng yên tại chỗ và TẠNG NÓ MỘT CÚ
            if enemy_to_attack:
                self.trigger_attack()
                return

            # CHECK TƯỜNG/VẬT CẢN MAP
            map_blocking = hasattr(self, 'check_future_collision') and self.check_future_collision(potential_target)
            if map_blocking:
                self.is_moving = False
                self.direction = pygame.math.Vector2()
            else:
                # Ô trống -> Tiến bước sang ô đó
                self.direction = input_dir
                self.target_pos = potential_target
                self.is_moving = True

    def move(self, dt):
        if not self.is_moving:
            return

        # Tính toán trượt ô mượt mà
        to_target = self.target_pos - self.pos
        distance = to_target.magnitude()
        move_distance = self.stats['speed'] * dt 

        if move_distance >= distance:
            self.pos = pygame.math.Vector2(self.target_pos)
            self.is_moving = False
            self.direction = pygame.math.Vector2()
            
            # 🟢 ĐIỂM CHỐT: Đi xong 1 ô -> Gọi lượt cho Quái phản công ngay!
            self.end_turn()
        else:
            self.pos += to_target.normalize() * move_distance

        # Đồng bộ hitbox vật lý và rect ảnh
        self.hitbox.centerx = round(self.pos.x)
        self.hitbox.centery = round(self.pos.y)
        self.rect.centerx = self.hitbox.centerx
        self.rect.bottom = self.hitbox.bottom

    def end_turn(self):
        """Kích hoạt khoảng chờ lượt và gọi lượt đi cho Quái"""
        self.timers['turn_cooldown'].activate() # Kích hoạt khóa phím 150ms
        
        if self.level and hasattr(self.level, 'check_enemy_turns'):
            self.level.check_enemy_turns()

    def update_status(self):
        if self.timers['weapon use'].active:
            self.state = 'attack'
        else:
            self.state = 'walk' if self.is_moving else 'idle'

        new_action = f'{self.state}_{self.facing}'
        if self.action != new_action:
            self.action = new_action

    def update_timer(self):
        for timer in self.timers.values():
            timer.update()

    def update(self, dt):
        self.input()
        self.update_timer()
        self.get_interaction_pos()
        self.move(dt)
        self.update_status()
        self.animate(dt)