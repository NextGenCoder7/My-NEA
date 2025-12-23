# This file contains utility functions for the game

import pygame
from constants import *
from os import listdir
from os.path import isfile, join


def load_image(filename, dir1, dir2=None, dir3=None):
    """
    Load an image from the assets directory with up to three nested directories.

    Args:
        filename (str): Image filename without extension.
        dir1 (str): Top-level asset folder name.
        dir2 (str, optional): Second-level folder name.
        dir3 (str, optional): Third-level folder name.

    Returns:
        Surface: Pygame Surface loaded with convert_alpha().
    """
    if dir3 is not None:
        return pygame.image.load(join('assets', dir1, dir2, dir3, f"{filename}.png")).convert_alpha()
    elif dir2 is not None:
        return pygame.image.load(join('assets', dir1, dir2, f"{filename}.png")).convert_alpha()
    else:
        return pygame.image.load(join('assets', dir1, f"{filename}.png")).convert_alpha()


def flip(sprites):
    """
    Return a new list of surfaces horizontally flipped from the input list.
    """
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]


def load_player_sprite_sheets(dir1, dir2, width, height, direction=False):
    """
    Loads player sprite sheets from the assets folder and returns a dictionary of frames.

    Args:
        dir1 (str): Folder under assets to search.
        dir2 (str): Subfolder under dir1.
        width (int): Width of each frame in source sprite sheets.
        height (int): Height of each frame in source sprite sheets.
        direction (bool): If True, produce both left/right flipped versions for animations.

    Returns:
        dict: Mapping of sprite names to lists of scaled frames.
    """
    path = join("assets", dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path, f))]

    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()

        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            surface.blit(sprite_sheet, (-i * width, 0))
            
            scale_width = TILE_SIZE - 8
            scale_height = int((height / width) * scale_width)  
            sprites.append(pygame.transform.scale(surface, (scale_width, scale_height)))

        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites


def load_gem_sprite_sheets(width, height):
    """
    Loads gem sprite sheets from the assets folder and returns a dictionary of frames.

    Args:
        width (int): Width of each frame in source sprite sheets.
        height (int): Height of each frame in source sprite sheets.

    Returns:
        dict: Mapping of sprite names to lists of scaled frames.
    """

    path = join("assets", "Objects", "Gems")
    images = [f for f in listdir(path) if isfile(join(path, f))]

    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()

        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            surface.blit(sprite_sheet, (-i * width, 0))

            scale_width = TILE_SIZE // 2
            scale_height = int((height / width) * scale_width)  
            sprites.append(pygame.transform.scale(surface, (scale_width, scale_height)))

            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites


def draw_bg(bg1, win, scroll):
    """
    Draw a scrolling background for the game window.

    Args:
        bg1 (Surface): Background image to tile.
        win (Surface): Window surface to draw onto.
        scroll (float): Current horizontal scroll value used for parallax.
    """
    for x in range(10):
        bg1_scaled = pygame.transform.scale(bg1, (WIDTH, HEIGHT))
        win.blit(bg1_scaled, ((x * WIDTH) - scroll * 0.1, 0))


def draw_text_middle(text, fontname, size, color, win):
    """
    Draws text centered in the window.

    Args:
        text (str): Text to render.
        fontname (str): System font name.
        size (int): Font size.
        color (tuple): RGB color.
        win (Surface): Surface to draw on.
    """

    font = pygame.font.SysFont(fontname, size, bold=False)
    label = font.render(text, 1, color)

    win.blit(label, (WIDTH // 2 - label.get_width() // 2, HEIGHT // 2 - label.get_height() // 2))


def draw_text(text, fontname, size, color, win, x, y, bold=False):
    """
    Draw text at a specific position in the window.

    Args:
        text (str): Text to render.
        fontname (str): System font name.
        size (int): Font size.
        color (tuple): RGB color.
        win (Surface): Surface to draw on.
        x (int): X position.
        y (int): Y position.
    """

    font = pygame.font.SysFont(fontname, size, bold)
    label = font.render(text, 1, color)

    win.blit(label, (x, y))


def load_ammo_sprites(character):
    """
    Load enemy ammo sprites from individual files for each animation frame.
    """

    if character == "Fierce Tooth" or character == "Seashell Pearl":
        path = join("assets", "Enemies", character)
    elif character == "Player":
        path = join("assets", "Main Characters")

    all_sprites = {}
    
    # Animation folders to load
    if character == "Fierce Tooth":
        animations = ["Cannon Ball Flying", "Cannon Ball Explosion", "Cannon Ball Destroyed"]
    elif character == "Seashell Pearl":
        animations = ["Pearl Idle", "Pearl Explosion", "Pearl Destroyed"]
    elif character == "Player":
        animations = ["Grenade Idle", "Explosion"]
    
    for animation in animations:
        animation_path = join(path, animation)
        if not isfile(animation_path):    
            try:
                files = [f for f in listdir(animation_path) if f.endswith('.png')]
                files.sort()
                
                sprites = []
                for file in files:
                    sprite = pygame.image.load(join(animation_path, file)).convert_alpha()
                    if animation == "Cannon Ball Explosion" or animation == "Pearl Explosion":
                        scale_width = scale_height = TILE_SIZE
                    elif animation == "Explosion":
                        scale_width = scale_height = TILE_SIZE * 4
                    elif animation == "Pearl Idle":
                        scale_width = scale_height = TILE_SIZE // 2
                    elif animation == "Grenade Idle":
                        scale_width = scale_height = TILE_SIZE // 3
                    else:
                        scale_width = scale_height = TILE_SIZE // 4
                    sprite = pygame.transform.scale(sprite, (scale_width, scale_height))
                    sprites.append(sprite)
                
                all_sprites[animation] = (sprites)
            except:
                continue
    
    return all_sprites


def load_enemy_sprites(enemy_type, width, height):
    """
    Load enemy sprites from individual files for each animation frame.
    """
    path = join("assets", "Enemies", enemy_type)
    all_sprites = {}
    
    # Animation folders to load
    if enemy_type == "Fierce Tooth":
        animations = ["Idle", "Run", "Jump", "Fall", "Dead", "Attack", "Recover", "Hit"]
    elif enemy_type == "Pink Star":
        animations = ["Idle", "Run", "Jump", "Fall", "Dead", "Attack", "Hit", "Recover"]
    elif enemy_type == "Seashell Pearl":
        animations = ["Idle", "Seashell Bite", "Seashell Fire", "Seashell Hit", "Seashell Recover", "Dead"]

    for animation in animations:
        animation_path = join(path, animation)
        if not isfile(animation_path):    
            try:
                files = [f for f in listdir(animation_path) if f.endswith('.png')]
                files.sort()
                
                sprites = []
                for file in files:
                    sprite = pygame.image.load(join(animation_path, file)).convert_alpha()
                    scale_width = TILE_SIZE - 8 if enemy_type != "Seashell Pearl" else TILE_SIZE
                    scale_height = int((height / width) * scale_width)
                    sprite = pygame.transform.scale(sprite, (scale_width, scale_height))
                    sprites.append(sprite)
                
                all_sprites[animation + "_right"] = flip(sprites)
                all_sprites[animation + "_left"] = (sprites)
            except:
                continue
    
    return all_sprites
