from pygame.math import Vector2

# screen
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 720
TILE_SIZE = 48

MAP_COLORS = {
    'morning':   (255, 200, 150, 40),  # Hơi cam vàng nhạt, mờ mờ (Bình minh)
    'noon':      (0, 0, 0, 0),         # Trong suốt hoàn toàn (Sáng rõ, không phủ gì)
    'afternoon': (240, 130, 40, 60),   # Cam đậm hơn chút (Hoàng hôn)
    'evening':   (20, 20, 80, 110),    # Xanh tối vừa phải (Chập choạng tối)
    'night':     (0, 0, 30, 200)     # Xanh đen đậm, rất tối (Ban đêm)
}

# ui
BAR_HEIGHT = 20
HEALTH_BAR_WIDTH = 200
ENERGY_BAR_WIDTH = 140
ITEM_BOX_SIZE = 80
UI_FONT = '../assets/font/joystix.ttf'
UI_FONT_SIZE = 18

# general colors
WATER_COLOR = '#71ddee'
UI_BG_COLOR = '#222222'
UI_BORDER_COLOR = '#111111'
TEXT_COLOR = '#EEEEEE'

# ui colors
HEALTH_COLOR = 'red'
ENERGEY_COLOR = 'blue'
UI_BORDER_COLOR_ACTIVE = 'gold'


OVERLAY_POSITION = {}

PLAYER_WEAPON_OFFSET = {
	'left': Vector2(-50,0),
	'right': Vector2(50,0),
	'up': Vector2(0,-50),
	'down': Vector2(0,50)
}

# weapons
weapon_data = {
	'sword': {'cooldown': 100, 'damage': 15,'graphic':'../assets/weapons/sword/full.png'},
	'lance': {'cooldown': 400, 'damage': 30,'graphic':'../assets/weapons/lance/full.png'},
	'axe': {'cooldown': 300, 'damage': 20, 'graphic':'../assets/weapons/axe/full.png'},
}

# e nemy
monster_data = {
    'rock_boss': {
        'health': 10, 'exp': 120, 'damage': 6, 
        'attack_type': 'leaf_attack', 'attack_sound': '../audio/attack/slash.wav', 
        'speed': 3, 'resistance': 3, 'attack_radius': 50, 'notice_radius': 192, 
        'monster_size': 64,
        'hitbox_width': 36,  
        'hitbox_height': 48,
        'y_offset': 0,
        # 🌟 Cấu hình cắt theo file riêng lẻ: (Tên file, Chỉ số hàng của file đó, Số frame)
        'single_sheet': False,
        'animations': {
            'idle_down':  ('idle',  0, 7),  'idle_up':    ('idle',  1, 7),  'idle_left':  ('idle',  2, 7),  'idle_right': ('idle',  3, 7),
            'walk_down':  ('walk',  3, 10), 'walk_up':    ('walk',  0, 10), 'walk_left':  ('walk',  1, 10), 'walk_right': ('walk',  2, 10),
            'stomp_down': ('stomp', 3, 13), 'stomp_up':   ('stomp', 0, 13), 'stomp_left': ('stomp', 1, 13), 'stomp_right':('stomp', 2, 13),
            'attack_down': ('swipe', 0, 10), 'attack_up':   ('swipe', 1, 10), 'attack_left': ('swipe', 2, 10), 'attack_right':('swipe', 3, 10),
        },
        'flip_on_left': False,  
        'flip_on_right': False,
    },
    'slime': {
        'health': 5, 'exp': 120, 'damage': 6, 
        'attack_type': 'leaf_attack', 'attack_sound': '../audio/attack/slash.wav', 
        'speed': 3, 'resistance': 3, 'attack_radius': 50, 'notice_radius': 144, 
        'monster_size': 32,
        'hitbox_width': 36,  
        'hitbox_height': 36,
        'y_offset': 0,
        # 🌟 Cấu hình cắt theo file tổng: (Chỉ số hàng trong file slime.png, Số frame)
        'single_sheet': True,
        'animations': {
            'idle_down':    (0, 4), 'idle_right':    (1, 4), 'idle_left':      (1, 4), 'idle_up':      (2, 4),
            'walk_down':    (3, 6), 'walk_right':    (4, 6), 'walk_left':      (4, 6), 'walk_up':      (5, 6),
            'attack_down':  (6, 7), 'attack_left':   (7, 7), 'attack_right':   (7, 7), 'attack_up':    (8, 7),
            'damaged_down': (9, 3), 'damaged_left':  (10, 3), 'damaged_right': (10, 3), 'damaged_up':  (11, 3),
            'die':         	(12, 6)
        },
        'flip_on_left': True,  
        'flip_on_right': False,
    }
}

ITEM_DATABASE = {
    'wood': {
        'name': 'Gỗ Thô',
        'type': 'material',
        'description': 'Nguyên liệu cơ bản lấy từ việc chặt cây.',
        'value': 0
    },
    'slime_gel': {
        'name': 'Gel Slime',
        'type': 'material',
        'description': 'Chất nhớt dính rớt ra từ quái vật Slime.',
        'value': 0
    },
    'potion_red': {
        'name': 'Bình Máu',
        'type': 'consumable',
        'description': 'Hồi lập tức 20 lượng máu cho bản thân.',
        'value': 20
    },
    'potion_energy': {
        'name': 'Nước Tăng Lực',
        'type': 'consumable',
        'description': 'Hồi lập tức 15 điểm năng lượng.',
        'value': 15
    }
}

LAYERS = {
    'water': 0,
    'ground': 1,
    'sky_overlay': 2,
    'main': 3,


}

OBJECT_POS = {}


