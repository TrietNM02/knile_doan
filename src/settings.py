import pygame
from pygame.math import Vector2
from spritesheet import load_spritesheet

# screen
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 720
TILE_SIZE = 48

MAP_COLORS = {
    'morning':   (255, 200, 150, 40),  # Hơi cam vàng nhạt, mờ mờ (Bình minh)
    'noon':      (0, 0, 0, 0),         # Trong suốt hoàn toàn (Sáng rõ, không phủ gì)
    'afternoon': (240, 130, 40, 60),   # Cam đậm hơn chút (Hoàng hôn)
    'evening':   (10, 15, 50, 140),    # Xanh tối vừa phải (Chập choạng tối)
    'night':     (0, 0, 30, 200)       # Xanh đen đậm, rất tối (Ban đêm)
}

# ui
BAR_HEIGHT = 20
HEALTH_BAR_WIDTH = 200
ENERGY_BAR_WIDTH = 140
ITEM_BOX_SIZE = 80
UI_FONT = '../assets/font/Cairopixel-G3DeP.ttf'  # Font Pixel đã Việt hóa
UI_FONT_SIZE = 18

# general colors
WATER_COLOR = '#71ddee'
UI_BG_COLOR = '#222222'
UI_BORDER_COLOR = '#111111'
TEXT_COLOR = '#EEEEEE'

# ui colors
HEALTH_COLOR = 'red'
ENERGY_COLOR = 'blue'
UI_BORDER_COLOR_ACTIVE = 'gold'

OVERLAY_POSITION = {}

PLAYER_WEAPON_OFFSET = {
    'left': Vector2(-50, 0),
    'right': Vector2(50, 0),
    'up': Vector2(0, -50),
    'down': Vector2(0, 50)
}

# weapons
weapon_data = {
    'sword': {
        'cooldown': 200,
        'damage': 15,
        'graphic': '../assets/weapons/sword/full.png',
        'effect_path': '../assets/effects/slash',
        'type': 'single_tile',
        'range_tiles': 1,
    },
    'lance': {
        'cooldown': 400,
        'damage': 30,
        'graphic': '../assets/weapons/lance/full.png',
        'effect_path': '../assets/effects/lance_thrust',
        'type': 'line_thrust',
        'range_width': 1,
        'range_length': 3
    },
    'axe': {
        'cooldown': 350,
        'damage': 25,
        'graphic': '../assets/weapons/axe/full.png',
        'effect_path': '../assets/effects/cleave',
        'type': 'aoe_sweep',
        'range_tiles': 1
    }
}

