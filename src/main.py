import pygame, sys
from settings import *
from level import Level
from menu import Menu
from save_manager import SaveManager
from sound_manager import SoundManager
from anticheat import AntiCheatSystem

class Game:
    def __init__(self):
        pygame.init()
        
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('Knight Tile')

        # 🟢 Khởi tạo SoundManager và truyền self vào để quản lý chung
        self.sound_manager = SoundManager(game=self)
        
        # 🟢 Bật nhạc nền ngay khi mở game (file MP3 của bạn)
        self.sound_manager.play_bgm('audio/theme/dewford_town.mp3')

        self.state = 'menu'
        self.menu = Menu(self.screen)
        self.clock = pygame.time.Clock()
        self.level = None

        # 🛡️ Khởi tạo hệ thống Anti-Cheat
        self.anticheat_system = AntiCheatSystem(max_allowed_energy=900.0, max_allowed_health=900.0)

        # ⚡ CÂU 3.1 & 3.2: Cho quét 1 file log external để kích hoạt cơ chế bắt Ngoại Lệ khi khởi động
        self.anticheat_system.scan_external_log_file("game_cheat_logs.csv")

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(60) / 1000

            # BẮT GIAN LẬN & THOÁT GAME TỰ ĐỘNG
            if self.state == 'playing' and self.level and hasattr(self.level, 'player'):
                player_obj = self.level.player
                
                # 1. Bắt gian lận energy -> Xuất JSON & Sập game ngay!
                if hasattr(player_obj, 'energy') and player_obj.energy > self.anticheat_system.max_energy:
                    print("\n⛔ [ANTI-CHEAT]: PHÁT HIỆN GIAN LẬN ENERGY HACK! ĐANG LƯU BÁO CÁO VÀ THOÁT GAME...")
                    self.anticheat_system.check_and_log("Player_01", "Energy_Hack", player_obj.energy)
                    running = False

                # 2. Bắt gian lận Health -> Xuất JSON & Sập game ngay!
                if hasattr(player_obj, 'health') and player_obj.health > self.anticheat_system.max_health:
                    print("\n⛔ [ANTI-CHEAT]: PHÁT HIỆN HEALTH HACK! ĐANG LƯU BÁO CÁO VÀ THOÁT GAME...")
                    self.anticheat_system.check_and_log("Player_01", "Health_Hack", player_obj.health)
                    running = False

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if self.state == 'menu':
                    menu_action = self.menu.handle_event(event)
                    
                    if menu_action == 'start_game':
                        self.level = Level(game=self)
                        self.state = 'playing'
                    
                    elif isinstance(menu_action, dict) and menu_action.get('action') == 'load_game':
                        save_data = SaveManager.load_game()
                        if save_data:
                            self.level = Level(game=self)
                            SaveManager.apply_save_to_level(self.level, save_data)
                            self.state = 'playing'

                elif self.state == 'playing':
                    if self.level:
                        self.level.handle_event(event)

            if self.state == 'menu':
                self.menu.draw()

            elif self.state == 'playing':
                if self.level:
                    self.level.run(dt)
            
            pygame.display.update()

        # Xuất file báo cáo JSON trước khi thoát game
        self.anticheat_system.export_anticheat_report("anticheat_report.json")
        pygame.quit()
        sys.exit()

if __name__ == '__main__':
    game = Game()
    game.run()