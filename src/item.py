import pygame

from settings import *

class Item:
    def __init__(self, item_id, name, item_type, description, value=0):
        self.id = item_id            # Định danh hệ thống (Ví dụ: 'potion_red', 'wood')
        self.name = name            # Tên hiển thị tiếng Việt (Ví dụ: 'Thuốc Hồi Máu')
        self.type = item_type        # Phân loại: 'consumable' (tiêu thụ), 'material' (nguyên liệu)
        self.description = description
        self.value = value          # Chỉ số hồi phục hoặc giá trị của vật phẩm

    def use(self, player):
        """Hàm xử lý khi sử dụng vật phẩm này. Trả về True nếu dùng thành công."""
        if self.type == 'consumable':
            if self.id == 'potion_red':
                # Hồi máu cho Player nhưng không vượt quá máu tối đa
                max_health = player.stats['health']
                if player.health >= max_health:
                    print("Máu đã đầy, không thể sử dụng!")
                    return False
                
                player.health = min(max_health, player.health + self.value)
                print(f"Uống {self.name}! Hồi {self.value} HP. Máu hiện tại: {player.health}")
                return True
                
            elif self.id == 'potion_energy':
                # Hồi năng lượng cho Player
                max_energy = player.stats['energy']
                if player.energy >= max_energy:
                    print("Năng lượng đã đầy!")
                    return False
                
                player.energy = min(max_energy, player.energy + self.value)
                print(f"Dùng {self.name}! Hồi {self.value} Năng lượng.")
                return True

        print(f"Vật phẩm {self.name} không thể sử dụng trực tiếp!")
        return False