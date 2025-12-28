import pygame
import json
from utils import load_image
from constants import *


def load_level(level_num):
    world_data = []

    for row in range(ROWS):
        r = [-1] * MAX_COLS
        world_data.append(r)

    with open(f"assets/Levels/level_{level_num}.json", "r") as file:
        data = json.load(file)

    for y, row in enumerate(data):
        for x, tile in enumerate(row):
            world_data[y][x] = tile

    return world_data


def load_tile_images():
    img_list = []
    for x in range(TILE_TYPES):
        img = load_image(f'{x + 1}', 'Level Editor Tiles')
        img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))   
        if x == 5:
            img = pygame.transform.flip(img, True, False)

        img_list.append(img)

    return img_list


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


# world_data = load_level(0)
# print(world_data)
