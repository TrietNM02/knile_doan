import pygame, sys

from settings import *

from level import Level

from menu import Menu

class Game:
    def __init__(self):
        pygame.init()
        
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('Knight Tile')

        self.state = 'menu'
        self.menu = Menu(self.screen)
        self.clock = pygame.time.Clock()
        self.level = Level()


    def run(self):
        while True:

            dt = self.clock.tick() / 1000

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if self.state == 'menu':
                    menu_action = self.menu.handle_event(event)
                    if menu_action == 'start_game':
                        self.level = Level() # Khởi tạo gameplay
                        self.state = 'playing'

                # Xử lý sự kiện khi đang PLAYING (chuột, phím bấm...)
                elif self.state == 'playing':
                    if hasattr(self.level, 'handle_event'):
                        self.level.handle_event(event)

            if self.state == 'menu':
                self.menu.draw()

            elif self.state == 'playing':
                if self.level:
                    self.level.run(dt)
            
            pygame.display.update()
            

if __name__ == '__main__':
    game = Game()
    game.run()