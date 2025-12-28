import pygame
from constants import RED, BLUE, ORANGE


class ConstraintRect(pygame.sprite.Sprite):

    def __init__(self, x, y, width, height, tile_number):
        super().__init__()

        self.color = None
        if tile_number == 25:
            self.color = RED
        elif tile_number == 26:
            self.color = BLUE
        elif tile_number == 29:
            self.color = ORANGE

        self.rect = pygame.Rect(x, y, width, height)   
        
    def draw(self, win):
        pygame.draw.rect(win, self.color, self.rect)