skill_data = {
    'fireball': {
        'name': 'FireBall',
        'energy_cost': 0,
        'cooldown_turns': 2,
        'damage_multiplier': 1.6,
        'type': 'projectile',
        'range_tiles': 5,
        'effect_path': '../assets/effects/fireball/fireball.png',
        'impact_effect_path': '../assets/effects/fireball/fireball-impact.png',
        'icon_path': '../assets/icons/fireball.png',

        # Thông số cho đạn bay (fireball.png)
        'frame_width': 48,
        'frame_height': 48,
        'cols': 4,
        'rows': 1,
        'total_frames': 4,
        'scale': 2,
        
        # Thông số cho impact (fireball-impact.png)
        'impact_cols': 6, 
        'impact_rows': 1,
        'impact_total_frames': 6, 
        'impact_speed': 40
    },
    'jump_stomp': {
        'name': 'Jump Stomp',
        'energy_cost': 10,
        'cooldown_turns': 3,
        'damage_multiplier': 1.4,
        'type': 'jump_aoe',
        'range_tiles': 5,
        'effect_path': '../assets/effects/stomp',
        'scale': 1.5,
        'speed': 50,
    },
    'wind_blast': {
        'name': 'Wind Blast',
        'energy_cost': 0,
        'cooldown_turns': 2,
        'damage_multiplier': 0.5,
        'type': 'push_back',
        'push_distance': 3,
        'effect_path': '../assets/effects/wind',
        'scale': 4,
        'icon_path': '../assets/icons/windblast.png',
    },
    'waterball': {
        'name': 'WaterBall',
        'energy_cost': 0,
        'cooldown_turns': 1,
        'damage_multiplier': 1.2,
        'type': 'projectile',
        'range_tiles': 4,

        'effect_path': '../assets/effects/waterball/waterball.png',
        'impact_effect_path': '../assets/effects/waterball/waterball-impact.png',
        'icon_path': '../assets/icons/waterball.png',

        'frame_width': 64,
        'frame_height': 64,
        'cols': 5,
        'rows': 5,
        'total_frames': 21,
        'scale': 1.5,

        'impact_cols': 4, 
        'impact_rows': 4,
        'impact_total_frames': 15, 
        'impact_speed': 50
    },
    'flame_slam': {
        'name': 'Flame Slam',
        'energy_cost': 0,
        'cooldown_turns': 3,
        'damage_multiplier': 1.4,
        'zone_damage_multiplier': 0.5,
        'duration_turns': 4,
        'type': 'jump_aoe',
        'range_tiles': 5,
        'zone_color': (255, 60, 0, 130),
        'effect_path': '../assets/effects/flame_slam',
        'scale': 1.5,
        'speed': 50,
    },
    'water_spout': {
        'name': 'Water Spout',
        'type': 'place_zone',
        'energy_cost': 0,
        'cooldown_turns': 4,
        'range_tiles': 3,
        'zone_damage_multiplier': 1.0,
        'duration_turns': 2,

        'startup_path': '../assets/effects/water_spout/water_spout_startup_infinity.png',
        'end_path': '../assets/effects/water_spout/water_spout_end.png',
        'icon_path': '../assets/icons/waterspout.png',

        'startup_info': {
            'cols': 4,
            'rows': 3,
            'total_frames': 12,
            'frame_width': 128,   
            'frame_height': 128,
            'speed': 14,
        },

        'end_info': {
            'cols': 3,
            'rows': 3,
            'total_frames': 8,
            'frame_width': 128,   
            'frame_height': 128,
            'speed': 14,
        },
    },
}

SKILL_FUSION_RECIPES = {
    ("fireball", "jump_stomp"): "flame_slam",
    ('waterball', 'wind_blast'): 'water_spout',
}

BOSS_SKILL_REWARDS = {
    'rock_boss': 'jump_stomp',
    'lava_slime_boss': 'fireball',
    'wind_slime_boss': 'wind_blast',
    'water_slime_boss': 'waterball',
}

