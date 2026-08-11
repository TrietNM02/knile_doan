import pygame

from item import Item

class Inventory:
    def __init__(self, total_slots=16):
        self.total_slots = total_slots
        # Khởi tạo danh sách các ô đồ. Ban đầu tất cả các ô đều rỗng (None)
        # Cấu trúc mỗi ô khi có đồ: {'item': Item_Object, 'amount': X}
        self.slots = [None] * self.total_slots
        self.equipped_weapon = None # Ô chứa vũ khí đang trang bị

    def add_item(self, item_id, item_database, amount=1):
        if item_id not in item_database:
            print(f"❌ Không tìm thấy item_id '{item_id}' trong database!")
            return False

        data = item_database[item_id]

        # 1. Tìm xem item này đã tồn tại trong balo chưa để cộng dồn (Stack). Nếu 0 phải vũ khí
        if data['type'] != 'weapon':
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
                # print(f"🎒 Nhét vào ô {i}: +{amount} {new_item.name}")
                return True

        print("❌ Hành trang đã đầy! Không thể nhặt thêm.")
        return False

    def equip_weapon_from_slot(self, slot_index, player):
        """Trang bị vũ khí từ ô túi đồ slot_index sang ô equipped_weapon"""
        if not (0 <= slot_index < self.total_slots):
            return False

        slot_data = self.slots[slot_index]
        if not slot_data or slot_data['item'].type != 'weapon':
            return False

        # Tráo đổi giữa vũ khí đang trang bị và vũ khí trong ô túi đồ
        old_equipped = self.equipped_weapon
        self.equipped_weapon = slot_data
        self.slots[slot_index] = old_equipped

        # Cập nhật vũ khí hiện tại cho Player
        player.selected_weapon = self.equipped_weapon['item'].id
        # print(f"⚔️ Đã trang bị: {self.equipped_weapon['item'].name}")
        return True

    def unequip_weapon(self, to_slot_index, player):
        """Gỡ vũ khí đang trang bị đặt vào ô túi đồ to_slot_index"""
        if not self.equipped_weapon:
            return False

        if not (0 <= to_slot_index < self.total_slots):
            return False

        target_slot = self.slots[to_slot_index]

        # Nếu ô đích rỗng hoặc chứa 1 vũ khí khác -> Tráo đổi
        if target_slot is None or target_slot['item'].type == 'weapon':
            self.slots[to_slot_index] = self.equipped_weapon
            self.equipped_weapon = target_slot

            if self.equipped_weapon:
                player.selected_weapon = self.equipped_weapon['item'].id
            else:
                player.selected_weapon = 'sword' # Mặc định nếu tháo hết vũ khí

            return True

        return False

    def use_item_at_slot(self, slot_index, player):
        slot_data = self.slots[slot_index]
        if not slot_data:
            return

        item = slot_data['item']
        
        # 1. Gọi hàm use() của Item
        used_success = item.use(player)

        # 2. CHỈ TRỪ SỐ LƯỢNG / XÓA NẾU LÀ THUỐC (consumable) VÀ DÙNG THÀNH CÔNG!
        # Vũ khí (weapon) hay nguyên liệu (material) thì BỎ QUA không được xóa!
        if used_success and getattr(item, 'type', '') == 'consumable':
            slot_data['amount'] -= 1
            if slot_data['amount'] <= 0:
                self.slots[slot_index] = None