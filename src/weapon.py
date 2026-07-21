import pygame
import os
from settings import *

class Weapon(pygame.sprite.Sprite):
    def __init__(self, rect, direction, groups):
        super().__init__(groups)
        
        self.z = LAYERS['main']  # Đảm bảo layer hiển thị ngang hàng player/enemy
        self.direction = direction
        self.rect = rect.copy()

        # 1. Tự động định vị đường dẫn tuyệt đối đến file ảnh duy nhất (0.png)
        src_dir = os.path.dirname(__file__)
        img_path = os.path.abspath(os.path.join(src_dir, '..', 'assets', 'effects', 'slash', '0.png'))
        
        # 2. Tải ảnh gốc
        raw_image = pygame.image.load(img_path).convert_alpha()
        
        # 3. Xoay ảnh theo đúng hướng đánh của nhân vật
        self.image = self.rotate_frame(raw_image)
        
        # 4. Scale kích thước ảnh vừa khít với hitbox thương (lance_rect)
        self.image = pygame.transform.scale(self.image, (self.rect.width, self.rect.height))
        
        # 5. Khởi tạo thuộc tính Alpha (độ trong suốt) để làm hiệu ứng mờ dần
        self.alpha = 255
        self.fade_speed = 500  # Tốc độ biến mất (giá trị càng cao mất càng nhanh)

    def rotate_frame(self, frame):
        # Mặc định giả định ảnh gốc 0.png là chém hướng RIGHT
        if self.direction == 'left':
            return pygame.transform.flip(frame, True, False)
        elif self.direction == 'up':
            return pygame.transform.rotate(frame, 90)
        elif self.direction == 'down':
            return pygame.transform.rotate(frame, -90)
        return frame  # Hướng right giữ nguyên

    def update(self, dt):
        # Giảm dần độ trong suốt theo delta time
        self.alpha -= self.fade_speed * dt
        
        if self.alpha <= 0:
            self.kill()  # Khi ảnh mờ hẳn hoàn toàn thì tự hủy
        else:
            # Cập nhật độ mờ mới cho ảnh hiệu ứng
            self.image.set_alpha(int(self.alpha))