skill_tree_data = {
    'root': {
        'name': 'Cội Nguồn', 'tier': 0, 'parent': None, 'cost': 0,
        'description': 'Điểm khởi đầu của Cây Kỹ Năng.',
    },

    # Tầng 1
    'dmg_branch': {
        'name': 'Nhánh Sát Thương', 'tier': 1, 'parent': 'root', 'cost': 1,
        'description': 'Mở khoá các nhánh tăng sát thương.',
        'effect_type': 'weapon_dmg_pct', 'effect_value': 0.05,
    },
    'vit_branch': {
        'name': 'Nhánh Sinh Tồn', 'tier': 1, 'parent': 'root', 'cost': 1,
        'description': 'Mở khoá các nhánh tăng sinh tồn.',
        'effect_type': 'max_hp_pct', 'effect_value': 0.05,
    },

    # Tầng 2
    'power_strike': {
        'name': 'Cường Kích', 'tier': 2, 'parent': 'dmg_branch', 'cost': 1,
        'description': '+10% sát thương đánh thường (vũ khí).',
        'effect_type': 'weapon_dmg_pct', 'effect_value': 0.10,
    },
    'arcane_mastery': {
        'name': 'Tinh Thông Phép', 'tier': 2, 'parent': 'dmg_branch', 'cost': 1,
        'description': '+15% sát thương Skill chủ động.',
        'effect_type': 'skill_dmg_pct', 'effect_value': 0.15,
    },
    'vitality': {
        'name': 'Thể Chất', 'tier': 2, 'parent': 'vit_branch', 'cost': 1,
        'description': '+10% máu tối đa.',
        'effect_type': 'max_hp_pct', 'effect_value': 0.10,
    },
    'mana_saver': {
        'name': 'Tiết Kiệm Mana', 'tier': 2, 'parent': 'vit_branch', 'cost': 1,
        'description': '-10% năng lượng tiêu hao khi dùng Skill.',
        'effect_type': 'energy_cost_reduction_pct', 'effect_value': 0.10,
    },

    # Tầng 3
    'crit_edge': {
        'name': 'Đòn Sắc Bén', 'tier': 3, 'parent': 'power_strike', 'cost': 1,
        'description': '+15% sát thương đánh thường (vũ khí).',
        'effect_type': 'weapon_dmg_pct', 'effect_value': 0.15,
    },
    'overwhelm': {
        'name': 'Áp Đảo', 'tier': 3, 'parent': 'power_strike', 'cost': 1,
        'description': '+20% sát thương (mọi loại) khi đánh Boss.',
        'effect_type': 'boss_dmg_bonus_pct', 'effect_value': 0.20,
    },
    'archmage': {
        'name': 'Đại Pháp Sư', 'tier': 3, 'parent': 'arcane_mastery', 'cost': 1,
        'description': '+20% sát thương Skill chủ động.',
        'effect_type': 'skill_dmg_pct', 'effect_value': 0.20,
    },
    'quick_recovery': {
        'name': 'Hồi Chiêu Nhanh', 'tier': 3, 'parent': 'arcane_mastery', 'cost': 1,
        'description': 'Giảm thẳng 1 lượt cooldown cho mọi Skill.',
        'effect_type': 'cooldown_reduction_flat', 'effect_value': 1,
    },
    'battle_hardened': {
        'name': 'Máu Chiến', 'tier': 3, 'parent': 'vitality', 'cost': 1,
        'description': '+15% máu tối đa.',
        'effect_type': 'max_hp_pct', 'effect_value': 0.15,
    },
    'regeneration': {
        'name': 'Tái Sinh', 'tier': 3, 'parent': 'vitality', 'cost': 1,
        'description': 'Hồi thêm 2% máu tối đa mỗi lượt đi.',
        'effect_type': 'hp_regen_pct_per_turn', 'effect_value': 0.02,
    },
    'meditation': {
        'name': 'Thiền Định', 'tier': 3, 'parent': 'mana_saver', 'cost': 1,
        'description': 'Hồi thêm 3 năng lượng mỗi lượt đi.',
        'effect_type': 'energy_regen_flat_per_turn', 'effect_value': 3,
    },
    'clarity': {
        'name': 'Tỉnh Táo', 'tier': 3, 'parent': 'mana_saver', 'cost': 1,
        'description': '-10% năng lượng tiêu hao khi dùng Skill (cộng dồn).',
        'effect_type': 'energy_cost_reduction_pct', 'effect_value': 0.10,
    },
}

particle = {
    'explosion_frame': {
        'explosion_path': '../assets/particles/explosion.png',
        'explosion_row': 8,
        'explosion_frames_count': 12,
        'frame_size': 64
    }
}

def load_particle_frames():
    """Hàm load sprite particle nổ"""
    if 'explosion_frame' not in particle:
        return []
        
    conf = particle['explosion_frame']
    try:
        raw_sheet = pygame.image.load(conf['explosion_path']).convert_alpha()
        return [
            load_spritesheet(
                raw_sheet, 
                conf['frame_size'], 
                conf['frame_size'], 
                conf['explosion_row'], 
                frame_idx, 
                2
            )
            for frame_idx in range(conf['explosion_frames_count'])
        ]
    except Exception as e:
        print(f"[LỖI LOAD PARTICLE]: {e}")
        return []

