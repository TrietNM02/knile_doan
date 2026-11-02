# ⚔️ KNIGHT TILE (GAME ROGUELIKE 2D)

Đồ án Game 2D phong cách Roguelike/Turn-based được viết bằng Python & Pygame, hỗ trợ hệ thống Kỹ năng, Cây kỹ năng (Skill Tree), NPC Shop, Lưu/Tải game (Save/Load) và Hệ thống giám sát an ninh (Anti-Cheat Log).

---

## 🛠️ 1. Yêu Cầu Hệ Thống & Cài Đặt Thư Viện

### Yêu cầu
* **Python**: Phiên bản `3.9` đến `3.12` (Khuyên dùng `Python 3.10` trở lên).
* **Tiled Map Editor**: Tùy chọn (Nếu muốn xem hoặc chỉnh sửa bản đồ `.tmx`).

### Các thư viện sử dụng trong đồ án:
1. `pygame`: Thư viện đồ họa, âm thanh và xử lý logic game.
2. `PyTMX`: Thư viện đọc và tải dữ liệu bản đồ dạng `.tmx` tạo bởi Tiled.

---

### 📦 Hướng dẫn cài đặt thư viện bằng Command Prompt (cmd) hoặc Terminal

Mở terminal tại thư mục gốc của đồ án (`trietnm02-knile_doan`) và chạy lệnh:

```bash
pip install pygame pytmx
```

*Nếu bạn sử dụng Python 3 trên macOS/Linux:*
```bash
pip3 install pygame pytmx
```

---

## 🚀 2. Hướng Dẫn Chạy Game

1. **Mở Terminal/Command Prompt** tại thư mục đồ án:
   ```bash
   cd trietnm02-knile_doan/src
   ```

2. **Chạy tệp `main.py`**:
   ```bash
   python main.py
   ```
   *(Hoặc `python3 main.py` tùy theo cấu hình thiết bị)*.

---

## 🗺️ 3. Hướng Dẫn Mở và Chỉnh Sửa Bản Đồ (Map) bằng Tiled

Đồ án sử dụng **Tiled Map Editor** để thiết kế bản đồ 2D dạng Tilemap (`.tmx`).

### Bước 1: Tải và cài đặt Tiled Map Editor
* Truy cập trang chủ: [https://www.mapeditor.org/](https://www.mapeditor.org/)
* Tải bản cài đặt phù hợp với hệ điều hành (Windows/macOS) và tiến hành cài đặt.

### Bước 2: Mở File Map trong Đồ Án
1. Khởi động ứng dụng **Tiled**.
2. Chọn **File** -> **Open File...** (hoặc nhấn `Ctrl + O`).
3. Trỏ đường dẫn đến tệp map trong dự án:
   `trietnm02-knile_doan/data/map.tmx` *(hoặc mở project file `data/map.tiled-project`)*.

### Bước 3: Cấu trúc các Layer chính trên Map
Khi mở map ra, bạn sẽ thấy các Layer quan trọng bên góc phải:
* `Decoration`: Cây cối, đồ vật trang trí có va chạm.
* `Collision`: Các ô chặn va chạm (tường tàng hình).
* `Water` / `Water Foam` / `Elevated`: Các lớp địa hình nước, bọt nước và đất cao.
* `Trees`: Đối tượng cây cối có thể chặt/gây sát thương.
* `Player`: Vị trí Spawn ban đầu của người chơi (`Player`).
* `NPC`: Vị trí đặt các NPC thương nhân.
* `Enemy`: Vị trí Spawn quái vật thường và Boss (`rock_boss`, `lava_slime_boss`, v.v.).

### Bước 4: Lưu bản đồ sau khi sửa
* Sau khi chỉnh sửa xong, nhấn `Ctrl + S` để lưu trực tiếp vào tệp `data/map.tmx`.
* Khởi động lại game (`python main.py`) để xem thay đổi trên bản đồ mới!

---

## 🎮 4. Phím Tắt Điều Khiển Trong Game

* `W` `A` `S` `D`: Di chuyển nhân vật theo các hướng.
* `SPACE`: Đánh thường bằng vũ khí hiện tại.
* `1`, `2`, `3`, `4`: Dùng Kỹ năng (Skill) gắn ở ô tương ứng.
* `H`: Sử dụng bình máu (Potion Red).
* `E`: Mở/Đóng Giao diện Túi đồ (Balo), Cây kỹ năng (Skill Tree) & Liên kết kỹ năng (Skill Link).
* `F`: Tương tác / Nói chuyện với NPC (Mở Shop mua bán).
* `ESC`: Mở Menu Pause (Lưu game, Cài đặt âm lượng, Thoát menu chính).

---

## 🛡️ 5. Hệ Thống An Ninh (Anti-Cheat & Security Logs)

Hệ thống Anti-Cheat (`anticheat.py`) tự động kiểm tra chỉ số người chơi:
* Khi khởi động game, hệ thống sẽ tự động quét file log vi phạm `game_cheat_logs.csv` (kiểm tra ngoại lệ `FileNotFoundError` và `ValueError`).
* Nếu phát hiện chỉ số bất thường (Energy hoặc Health vượt quá mức cho phép `900.0`), game sẽ lập tức khóa truy cập và xuất file báo cáo chi tiết `anticheat_report.json`.