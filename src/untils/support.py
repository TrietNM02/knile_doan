import os
import pygame
from untils.spritesheet import *

def load_effect_frames(path, info):
    """Load danh sách frame ảnh từ đường dẫn path được chỉ định"""
    frames = []

    if not path or not os.path.exists(path):
        return frames

    # 1. Nếu là FILE ảnh (spritesheet hoặc ảnh đơn)
    if os.path.isfile(path):
        try:
            sheet = pygame.image.load(path).convert_alpha()
            fw = info.get("frame_width", sheet.get_width())
            fh = info.get("frame_height", sheet.get_height())
            cols = info.get("cols", 1)
            rows = info.get("rows", 1)
            total_frames = info.get("total_frames", cols * rows)
            scale = info.get("scale", 1.0)

            count = 0
            for r in range(rows):
                for c in range(cols):
                    if count >= total_frames:
                        break
                    frame_img = load_spritesheet(sheet, fw, fh, r, c, scale)
                    frames.append(frame_img)
                    count += 1
                if count >= total_frames:
                    break
        except Exception as e:
            print(f"❌ Lỗi load spritesheet {path}: {e}")

    # 2. Nếu là THƯ MỤC chứa nhiều ảnh lẻ
    elif os.path.isdir(path):
        scale = info.get("scale", 1.0)
        for f in sorted(os.listdir(path)):
            if f.lower().endswith((".png", ".jpg", ".jpeg")):
                full_path = os.path.join(path, f)
                try:
                    img = pygame.image.load(full_path).convert_alpha()
                    if scale != 1.0:
                        new_size = (
                            int(img.get_width() * scale),
                            int(img.get_height() * scale),
                        )
                        img = pygame.transform.scale(img, new_size)
                    frames.append(img)
                except Exception as e:
                    print(f"❌ Lỗi load ảnh {f}: {e}")

    return frames

_SKILL_ICON_CACHE = {}
def get_skill_icon(skill_name, info, size, font=None):
    """
    Lấy icon Skill, có cache theo (skill_name, size).
    Đã bỏ 'self' để làm hàm độc lập (Utility Function).
    """
    cache_key = (skill_name, size)
    
    # 1. Kiểm tra Cache toàn cục (Dùng _SKILL_ICON_CACHE thay vì self._skill_icon_cache)
    if cache_key in _SKILL_ICON_CACHE:
        return _SKILL_ICON_CACHE[cache_key]

    inner_size = max(1, size - 8)
    surf = None

    # 2. Ưu tiên 'icon_path'
    icon_path = info.get('icon_path') if isinstance(info, dict) else None
    if icon_path and os.path.exists(icon_path):
        try:
            surf = pygame.image.load(icon_path).convert_alpha()
        except Exception as e:
            print(f"[LỖI ICON SKILL '{skill_name}']: {e}")
            surf = None

    # 3. Mượn tạm ảnh đầu tiên trong effect_path nếu không có icon riêng
    if surf is None and isinstance(info, dict):
        effect_path = info.get('effect_path', '')
        if effect_path and os.path.isdir(effect_path):
            try:
                png_files = sorted(f for f in os.listdir(effect_path) if f.endswith('.png'))
                if png_files:
                    surf = pygame.image.load(os.path.join(effect_path, png_files[0])).convert_alpha()
            except Exception as e:
                print(f"[LỖI ICON SKILL '{skill_name}']: {e}")
                surf = None

    if surf is not None:
        surf = pygame.transform.smoothscale(surf, (inner_size, inner_size))
    else:
        # 4. Fallback: vẽ ô vuông màu và chữ ngắn
        surf = pygame.Surface((inner_size, inner_size), pygame.SRCALPHA)
        surf.fill((90, 90, 150, 255))
        
        label = info.get('name', skill_name) if isinstance(info, dict) else str(skill_name)
        short_label = label[:6] + '.' if len(label) > 6 else label
        
        # Nếu truyền font vào thì dùng, không thì tạo font mặc định
        use_font = font if font else pygame.font.Font(None, 16)
        text_surf = use_font.render(short_label, True, (255, 255, 255))
        surf.blit(text_surf, text_surf.get_rect(center=(inner_size // 2, inner_size // 2)))

    # Lưu vào Cache toàn cục và trả về
    _SKILL_ICON_CACHE[cache_key] = surf
    return surf
