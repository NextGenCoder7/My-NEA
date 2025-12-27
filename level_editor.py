import pygame
from constants import *
from utils import *
from button import Button
import json
import os

pygame.init()

level_editor_WIN = pygame.display.set_mode((WIDTH + SIDE_MARGIN, HEIGHT + LOWER_MARGIN))
pygame.display.set_caption(LEVEL_EDITOR_TITLE)


def draw_grid(win, scroll):
    """
    Draw the level editor grid lines on the provided surface.

    Args:
        win (Surface): Surface to draw the grid on.
        scroll (int): Horizontal scroll offset used to offset vertical grid lines.
    """
    # vertical lines
    for c in range(MAX_COLS + 1):
        pygame.draw.line(win, WHITE, (c * TILE_SIZE - scroll, 0), (c * TILE_SIZE - scroll, HEIGHT))
    # horizontal lines
    for r in range(ROWS + 1):
        pygame.draw.line(win, WHITE, (0, r * TILE_SIZE), (WIDTH, r * TILE_SIZE))


def draw_window(win, bg1, scroll, current_tile, save_button, load_button, level, buttons_list=None, world_data=None, img_list=None):
    """
    Render the level editor window including background, grid, tiles, and UI.

    Returns the potentially-updated current_tile and world_data.
    """
    draw_bg(bg1, win, scroll)
    
    # draw grid lines
    draw_grid(win, scroll)

    # draw world
    if isinstance(world_data, list) and isinstance(img_list, list):
        for y, row in enumerate(world_data):
            for x, tile in enumerate(row):
                if tile >= 0:
                    win.blit(img_list[tile], (x * TILE_SIZE - scroll, y * TILE_SIZE))
    
    # draw level num text 
    pygame.draw.rect(win, BLACK, (10, HEIGHT + LOWER_MARGIN - 90, 200, 40))
    draw_text(f"Level: {level}", 'Futura', 30, WHITE, win, 10, HEIGHT + LOWER_MARGIN - 90)

    # draw save button
    if save_button.draw(win):
        with open(f"assets/Levels/level_{level}.json", "w") as file:
            json.dump(world_data, file)
        print(f"Level {level} data saved!")

    # draw load button
    if load_button.draw(win):
        if os.path.exists(f"assets/Levels/level_{level}.json"):
            with open(f"assets/Levels/level_{level}.json", "r") as file:
                world_data = json.load(file)
            print(f"Level {level} data loaded!")
        else:
            print(f"No saved data for level {level}.")

    pygame.draw.rect(win, BLACK, (WIDTH, 0, SIDE_MARGIN, HEIGHT + LOWER_MARGIN))

    # draw tile buttons
    if isinstance(buttons_list, list):
        button_count = 0
        for button_count, i in enumerate(buttons_list):
            if i.draw(win):
                current_tile = button_count
    
    # draw red highlighter around tile buttons
    pygame.draw.rect(win, RED, buttons_list[current_tile].rect, 3)

    pygame.display.update()

    return current_tile, world_data
    

def main_level_editor():
    """
    Main loop for the level editor UI.

    Handles input, scrolling, and editing world_data which represents the tile map.
    """
    clock = pygame.time.Clock()

    bg1 = load_image('1', 'Locations', 'Backgrounds', 'Blue Nebula')

    save_img = load_image('save_btn', 'GUI', 'Buttons')
    load_img = load_image('load_btn', 'GUI', 'Buttons')

    img_list = []
    for x in range(TILE_TYPES):
        img = load_image(f'{x + 1}', 'Level Editor Tiles')
        img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
        if x == 5:
            img = pygame.transform.flip(img, True, False)

        img_list.append(img)

    save_button = Button(WIDTH // 3, HEIGHT + LOWER_MARGIN - 80, save_img, 1)
    load_button = Button(WIDTH // 2 + 150, HEIGHT + LOWER_MARGIN - 80, load_img, 1)

    buttons_list = []
    button_col, button_row = 0, 0  

    for i in range(len(img_list)):
        tile_button = Button(WIDTH + (TILE_BTN_SPACING_X * button_col) + TILE_BTN_OFFSET_X,
                             TILE_BTN_SPACING_Y * button_row + TILE_BTN_OFFSET_Y, img_list[i], 1)
        buttons_list.append(tile_button)
        button_col += 1
        if button_col == 3:
            button_row += 1
            button_col = 0

    current_tile = 0
    level = 0

    world_data = []
    for _ in range(ROWS):
        r = [-1] * MAX_COLS
        world_data.append(r)

    if level == 0:    # gonna create and use this one for testing game features during analysis
        for tile in range(0, MAX_COLS):
            world_data[ROWS - 1][tile] = 0

    scroll_left = False
    scroll_right = False
    scroll = 0
    scroll_speed = 1

    run = True
    while run:
        clock.tick(FPS)

        current_tile, world_data = draw_window(level_editor_WIN, bg1, scroll, current_tile, save_button, load_button, level, buttons_list, world_data, img_list)

        if scroll_left and scroll > 0:
            scroll -= 5 * scroll_speed
        if scroll_right and scroll < (MAX_COLS * TILE_SIZE) - WIDTH:
            scroll += 5 * scroll_speed

        pos = pygame.mouse.get_pos()
        x = (pos[0] + scroll) // TILE_SIZE
        y = pos[1] // TILE_SIZE

        if pos[0] < WIDTH and pos[1] < HEIGHT:
            if pygame.mouse.get_pressed()[0] == 1:
                if world_data[y][x] != current_tile:
                    world_data[y][x] = current_tile
            if pygame.mouse.get_pressed()[2] == 1:
                world_data[y][x] = -1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    run = False
                if event.key == pygame.K_LEFT:
                    scroll_left = True
                if event.key == pygame.K_RIGHT:
                    scroll_right = True
                if event.key == pygame.K_RSHIFT:
                    scroll_speed = 5
                if event.key == pygame.K_UP:
                    level += 1
                if event.key == pygame.K_DOWN and level > 0:
                    level -= 1

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT:
                    scroll_left = False
                if event.key == pygame.K_RIGHT:
                    scroll_right = False
                if event.key == pygame.K_RSHIFT:
                    scroll_speed = 1
    
    pygame.quit()


main_level_editor()
