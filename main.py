import pygame
from constants import *
from utils import *
from player import Player
from fiercetooth import FierceTooth
from seashell_pearl import SeashellPearl
from pink_star import PinkStar

pygame.init()

WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(TITLE)


def draw_window(win, bg1, player, scroll, player_ammo_group, player_grenade_group, seashell_group, pearl_ammo_group, fiercetooth_group, cannonball_group, pinkstar_group):
    """
    Render the main gameplay window for the current frame.

    Draws background, player, enemies, ammo, and optional debug visuals.

    Args:
        win (Surface): Surface to draw everything on.
        bg1 (Surface): Background image.
        player (Player): Player instance to draw and query.
        scroll (int): Horizontal scroll offset for parallax backgrounds.
        player_ammo_group (Group): Group containing player projectiles.
        seashell_group (Group): Group containing enemy seashell instances.
        cannon_ball_group (Group): Group containing enemy projectiles.
    """

    draw_bg(bg1, win, scroll)
    pygame.draw.line(win, RED, (0, 400), (WIDTH, 400))   # temporary floor

    player.draw(win)
    player.draw_health_bar(win)

    for enemy in fiercetooth_group:
        enemy.draw(win)
        enemy.draw_health_bar(win)
        # enemy.draw_vision_cone(win, player)   # for debugging enemy vision

    for enemy in seashell_group:
        enemy.draw(win)
        enemy.draw_health_bar(win)
        # enemy.draw_vision_cone(win, player)   # for debugging enemy vision

    for ammo in pearl_ammo_group:
        ammo.draw(win)

    for cannon_ball in cannonball_group:
        cannon_ball.draw(win)

    for ammo in player_ammo_group:
        ammo.draw(win)

    for grenade in player_grenade_group:
        grenade.draw(win)

    # for enemy in pinkstar_group:
    #     enemy.draw(win)
    #     enemy.draw_health_bar(win)

    pygame.display.update()


def main(win):
    """
    Main function to run the playing game loop.

    Args:
        win (Surface): Main game window surface.
    """
    clock = pygame.time.Clock()

    player_ammo_group = pygame.sprite.Group()
    player_grenade_group = pygame.sprite.Group()
    fiercetooth_group = pygame.sprite.Group()
    cannon_ball_group = pygame.sprite.Group()
    seashell_group = pygame.sprite.Group()
    pearl_group = pygame.sprite.Group()
    pink_star_group = pygame.sprite.Group()

    bg1 = load_image('1', 'Locations', 'Backgrounds', 'Blue Nebula')

    purple_ammo_gem = load_image('24', 'Level Editor Tiles')
    purple_ammo_gem = pygame.transform.scale(purple_ammo_gem, (TILE_SIZE // 4, TILE_SIZE // 4))

    green_gem = load_image('25', 'Level Editor Tiles')
    green_gem = pygame.transform.scale(green_gem, (TILE_SIZE // 4, TILE_SIZE // 4))
    purple_gem = load_image('24', 'Level Editor Tiles')
    purple_gem = pygame.transform.scale(purple_gem, (TILE_SIZE // 4, TILE_SIZE // 4))

    PLAYER_SPRITES = load_player_sprite_sheets('Main Characters', '2', 32, 32, direction=True)
    GRENADE_SPRITES = load_ammo_sprites('Player')
    FIERCETOOTH_SPRITES = load_enemy_sprites('Fierce Tooth', 32, 32)
    CANNON_BALL_SPRITES = load_ammo_sprites('Fierce Tooth')
    SEASHELL_SPRITES = load_enemy_sprites('Seashell Pearl', 32, 32)
    PEARL_SPRITES = load_ammo_sprites('Seashell Pearl')
    PINKSTAR_SPRITES = load_enemy_sprites('Pink Star', 32, 32)

    player = Player(150, HEIGHT // 3, 3, PLAYER_SPRITES, 1000, 50)
    enemy = FierceTooth(600, 300, 2, FIERCETOOTH_SPRITES, 80, True)   
    enemy2 = SeashellPearl(400, 360, 0, SEASHELL_SPRITES, 120, True)     
    enemy3 = PinkStar(200, 300, 3, PINKSTAR_SPRITES, 500)
    fiercetooth_group.add(enemy)
    seashell_group.add(enemy2)
    pink_star_group.add(enemy3)

    enemies = list(fiercetooth_group) + list(seashell_group) 

    scroll_left = False
    scroll_right = False
    scroll = 0
    scroll_speed = 1

    run = True
    while run:
        clock.tick(FPS)

        keys = pygame.key.get_pressed()

        draw_window(win, bg1, player, scroll, player_ammo_group, player_grenade_group, seashell_group, pearl_group, fiercetooth_group, cannon_ball_group, pink_star_group)

        for enemy in fiercetooth_group:  
            if enemy.alive:
                enemy.update(player, CANNON_BALL_SPRITES, cannon_ball_group)
                enemy.handle_movement()           
                enemy.update_sprite(player)

                if hasattr(enemy, 'smartmode') and enemy.smartmode:
                    enemy.check_and_dodge_bullets(player_ammo_group)

                if hasattr(enemy, 'smartmode') and enemy.smartmode:
                    enemy.check_and_dodge_grenades(player_grenade_group)

                if hasattr(enemy, 'was_hit_from_behind') and enemy.was_hit_from_behind:
                    enemy.shoot(CANNON_BALL_SPRITES, cannon_ball_group)
                    enemy.was_hit_from_behind = False

        for enemy in seashell_group:
            if enemy.alive:
                enemy.update(player, PEARL_SPRITES, pearl_group)        
                enemy.update_sprite(player)

                if hasattr(enemy, 'was_hit_from_behind') and enemy.was_hit_from_behind:
                    enemy.fire(PEARL_SPRITES, pearl_group)
                    enemy.was_hit_from_behind = False

        # for enemy in pink_star_group:
        #     if enemy.alive:
        #         enemy.update(player)   
        #         enemy.handle_movement()
        #         enemy.update_sprite(player)

        if player.alive:
            player.update()
            player.handle_movement(keys, enemies)
            # player.handle_movement(keys, pink_star_group)      
            player.update_sprite()

            if player.shoot:
                player.shoot_ammo(purple_ammo_gem, player_ammo_group)
            if player.throw_grenade:
                player.launch_grenade(GRENADE_SPRITES, player_grenade_group)

            if scroll_left and scroll > 0:
                scroll -= 5 * scroll_speed
            if scroll_right and scroll < (MAX_COLS * TILE_SIZE) - WIDTH:
                scroll += 5 * scroll_speed
        else:
            pass    # Player is dead; need to code screen fade (later)

        for ammo in player_ammo_group:
            ammo.update(enemies)   
            # ammo.update(pink_star_group)

        for grenade in player_grenade_group:
            grenade.update(player, enemies)
            # grenade.update(player, pink_star_group)
            grenade.update_sprite()

        for cannon_ball in cannon_ball_group:
            cannon_ball.update(player)
            cannon_ball.update_sprite()

        for pearl in pearl_group:
            pearl.update(player)
            pearl.update_sprite()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    run = False
                if event.key in (pygame.K_UP, pygame.K_w):
                    player.jump()
                if event.key == pygame.K_SPACE:
                    if player.alive:
                        player.shoot = True
                if event.key == pygame.K_g:
                    if player.alive:
                        player.throw_grenade = True
    
    pygame.quit()


if __name__ == "__main__":
    main(WIN)
