import pygame

from untils.settings import *

def load_spritesheet(sheet, frame_width, frame_height, rows, cols, scale):
    image = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
    x = frame_width * cols
    y = frame_height * rows
    image.blit(sheet, (0, 0), (x, y, frame_width, frame_height))
    image = pygame.transform.scale(image, (int(frame_width * scale), int(frame_height * scale)))

    return image.convert_alpha()