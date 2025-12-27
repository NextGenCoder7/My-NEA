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


class World:

    def __init__(self, img_list):
        self.obstacle_list = []
        self.img_list = img_list

    def process_data(self, data):
        for y, row in enumerate(data):
            for x, tile in enumerate(row):
                if tile >= 0:
                    img = self.img_list[tile]
                    img_rect = img.get_rect()
                    img_rect.x = x * TILE_SIZE
                    img_rect.y = y * TILE_SIZE
                    tile_data = (img, img_rect)

                    if tile >= 0 and tile <= 14:
                        self.obstacle_list.append(tile_data)
                    elif tile >= 15 and tile <= 16:
                        pass # hazards
                    elif tile == 17 or tile == 28:
                        pass # literal flags
                    elif tile == 18:
                        pass # player
                    elif tile == 19:
                        pass # Fiercetooth
                    elif tile == 20:
                        pass # Pink Star
                    elif tile == 21:
                        pass # Seashell Pearl
                    elif tile >= 22 and tile <= 24:
                        pass # collectible gems/coins
                    elif tile == 25 or tile == 26 or tile == 29:
                        pass # enemy constraint rectangles
                    elif tile == 27:
                        pass # grenade boxes


# world_data = load_level(0)
# print(world_data)