# enemy
monster_data = {
    'rock_boss': {
        'health': 100, 'exp': 120, 'gold': 120, 'damage': 6, 
        'attack_type': 'leaf_attack', 'attack_sound': '', 
        'speed': 3, 'resistance': 3, 'attack_radius': 50, 'notice_radius': 4, 
        'monster_size': 64,
        'scale': 2,
        'body_size': 2,
        'hitbox_width': 36,  
        'hitbox_height': 48,
        'y_offset': 0,
        'skills': [
            {
                'name': 'stomp',
                'cooldown': 10,
                'cd_timer': 0,
                'range_type': 'aoe_around'
            },
        ],
        'single_sheet': False,
        'animations': {
            'idle_down':  ('idle',  0, 7),  'idle_up':    ('idle',  1, 7),  'idle_left':  ('idle',  2, 7),  'idle_right': ('idle',  3, 7),
            'walk_down':  ('walk',  3, 10), 'walk_up':    ('walk',  0, 10), 'walk_left':  ('walk',  1, 10), 'walk_right': ('walk',  2, 10),
            'stomp_down': ('stomp', 3, 13), 'stomp_up':   ('stomp', 0, 13), 'stomp_left': ('stomp', 1, 13), 'stomp_right':('stomp', 2, 13),
            'attack_down': ('swipe', 0, 10), 'attack_up':   ('swipe', 1, 10), 'attack_left': ('swipe', 2, 10), 'attack_right':('swipe', 3, 10),
        },
        'flip_on_left': False,  
        'flip_on_right': False,
        'particle_frames': load_particle_frames()
    },

    'lava_slime_boss': {
        'health': 100, 'exp': 120, 'gold': 120, 'damage': 6, 
        'attack_type': 'leaf_attack', 'attack_sound': '../audio/attack/slash.wav', 
        'speed': 3, 'resistance': 3, 'attack_radius': 50, 'notice_radius': 4, 
        'monster_size': 64,
        'scale': 4,
        'body_size': 2,
        'hitbox_width': 128,  
        'hitbox_height': 128,
        'y_offset': 0,
        'skills': [
            {
                'name': 'stomp',
                'cooldown': 10,
                'cd_timer': 0,
                'range_type': 'aoe_around'
            },
        ],
        'single_sheet': False,
        'animations': {
            'idle_down':  ('idle',  0, 6),  'idle_up':    ('idle',  1, 6),  'idle_left':  ('idle',  2, 6),  'idle_right': ('idle',  3, 6),
            'walk_down':  ('walk',  0, 8), 'walk_up':    ('walk',  1, 8), 'walk_left':  ('walk',  2, 8), 'walk_right': ('walk',  3, 8),
            'stomp_down': ('stomp', 0, 9), 'stomp_up':   ('stomp', 1, 9), 'stomp_left': ('stomp', 2, 9), 'stomp_right':('stomp', 3, 9),
            'attack_down': ('attack', 0, 9), 'attack_up':   ('attack', 1, 9), 'attack_left': ('attack', 2, 9), 'attack_right':('attack', 3, 9),
            'die': ('die', 0, 10),
        },
        'flip_on_left': False,  
        'flip_on_right': False,
        'particle_frames': []
    },

    'wind_slime_boss': {
        'health': 100, 'exp': 120, 'gold': 120, 'damage': 6, 
        'attack_type': 'leaf_attack', 'attack_sound': '../audio/attack/slash.wav', 
        'speed': 3, 'resistance': 3, 'attack_radius': 50, 'notice_radius': 4, 
        'monster_size': 64,
        'scale': 4,
        'body_size': 2,
        'hitbox_width': 128,  
        'hitbox_height': 128,
        'y_offset': 0,
        'skills': [
            {
                'name': 'stomp',
                'cooldown': 10,
                'cd_timer': 0,
                'range_type': 'aoe_around'
            },
        ],
        'single_sheet': False,
        'animations': {
            'idle_down':  ('idle',  0, 6),  'idle_up':    ('idle',  1, 6),  'idle_left':  ('idle',  2, 6),  'idle_right': ('idle',  3, 6),
            'walk_down':  ('walk',  0, 8), 'walk_up':    ('walk',  1, 8), 'walk_left':  ('walk',  2, 8), 'walk_right': ('walk',  3, 8),
            'stomp_down': ('stomp', 0, 9), 'stomp_up':   ('stomp', 1, 9), 'stomp_left': ('stomp', 2, 9), 'stomp_right':('stomp', 3, 9),
            'attack_down': ('attack', 0, 9), 'attack_up':   ('attack', 1, 9), 'attack_left': ('attack', 2, 9), 'attack_right':('attack', 3, 9),
            'die': ('die', 0, 10),
        },
        'flip_on_left': False,  
        'flip_on_right': False,
        'particle_frames': []
    },

    'water_slime_boss': {
        'health': 100, 'exp': 120, 'gold': 120, 'damage': 6, 
        'attack_type': 'leaf_attack', 'attack_sound': '../audio/attack/slash.wav', 
        'speed': 3, 'resistance': 3, 'attack_radius': 50, 'notice_radius': 4, 
        'monster_size': 64,
        'scale': 4,
        'body_size': 2,
        'hitbox_width': 128,  
        'hitbox_height': 128,
        'y_offset': 0,
        'skills': [
            {
                'name': 'stomp',
                'cooldown': 10,
                'cd_timer': 0,
                'range_type': 'aoe_around'
            },
        ],
        'single_sheet': False,
        'animations': {
            'idle_down':  ('idle',  0, 6),  'idle_up':    ('idle',  1, 6),  'idle_left':  ('idle',  2, 6),  'idle_right': ('idle',  3, 6),
            'walk_down':  ('walk',  0, 8), 'walk_up':    ('walk',  1, 8), 'walk_left':  ('walk',  2, 8), 'walk_right': ('walk',  3, 8),
            'stomp_down': ('stomp', 0, 9), 'stomp_up':   ('stomp', 1, 9), 'stomp_left': ('stomp', 2, 9), 'stomp_right':('stomp', 3, 9),
            'attack_down': ('attack', 0, 9), 'attack_up':   ('attack', 1, 9), 'attack_left': ('attack', 2, 9), 'attack_right':('attack', 3, 9),
            'die': ('die', 0, 10),
        },
        'flip_on_left': False,  
        'flip_on_right': False,
        'particle_frames': []
    },

    'slime': {
        'health': 50, 'exp': 120, 'gold': 15, 'damage': 6, 
        'attack_type': 'leaf_attack', 'attack_sound': '../audio/attack/slash.wav', 
        'speed': 3, 'resistance': 3, 'attack_radius': 50, 'notice_radius': 144, 
        'monster_size': 32,
        'hitbox_width': 48,  
        'hitbox_height': 48,
        'y_offset': 0,
        'single_sheet': True,
        'animations': {
            'idle_down':    (0, 4), 'idle_right':    (1, 4), 'idle_left':      (1, 4), 'idle_up':      (2, 4),
            'walk_down':    (3, 6), 'walk_right':    (4, 6), 'walk_left':      (4, 6), 'walk_up':      (5, 6),
            'attack_down':  (6, 7), 'attack_left':   (7, 7), 'attack_right':   (7, 7), 'attack_up':    (8, 7),
            'damaged_down': (9, 3), 'damaged_left':  (10, 3), 'damaged_right': (10, 3), 'damaged_up':  (11, 3),
            'die':          (12, 6)
        },
        'flip_on_left': True,  
        'flip_on_right': False,
        'particle_frames': []
    }
}

