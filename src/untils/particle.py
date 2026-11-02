import pygame
from untils.settings import *

class ParticleEffect(pygame.sprite.Sprite):
    def __init__(self, pos, frames, groups, animation_speed=12, z=LAYERS['main']):
        super().__init__(groups)
        
        # Validation kiểm tra dữ liệu đầu vào
        if not frames:
            raise ValueError("Danh sách 'frames' cung cấp cho ParticleEffect không được rỗng!")

        self.frames = frames
        self.frame_index = 0.0
        self.animation_speed = animation_speed
        
        # Khởi tạo frame đầu tiên
        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=pos)
        self.z = z

    def animate(self, dt):
        """Xử lý cập nhật khung hình và tự hủy khi hoàn thành"""
        self.frame_index += self.animation_speed * dt
        
        # Kiểm tra hoàn thành animation
        if self.frame_index >= len(self.frames):
            self.kill()
        else:
            # Lấy vị trí tâm hiện tại để re-center (tránh lệch hình nếu các frame có kích thước khác nhau)
            current_center = self.rect.center
            
            # Cập nhật image và rect mới
            self.image = self.frames[int(self.frame_index)]
            self.rect = self.image.get_rect(center=current_center)

    def update(self, dt):
        self.animate(dt)