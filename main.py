import pygame
from constants import *
from utils import *
from player import Player
from fiercetooth import FierceTooth
from seashell_pearl import SeashellPearl
from pink_star import PinkStar
from objects import Obstacle, CollectibleGem, GrenadeBox, Hazard, GameFlag
from constraint_rects import ConstraintRect, compute_danger_zones
from utils import load_level, load_tile_images

pygame.init()

WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(TITLE)


class Camera:

    def __init__(self, screen_width: int, world_width: int, scroll_area: int):
        self.screen_width = screen_width
        self.world_width = world_width
        self.scroll_area = scroll_area
        self.scroll = 0

    def update(self, player_rect: pygame.Rect):
        if player_rect.centerx - self.scroll < self.scroll_area:
            self.scroll = max(0, player_rect.centerx - self.scroll_area)
        elif player_rect.centerx - self.scroll > self.screen_width - self.scroll_area:
            max_scroll = max(0, self.world_width - self.screen_width)
            self.scroll = min(max_scroll, player_rect.centerx - (self.screen_width - self.scroll_area))


class World:

    GEM_SPRITES = load_collidable_objects_sprite_sheets(16, 16, "gem")
    HAZARD_SPRITES = load_collidable_objects_sprite_sheets(48, 50, "hazard")
    FLAG_SPRITES = load_collidable_objects_sprite_sheets(48, 50, "flag")
    GRENADE_SPRITES = load_ammo_sprites('Player')
    CANNON_BALL_SPRITES = load_ammo_sprites('Fierce Tooth')
    PEARL_SPRITES = load_ammo_sprites('Seashell Pearl')

    def __init__(self, img_list):
        self.img_list = img_list
        self.obstacle_group = pygame.sprite.Group()
        self.fiercetooth_group = pygame.sprite.Group()
        self.pink_star_group = pygame.sprite.Group()
        self.seashell_group = pygame.sprite.Group()
        self.collectible_gem_group = pygame.sprite.Group()
        self.hazard_group = pygame.sprite.Group()
        self.constraint_rect_group = pygame.sprite.Group()
        self.grenade_box_group = pygame.sprite.Group()
        self.checkpoint_group = pygame.sprite.Group()

        self.player_ammo_group = pygame.sprite.Group()
        self.player_grenade_group = pygame.sprite.Group()
        self.cannon_ball_group = pygame.sprite.Group()
        self.pearl_group = pygame.sprite.Group()

    def process_data(self, data):
        """
        Process the level data to create game objects and populate the world.

        Args:
            data (list): 2D list representing the level layout.

        Returns:
            tuple: Contains the player object, various sprite groups, and sprite sheets.
            pygame sprite groups: these are sprite groups for various types of objects.
            sprite sheets: these are the loaded sprite sheets for gems, hazards, grenades, cannon balls, and pearls.
        """

        for y, row in enumerate(data):
            for x, tile in enumerate(row):
                if tile >= 0:
                    img = self.img_list[tile]
                    img_rect = img.get_rect(topleft=(x * TILE_SIZE, y * TILE_SIZE))    

                    if tile >= 0 and tile <= 14:   # obstacle tiles, the platforms
                        if tile in OBSTACLE_TILE_COLLISIONS:
                            collision_data = OBSTACLE_TILE_COLLISIONS[tile]
                            collision_rect = pygame.Rect(
                                img_rect.x + collision_data["x"],
                                img_rect.y + collision_data["y"],
                                collision_data["w"],
                                collision_data["h"]
                            )
                            obstacle = Obstacle(img, img_rect, collision_rect)
                            self.obstacle_group.add(obstacle)
                    elif tile >= 15 and tile <= 16:    # hazard tiles, saws and spikes
                        if tile == 15:
                            hazard = Hazard(x * TILE_SIZE, y * TILE_SIZE - 8, self.HAZARD_SPRITES, tile)
                        else:
                            hazard = Hazard(x * TILE_SIZE, y * TILE_SIZE - 23, self.HAZARD_SPRITES, tile)
                        self.hazard_group.add(hazard)
                    elif tile == 17 or tile == 28:     # flag tiles, level end flag and checkpoint flags
                        if tile == 17:
                            self.level_end_flag = GameFlag(x * TILE_SIZE, y * TILE_SIZE - 33, self.FLAG_SPRITES, tile)
                        elif tile == 28:
                            flag = GameFlag(x * TILE_SIZE, y * TILE_SIZE - 33, self.FLAG_SPRITES, tile)
                            self.checkpoint_group.add(flag)
                    elif tile == 18:     # player tile
                        PLAYER_SPRITES = load_player_sprite_sheets('Main Characters', '2', 32, 32, direction=True)                       
                        self.player = Player(x * TILE_SIZE, y * TILE_SIZE, 3, PLAYER_SPRITES, 100, 50, self.GEM_SPRITES, self.GRENADE_SPRITES)
                    elif tile == 19:    # FierceTooth enemy tile
                        FIERCETOOTH_SPRITES = load_enemy_sprites('Fierce Tooth', 32, 32)
                        fiercetooth_enemy = FierceTooth(x * TILE_SIZE, y * TILE_SIZE, 2, FIERCETOOTH_SPRITES, 80, True) 
                        self.fiercetooth_group.add(fiercetooth_enemy)               
                        print(f"[WORLD] Spawn FierceTooth tile at ({x},{y}) -> pos=({x * TILE_SIZE},{y * TILE_SIZE})")
                    elif tile == 20:     # PinkStar enemy tile
                        PINKSTAR_SPRITES = load_enemy_sprites('Pink Star', 32, 32)
                        pink_star_enemy = PinkStar(x * TILE_SIZE, y * TILE_SIZE, 3, PINKSTAR_SPRITES, 500)
                        self.pink_star_group.add(pink_star_enemy)
                    elif tile == 21:     # SeashellPearl enemy tile
                        SEASHELL_SPRITES = load_enemy_sprites('Seashell Pearl', 32, 32)
                        seashell_pearl_enemy = SeashellPearl(x * TILE_SIZE, y * TILE_SIZE, 0, SEASHELL_SPRITES, 120, True)  
                        self.seashell_group.add(seashell_pearl_enemy)               
                        print(f"[WORLD] Spawn Seashell tile at ({x},{y}) -> pos=({x * TILE_SIZE},{y * TILE_SIZE})")
                    elif tile >= 22 and tile <= 24:    # collectible gem tiles: player_ammo, player_health, coins
                        collectible_gem = CollectibleGem(x * TILE_SIZE, y * TILE_SIZE, self.GEM_SPRITES, tile)
                        self.collectible_gem_group.add(collectible_gem)
                    elif tile == 25 or tile == 26 or tile == 29:    # constraint rect tiles: red, blue, orange (for enemies)
                        constraint_rect = ConstraintRect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE, tile)
                        self.constraint_rect_group.add(constraint_rect)
                    elif tile == 27:     # grenade box tile
                        grenade_box_img = load_image('28', 'Level Editor Tiles')
                        grenade_box_img = pygame.transform.scale(grenade_box_img, (TILE_SIZE // 2, TILE_SIZE // 2))
                        grenade_box = GrenadeBox(x * TILE_SIZE, y * TILE_SIZE, grenade_box_img)
                        self.grenade_box_group.add(grenade_box)

        self.danger_zones = compute_danger_zones(self.constraint_rect_group)

        return self.obstacle_group, self.player, self.level_end_flag, self.player_ammo_group, self.player_grenade_group, self.fiercetooth_group, self.cannon_ball_group, self.pink_star_group, \
        self.seashell_group, self.pearl_group, self.collectible_gem_group, self.hazard_group, self.constraint_rect_group, self.danger_zones, self.grenade_box_group, self.checkpoint_group, \
        self.GEM_SPRITES, self.GRENADE_SPRITES, self.CANNON_BALL_SPRITES, self.PEARL_SPRITES

    def draw_world(self, bg1, camera: Camera, win):
        draw_bg(bg1, win, camera.scroll)
        # pygame.draw.line(win, RED, (0, 400), (WIDTH, 400))   # temporary floor

        shifted = []
        def _shift_rect(obj, attr_name, dx):
            if not hasattr(obj, attr_name):
                return
            rect = getattr(obj, attr_name)
            old_x = rect.x
            rect.x = int(rect.x - dx)
            shifted.append((obj, attr_name, old_x))

        for tile in self.obstacle_group:
            _shift_rect(tile, 'rect', camera.scroll)
            if hasattr(tile, 'collide_rect'):
                cr = tile.collide_rect
                old_cr_x = cr.x
                cr.x = int(cr.x - camera.scroll)
                shifted.append((tile, 'collide_rect', old_cr_x))

        for rect in self.constraint_rect_group:
            _shift_rect(rect, 'rect', camera.scroll)

        for flag in self.checkpoint_group:
            _shift_rect(flag, 'rect', camera.scroll)
        if self.level_end_flag is not None:
            _shift_rect(self.level_end_flag, 'rect', camera.scroll)

        for gem in self.collectible_gem_group:
            _shift_rect(gem, 'rect', camera.scroll)
        for grenade_box in self.grenade_box_group:
            _shift_rect(grenade_box, 'rect', camera.scroll)
        for hazard in self.hazard_group:
            _shift_rect(hazard, 'rect', camera.scroll)

        for enemy in self.fiercetooth_group:
            _shift_rect(enemy, 'rect', camera.scroll)
        for enemy in self.seashell_group:
            _shift_rect(enemy, 'rect', camera.scroll)
        for enemy in self.pink_star_group:
            _shift_rect(enemy, 'rect', camera.scroll)

        for pearl in self.pearl_group:
            _shift_rect(pearl, 'rect', camera.scroll)
        for cannon_ball in self.cannon_ball_group:
            _shift_rect(cannon_ball, 'rect', camera.scroll)
        for ammo in self.player_ammo_group:
            _shift_rect(ammo, 'rect', camera.scroll)
        for grenade in self.player_grenade_group:
            _shift_rect(grenade, 'rect', camera.scroll)

        _shift_rect(self.player, 'rect', camera.scroll)

        for tile in self.obstacle_group:
            tile.draw(win)

        # for testing purposes
        for rect in self.constraint_rect_group:
            rect.draw(win)

        for flag in self.checkpoint_group:
            flag.draw(win)

        if self.level_end_flag is not None:
            self.level_end_flag.draw(win)

        self.player.draw(win)
        self.player.draw_stamina_bar(win)
        self.player.draw_health_bar(win)
        self.player.draw_ammo_count(win)
        self.player.draw_grenade_count(win)

        for gem in self.collectible_gem_group:
            gem.draw(win)

        for grenade_box in self.grenade_box_group:
            grenade_box.draw(win)

        for hazard in self.hazard_group:
            hazard.draw(win)

        for enemy in self.fiercetooth_group:
            enemy.draw(win)
            enemy.draw_health_bar(win)
            # enemy.draw_vision_cone(win, self.player, self.obstacle_group, self.constraint_rect_group)   # for debugging enemy vision

        for enemy in self.seashell_group:
            enemy.draw(win)
            enemy.draw_health_bar(win)
            # enemy.draw_vision_cone(win, self.player, self.obstacle_group, self.constraint_rect_group)   # for debugging enemy vision

        for enemy in self.pink_star_group:
            enemy.draw(win)
            enemy.draw_health_bar(win)

        for pearl in self.pearl_group:
            pearl.draw(win)

        for cannon_ball in self.cannon_ball_group:
            cannon_ball.draw(win)

        for ammo in self.player_ammo_group:
            ammo.draw(win)

        for grenade in self.player_grenade_group:
            grenade.draw(win)

        pygame.display.update()

        for obj, attr, old_x in shifted:
            rect = getattr(obj, attr)
            rect.x = old_x
        # do I not need to restore the collide_rects here as well for the obstacles?


def main(win):
    """
    Main function to run the playing game loop.

    Args:
        win (Surface): Main game window surface.
    """
    clock = pygame.time.Clock()

    world_data = load_level(0)
    tile_images = load_tile_images()
    world = World(tile_images)
    obstacle_list, player, level_end_flag, player_ammo_group, player_grenade_group, fiercetooth_group, cannon_ball_group, pink_star_group, seashell_group, pearl_group, \
    collectible_gem_group, hazard_group, constraint_rect_group, danger_zones, grenade_box_group, checkpoint_group, GEM_SPRITES, GRENADE_SPRITES, CANNON_BALL_SPRITES, PEARL_SPRITES = world.process_data(world_data)

    camera = Camera(WIDTH, WORLD_WIDTH, SCROLL_AREA_WIDTH)

    bg1 = load_image('1', 'Locations', 'Backgrounds', 'Blue Nebula')

    enemies = list(fiercetooth_group) + list(seashell_group) + list(pink_star_group) 

    scroll_left = False
    scroll_right = False
    scroll = 0
    scroll_speed = 1

    level = 0

    run = True
    while run:
        clock.tick(FPS)

        keys = pygame.key.get_pressed()

        if keys[pygame.K_g] and player.alive and player.grenade_charging:
            player.grenade_charge_time += clock.get_time() / 1000.0
            if player.grenade_charge_time > player.GRENADE_MAX_CHARGE_SECONDS:
                player.grenade_charge_time = player.GRENADE_MAX_CHARGE_SECONDS

        for enemy in fiercetooth_group:  
            if enemy.alive:
                enemy.update(player, CANNON_BALL_SPRITES, cannon_ball_group, obstacle_list, constraint_rect_group)
                enemy.handle_movement(obstacle_list, constraint_rect_group, player)           
                enemy.update_sprite(player)

                if hasattr(enemy, 'smartmode') and enemy.smartmode:
                    enemy.check_and_dodge_bullets(player_ammo_group)
                    enemy.check_and_dodge_grenades(player_grenade_group)                    

                if hasattr(enemy, 'was_hit_from_behind') and enemy.was_hit_from_behind:
                    enemy.shoot(CANNON_BALL_SPRITES, cannon_ball_group)
                    enemy.was_hit_from_behind = False
            else:
                if not enemy.death_handled:
                    enemy.handle_death()

        for enemy in seashell_group:
            if enemy.alive:
                enemy.update(player, PEARL_SPRITES, pearl_group)  
                enemy.handle_movement(obstacle_list)
                enemy.update_sprite(player)

                if hasattr(enemy, 'smartmode') and enemy.smartmode:
                    enemy.react_to_grenades(player, player_grenade_group)

                if hasattr(enemy, 'was_hit_from_behind') and enemy.was_hit_from_behind:
                    enemy.fire(PEARL_SPRITES, pearl_group)
                    enemy.was_hit_from_behind = False

        # for enemy in pink_star_group:
        #     if enemy.alive:
        #         enemy.update(player)   
        #         enemy.handle_movement(obstacle_list, constraint_rect_group)
        #         enemy.update_sprite(player)
        
        if player.alive:
            player.update()
            player.handle_movement(keys, obstacle_list, hazard_group, enemies)      
            player.update_sprite()

            if player.shoot:
                player.shoot_ammo(GEM_SPRITES, player_ammo_group)

            camera.update(player.rect)

            for zone_rect, validated in danger_zones:
                if validated and zone_rect.colliderect(player.rect):
                    player.in_danger_zone = True
                else:
                    player.in_danger_zone = False

            if scroll_left and scroll > 0:
                scroll -= 5 * scroll_speed
            if scroll_right and scroll < (MAX_COLS * TILE_SIZE) - WIDTH:
                scroll += 5 * scroll_speed
        else:
            player.handle_death(HEIGHT)

        for tile in obstacle_list:
            tile.update()

        for ammo in player_ammo_group:
            ammo.update(enemies)   

        for grenade in player_grenade_group:
            grenade.update(player, enemies, obstacle_list)
            grenade.update_sprite()

        for cannon_ball in cannon_ball_group:
            cannon_ball.update(player)
            cannon_ball.update_sprite()

        for pearl in pearl_group:
            pearl.update(player)
            pearl.update_sprite()

        for grenade_box in grenade_box_group:
            grenade_box.update(player)

        for gem in collectible_gem_group:
            gem.update(player)
            gem.update_sprite()

        for hazard in hazard_group:
            hazard.update(player)
            hazard.update_sprite()

        for flag in checkpoint_group:
            flag.update(player)
            flag.update_sprite()

        level_end_flag.update(player)
        level_end_flag.update_sprite()

        world.draw_world(bg1, camera, win)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    run = False
                if event.key in (pygame.K_UP, pygame.K_w):
                    if player.alive:
                        player.jump()
                if event.key == pygame.K_SPACE:
                    if player.alive:
                        player.shoot = True
                if event.key == pygame.K_g:
                    if player.alive:
                        player.grenade_charging = True
                        player.grenade_charge_time = 0.0
                if event.key == pygame.K_z:
                    if player.alive:
                        player.draw_num_grenades_timer = player.NUM_GRENADES_DURATION
                if event.key == pygame.K_x:
                    if player.alive:
                        player.draw_num_ammo_timer = player.NUM_AMMO_DURATION
                if event.key == pygame.K_h:
                    if player.alive:
                        player.health_bar_timer = player.HEALTH_BAR_DURATION
                if event.key == pygame.K_c:
                    if player.alive:
                        player.stamina_bar_timer = player.STAMINA_BAR_DURATION

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_g:
                    if player.alive and player.grenade_charging:
                        player.launch_grenade(GRENADE_SPRITES, player_grenade_group, 
                                              charge_seconds=player.grenade_charge_time)
    
    pygame.quit()


if __name__ == "__main__":
    main(WIN)
