import pygame
import os

class SoundManager:
    def __init__(self, game=None):
        self.game = game
        
        # 🟢 Khởi tạo mixer
        if not pygame.mixer.get_init():
            pygame.mixer.pre_init(44100, -16, 2, 512)
            pygame.mixer.init()

        # 🟢 Đường dẫn tuyệt đối đến thư mục gốc
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

        self.sfx_volume = 0.8
        self.bgm_volume = 0.5
        self.is_muted = False

        self.sounds = {}
        self.current_bgm = None

        # 🟢 Map đúng các key SFX (Gồm cả 'slash' và 'attack')
        self.load_sfx('slash', 'audio/Slash.wav')
        self.load_sfx('attack', 'audio/Slash.wav')
        self.load_sfx('fireball', 'audio/skill/Fireball.wav')
        self.load_sfx('waterball', 'audio/skill/Waterball.wav')
        self.load_sfx('wind_blast', 'audio/skill/WindBlast.wav')
        self.load_sfx('jump_stomp', 'audio/skill/Stomp.wav')
        self.load_sfx('flame_slam', 'audio/skill/Stomp.wav')
        self.load_sfx('water_spout', 'audio/skill/Twister.wav')

    def load_sfx(self, key, relative_path):
        full_path = os.path.join(self.base_dir, relative_path)

        if os.path.exists(full_path):
            try:
                sound = pygame.mixer.Sound(full_path)
                sound.set_volume(0 if self.is_muted else self.sfx_volume)
                self.sounds[key] = sound
                print(f"[SOUND OK] Loaded: {key}")
            except Exception as e:
                print(f"[SOUND ERROR] Lỗi file {full_path}: {e}")
        else:
            print(f"[SOUND WARNING] Không thấy file: {full_path}")

    def play_sfx(self, key):
        if self.is_muted:
            return
        if key in self.sounds:
            self.sounds[key].play()

    def play_bgm(self, relative_path='audio/theme/dewford_town.mp3', loop=-1):
        full_path = os.path.join(self.base_dir, relative_path)

        if self.current_bgm == full_path:
            return

        if os.path.exists(full_path):
            try:
                pygame.mixer.music.load(full_path)
                pygame.mixer.music.set_volume(0 if self.is_muted else self.bgm_volume)
                pygame.mixer.music.play(loop)
                self.current_bgm = full_path
                print(f"[BGM OK] Đang phát nhạc nền!")
            except Exception as e:
                print(f"[SOUND ERROR] Lỗi BGM {full_path}: {e}")
        else:
            print(f"[BGM WARNING] Không thấy BGM tại: {full_path}")

    def stop_bgm(self):
        pygame.mixer.music.stop()
        self.current_bgm = None

# 🟢 CHẠY TRỰC TIẾP FILE NÀY ĐỂ TEST SỐNG ÂM THANH
if __name__ == '__main__':
    pygame.init()
    screen = pygame.display.set_mode((300, 200))
    pygame.display.set_caption("Test Sound")
    sm = SoundManager()
    
    # Bật nhạc
    sm.play_bgm('audio/theme/dewford_town.mp3')
    
    print("\n--- ĐANG TEST ÂM THANH ---")
    print(" Bấm SPACE -> Tiếng Slash")
    print(" Bấm 1     -> Fireball")
    print(" Bấm 2     -> Waterball")
    print(" Bấm ESC   -> Thoát\n")
    
    running = True
    clock = pygame.time.Clock()
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    print("--> Phát tiếng Slash")
                    sm.play_sfx('slash')
                elif event.key == pygame.K_1:
                    print("--> Phát Fireball")
                    sm.play_sfx('fireball')
                elif event.key == pygame.K_2:
                    print("--> Phát Waterball")
                    sm.play_sfx('waterball')

        clock.tick(30)
    pygame.quit()