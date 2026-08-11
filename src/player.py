import pygame
from settings import *
from spritesheet import load_spritesheet
from timers import Timer
from entity import Entity
from weapon import Weapon
from inventory import Inventory
from skill import SkillManager
from floating_text import FloatingText


class Player(Entity):
    def __init__(self, pos, group, collision_sprites, tree_sprites, enemy_sprites):
        super().__init__(group)

        self.spawn_pos = pygame.math.Vector2(pos)

        # ---------------------------------------------------------------------
        # 1. GRAPHIC & ANIMATION SETUP
        # ---------------------------------------------------------------------
        self.state = 'idle'
        self.facing = 'down'
        self.action = f'{self.state}_{self.facing}'
        self.frame = 0
        self.flip = False
        self.z = LAYERS['main']

        self.import_spritesheet()
        self.image = self.animations_dict[self.action][self.frame]
        self.rect = self.image.get_rect(center=pos)

        # ---------------------------------------------------------------------
        # 2. HITBOX & GRID SETUP
        # ---------------------------------------------------------------------
        self.tile_size = 48
        self.hitbox = pygame.Rect(0, 0, 24, 24)
        self.hitbox.center = (pos)
        self.update_rect_to_hitbox()

        self.collision_sprites = collision_sprites
        self.tree_sprites = tree_sprites
        self.enemy_sprites = enemy_sprites
        self.level = None

        # ---------------------------------------------------------------------
        # 3. TRẠNG THÁI DI CHUYỂN & TIMER
        # ---------------------------------------------------------------------
        self.pos = pygame.math.Vector2(self.hitbox.center)
        self.target_pos = pygame.math.Vector2(self.pos)
        self.is_moving = False
        self.is_casting = False
        self.attacking = False
        self.steps = 0

        self.timers = {
            'weapon use': Timer(200, self.weapon_use),
            'turn_cooldown': Timer(150),
        }

        # ---------------------------------------------------------------------
        # 4. HỆ THỐNG SKILL (ONEBIT)
        # ---------------------------------------------------------------------
        self.skill_manager = SkillManager(self, skill_data, SKILL_FUSION_RECIPES)
        self.skill_slots = {1: None, 2: None, 3: None, 4: None}
        self.unlocked_active_skills = set()
        self.skill_points = 0
        self.unlocked_skill_nodes = {'root'}

        # ---------------------------------------------------------------------
        # 5. CHI TIẾT CHỈ SỐ & TÚI ĐỒ (STATS & INVENTORY)
        # ---------------------------------------------------------------------
        self.stats = {
            'health': 100,
            'energy': 60,
            'attack': 10,
            'magic': 4,
            'speed': 300
        }
        self.health = self.stats['health'] * 0.5
        self.energy = self.stats['energy'] * 0.8
        self.exp = 123
        self._gold = 0

        self.vfx_font = pygame.font.Font(UI_FONT, 18)
        self.selected_weapon = 'sword'

        self.inventory = Inventory(total_slots=16)
        self.add_item('sword', 1)
        self.add_item('lance', 1)
        self.add_item('axe', 1)
        self.add_item('potion_red', 2)

        self.inventory.equip_weapon_from_slot(0, self)

    def update_rect_to_hitbox(self):
        """ Căn chỉnh vị trí hình ảnh ăn theo hitbox (tránh lặp code)"""
        self.rect.centerx = self.hitbox.centerx
        self.rect.bottom = self.hitbox.bottom

    # -------------------------------------------------------------------------
    # PROPERTIES
    # -------------------------------------------------------------------------
    @property
    def gold(self) -> int:
        return self._gold

    @property
    def total_attack_damage(self):
        base_attack = self.stats.get('attack', 10)
        current_weapon = getattr(self, 'selected_weapon', 'sword')
        weapon_damage = weapon_data.get(current_weapon, {}).get('damage', 0)

        raw_total = base_attack + weapon_damage
        bonus_pct = self.get_skill_tree_bonus('weapon_dmg_pct')
        return int(raw_total * (1 + bonus_pct))

    @property
    def max_health(self):
        bonus_pct = self.get_skill_tree_bonus('max_hp_pct')
        return int(self.stats.get('health', 100) * (1 + bonus_pct))

    @property
    def max_energy(self):
        bonus_pct = self.get_skill_tree_bonus('max_energy_pct')
        return int(self.stats.get('energy', 60) * (1 + bonus_pct))

    @property
    def game_sound(self):
        if self.level and hasattr(self.level, 'game') and hasattr(self.level.game, 'sound_manager'):
            return self.level.game.sound_manager
        return None

    # -------------------------------------------------------------------------
    # QUẢN LÝ TIỀN TỆ & CÂY KỸ NĂNG
    # -------------------------------------------------------------------------
    def add_gold(self, amount: int, spawn_vfx_pos=None) -> int:
        if amount <= 0:
            return self._gold
            
        self._gold += amount

        if spawn_vfx_pos and self.level and hasattr(self.level, 'all_sprites'):
            FloatingText(
                text=f"+{amount} G", 
                pos=spawn_vfx_pos, 
                color=(255, 215, 0), 
                groups=self.level.all_sprites,
                font=self.vfx_font
            )
        return self._gold

    def spend_gold(self, amount: int) -> bool:
        if 0 < amount <= self._gold:
            self._gold -= amount
            return True
        return False

    def get_skill_tree_bonus(self, effect_type):
        total = 0
        for node_id in self.unlocked_skill_nodes:
            node = skill_tree_data.get(node_id)
            if node and node.get('effect_type') == effect_type:
                total += node.get('effect_value', 0)
        return total

    def unlock_skill_node(self, node_id):
        node = skill_tree_data.get(node_id)
        if not node:
            return False, "Node không tồn tại"
        if node_id in self.unlocked_skill_nodes:
            return False, "Đã mở khoá rồi"

        parent_id = node.get('parent')
        if parent_id and parent_id not in self.unlocked_skill_nodes:
            return False, "Cần mở khoá node trước đó trước"

        cost = node.get('cost', 0)
        if self.skill_points < cost:
            return False, "Không đủ điểm Kỹ Năng"

        self.skill_points -= cost
        self.unlocked_skill_nodes.add(node_id)
        return True, f"Đã mở khoá {node.get('name', node_id)}!"

    def on_boss_defeated(self, monster_name):
        self.skill_points += 3
        reward_skill = BOSS_SKILL_REWARDS.get(monster_name)
        if reward_skill and reward_skill not in self.unlocked_active_skills:
            self.unlocked_active_skills.add(reward_skill)
            for slot_num in sorted(self.skill_slots.keys()):
                if self.skill_slots[slot_num] is None:
                    self.skill_slots[slot_num] = reward_skill
                    break

    def set_skill_slot(self, slot_number, skill_name):
        if slot_number not in self.skill_slots:
            return None
        old_skill = self.skill_slots.get(slot_number)
        self.skill_slots[slot_number] = skill_name
        return old_skill

    # -------------------------------------------------------------------------
    # HÀM XỬ LÝ VŨ KHÍ & INVENTORY
    # -------------------------------------------------------------------------
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
        if self.health <= 0:
            self.respawn()

    def respawn(self):
        self.health = self.max_health
        self.energy = self.max_energy
        self.pos = pygame.math.Vector2(self.spawn_pos)
        self.target_pos = pygame.math.Vector2(self.spawn_pos)
        self.hitbox.center = (self.pos)
        self.update_rect_to_hitbox()
        self.is_moving = False
        self.state = 'idle'
        self.action = f'{self.state}_{self.facing}'
        self.frame = 0

    def weapon_use(self):
        if self.groups():
            w = Weapon(self, self.selected_weapon, self.groups()[0])
            if self.selected_weapon == 'lance':
                self.debug_lance_rect = w.rect

        self.action = self.action.replace('attack_', 'idle_')
        self.end_turn()

    def trigger_attack(self):
        self.timers['weapon use'].activate()
        self.frame = 0
        self.state = 'attack'
        self.attacking = True

        if self.game_sound:
            self.game_sound.play_sfx('attack')

    def get_interaction_pos(self):
        direction_str = self.action.split('_')[1]
        return self.pos + PLAYER_WEAPON_OFFSET[direction_str]

    # -------------------------------------------------------------------------
    # ANIMATION
    # -------------------------------------------------------------------------
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
        self.update_rect_to_hitbox()

    # -------------------------------------------------------------------------
    # INPUT
    # -------------------------------------------------------------------------
    def input(self):
        if (self.is_moving or 
            self.is_casting or 
            self.timers['weapon use'].active or 
            self.timers['turn_cooldown'].active):
            return

        camera_offset = self.level.all_sprites.offset if self.level else pygame.math.Vector2()
        if self.skill_manager.handle_input(camera_offset):
            return

        keys = pygame.key.get_just_pressed()

        # Space -> Đánh
        if keys[pygame.K_SPACE]:
            if not self.attacking and not self.timers['weapon use'].active:
                self.trigger_attack()
            return
        else:
            self.attacking = False

        # Phím H -> Dùng bình máu
        if keys[pygame.K_h]:
            self.use_item('potion_red')

        # Phím 1-4 -> Skill
        slot_keys = {1: pygame.K_1, 2: pygame.K_2, 3: pygame.K_3, 4: pygame.K_4}
        for slot_num, key_const in slot_keys.items():
            if keys[key_const]:
                active_skill = self.skill_manager.get_active_skill_for_slot(slot_num)
                if active_skill:
                    self.skill_manager.start_aiming(active_skill)
                break

        # WASD Di chuyển
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

        # Bump Attack / Move
        if input_dir.magnitude() > 0:
            potential_target = self.pos + input_dir * self.tile_size
            target_gx = int(potential_target.x // self.tile_size)
            target_gy = int(potential_target.y // self.tile_size)

            enemy_to_attack = None
            for enemy in self.enemy_sprites.sprites():
                if enemy.alive:
                    if hasattr(enemy, 'get_occupied_tiles'):
                        boss_tiles = enemy.get_occupied_tiles(enemy.grid_x, enemy.grid_y)
                        if (target_gx, target_gy) in boss_tiles:
                            enemy_to_attack = enemy
                            break
                    else:
                        if (enemy.pos == potential_target or 
                            (hasattr(enemy, 'target_pos') and enemy.target_pos == potential_target)):
                            enemy_to_attack = enemy
                            break

            if enemy_to_attack:
                self.trigger_attack()
                is_boss = hasattr(enemy_to_attack, 'get_occupied_tiles')
                bonus_pct = self.get_skill_tree_bonus('boss_dmg_bonus_pct')
                final_dmg = int(self.total_attack_damage * (1 + bonus_pct)) if is_boss else self.total_attack_damage
                enemy_to_attack.damaged(final_dmg)
                return

            # Collision Check
            map_blocking = hasattr(self, 'check_future_collision') and self.check_future_collision(potential_target)
            if map_blocking:
                self.is_moving = False
            else:
                self.target_pos = potential_target
                self.is_moving = True

    # -------------------------------------------------------------------------
    # UPDATE LOGIC
    # -------------------------------------------------------------------------
    def move(self, dt):
        if not self.is_moving:
            return

        to_target = self.target_pos - self.pos
        distance = to_target.magnitude()
        move_distance = self.stats['speed'] * dt 

        if move_distance >= distance:
            self.pos = pygame.math.Vector2(self.target_pos)
            self.is_moving = False
            self.end_turn()
        else:
            self.pos += to_target.normalize() * move_distance

        self.hitbox.centerx = round(self.pos.x)
        self.hitbox.centery = round(self.pos.y)
        self.update_rect_to_hitbox()

    def end_turn(self):
        self.steps += 1
        self.timers['turn_cooldown'].activate()
        self.skill_manager.update_cooldowns()

        hp_regen_pct = self.get_skill_tree_bonus('hp_regen_pct_per_turn')
        if hp_regen_pct > 0:
            self.health = min(self.max_health, self.health + self.max_health * hp_regen_pct)

        energy_regen = self.get_skill_tree_bonus('energy_regen_flat_per_turn')
        if energy_regen > 0:
            self.energy = min(self.max_energy, self.energy + energy_regen)

        if hasattr(self, 'active_zones'):
            for zone in self.active_zones[:]:
                if zone.alive():
                    zone.on_turn_end()
                else:
                    self.active_zones.remove(zone)

        if self.level and hasattr(self.level, 'end_player_turn'):
            self.level.end_player_turn()

    def update_status(self):
        if self.timers['weapon use'].active:
            self.state = 'attack'
        else:
            self.state = 'walk' if self.is_moving else 'idle'

        new_action = f'{self.state}_{self.facing}'
        if self.action != new_action:
            self.action = new_action

    def update(self, dt):
        self.input()
        
        for timer in self.timers.values():
            timer.update()

        self.move(dt)
        self.update_status()
        self.animate(dt)