"""
Project: Anti-Cheat & Security Log System
Author: Nguyễn Minh Triết
module: anticheat.py
Mô tả: Hệ thống giám sát và báo cáo gian lận trong game

"""

import json
import os
from datetime import datetime

class AntiCheatSystem:
    """Hệ thống giám sát và báo cáo gian lận (Anti-Cheat & Security Log)"""
    def __init__(self, max_allowed_energy=900.0, max_allowed_health=900.0):
        self.max_energy = max_allowed_energy
        self.max_health = max_allowed_health

        # CÂU 3.3: Khai báo các cấu trúc dữ liệu bắt buộc
        self.cheat_logs = []             # List chứa danh sách các bản ghi (Tuple)
        self.blacklisted_players = set() # Set lọc trùng danh sách người chơi bị cấm
        self.cheat_counts = {}           # Dict đếm tần suất vi phạm theo loại hack

    def check_and_log(self, player_id: str, cheat_type: str, value: float):
        """Kiểm tra và ghi nhận vi phạm khi có dấu hiệu gian lận"""
        # CÂU 3.1: Chuẩn hóa chuỗi (strip, upper/lower)
        p_id = player_id.strip().upper()
        c_type = cheat_type.strip().lower()
        val = float(value)

        # CÂU 3.3: Dùng Tuple để lưu trữ bản ghi an ninh cố định
        log_record = (p_id, c_type, val, datetime.now().strftime("%H:%M:%S"))
        self.cheat_logs.append(log_record)

        # CÂU 3.3: Thống kê tần suất vi phạm bằng Dict và lọc trùng bằng Set
        self.cheat_counts[c_type] = self.cheat_counts.get(c_type, 0) + 1
        self.blacklisted_players.add(p_id)

    def scan_external_log_file(self, file_path: str) -> bool:
        """ Đọc file log bên ngoài, xử lý chuỗi và BẮT 2 NGOẠI LỆ"""
        # NGOẠI LỆ 1: Lỗi không tìm thấy file
        if not os.path.exists(file_path):
            print(f"[NGOẠI LỆ 1 - FileNotFoundError]: Tệp '{file_path}' không tồn tại!")
            return False

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, start=1):
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    
                    parts = line.split(',')
                    if len(parts) < 3:
                        continue
                    
                    p_id, c_type, val_str = parts[0], parts[1], parts[2]
                    
                    # NGOẠI LỆ 2: Lỗi sai kiểu dữ liệu số (ValueError)
                    try:
                        val = float(val_str)
                        self.check_and_log(p_id, c_type, val)
                    except ValueError:
                        print(f"[NGOẠI LỆ 2 - ValueError]: Dữ liệu hỏng ở dòng {line_num}: '{val_str}'")

            return True
        except Exception as e:
            print(f"[LỖI XỬ LÝ]: {e}")
            return False

    def export_anticheat_report(self, output_path: str = "anticheat_report.json"):
        """Xuất báo cáo an ninh ra tệp JSON"""
        report_data = {
            "report_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_cheats_detected": len(self.cheat_logs),
            "blacklisted_players": list(self.blacklisted_players), # Set -> List để lưu JSON
            "cheat_type_summary": self.cheat_counts,
            "detailed_incident_tuples": self.cheat_logs
        }
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=4, ensure_ascii=False)
            print(f"-> [THÀNH CÔNG] Đã xuất báo cáo an ninh ra tệp: '{output_path}'")
        except IOError as e:
            print(f"[LỖI GHI FILE]: {e}")