import pygame

from item import Item

class Inventory:
    def __init__(self, total_slots=16):
        self.total_slots = total_slots
        # Khởi tạo danh sách các ô đồ. Ban đầu tất cả các ô đều rỗng (None)
        # Cấu trúc mỗi ô khi có đồ: {'item': Item_Object, 'amount': X}
        self.slots = [None] * self.total_slots

    def add_item(self, item_id, item_database, amount=1):
        # 1. Tìm xem item này đã tồn tại trong balo chưa để cộng dồn (Stack)
        for slot in self.slots:
            if slot is not None and slot['item'].id == item_id:
                slot['amount'] += amount
                print(f"🎒 Xếp chồng: +{amount} {slot['item'].name}")
                return True

        # 2. Nếu là item mới, tìm ô trống đầu tiên (None) để nhét vào
        for i in range(self.total_slots):
            if self.slots[i] is None:
                data = item_database[item_id]
                new_item = Item(item_id, data['name'], data['type'], data['description'], data['value'])
                self.slots[i] = {
                    'item': new_item,
                    'amount': amount
                }
                print(f"🎒 Nhét vào ô {i}: +{amount} {new_item.name}")
                return True

        print("❌ Hành trang đã đầy! Không thể nhặt thêm.")
        return False

    def use_item_at_slot(self, slot_index, player):
        """Sử dụng vật phẩm tại một ô cụ thể bằng chỉ mục (Index)"""
        if 0 <= slot_index < self.total_slots and self.slots[slot_index] is not None:
            slot_data = self.slots[slot_index]
            item_obj = slot_data['item']

            # Gọi hàm use của Item
            if item_obj.use(player):
                slot_data['amount'] -= 1
                if slot_data['amount'] <= 0:
                    self.slots[slot_index] = None # Trả lại ô trống nếu hết đồ
                return True
        return False