ITEM_DATABASE = {
    'sword': {
        'name': 'Sword',
        'type': 'weapon',
        'description': 'Kiếm ngắn linh hoạt, đánh 1 ô phía trước.',
        'value': 15,
        'icon_path': '../assets/weapons/sword/full.png'
    },
    'lance': {
        'name': 'Lance',
        'type': 'weapon',
        'description': 'Vũ khí tầm xa, đánh quét 3 ô.',
        'value': 30,
        'icon_path': '../assets/weapons/lance/full.png'
    },
    'axe': {
        'name': 'Axe',
        'type': 'weapon',
        'description': 'Rìu càn quét sát thương cao.',
        'value': 5,
        'icon_path': '../assets/weapons/axe/full.png'
    },
    'wood': {
        'name': 'Gỗ Thô',
        'type': 'material',
        'description': 'Nguyên liệu cơ bản lấy từ việc chặt cây.',
        'price': 5,
    },
    'slime_gel': {
        'name': 'Gel Slime',
        'type': 'material',
        'description': 'Chất nhớt dính rớt ra từ quái vật Slime.',
        'price': 10
    },
    'potion_red': {
        'name': 'Bình Máu',
        'type': 'consumable',
        'description': 'Hồi lập tức 20 lượng máu cho bản thân.',
        'value': 20,
        'price': 15,
        'icon_path': '../assets/items/potion_red.png'
    },
    'potion_energy': {
        'name': 'Nước Tăng Lực',
        'type': 'consumable',
        'description': 'Hồi lập tức 15 điểm năng lượng.',
        'value': 15,
        'price': 20,
        'icon_path': '../assets/items/potion_energy.png'
    }
}

LAYERS = {
    'water': 0,
    'ground': 1,
    'floor': 2,
    'main': 3,
    'dialog': 4,
    'ui_overlay': 5,
}

OBJECT_POS = {}