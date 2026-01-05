import pygame
from constants import *
from utils import *
from player import Player
from fiercetooth import FierceTooth
from seashell_pearl import SeashellPearl
from pink_star import PinkStar
from objects import Obstacle, CollectibleGem, GrenadeBox, Hazard, GameFlag
from constraint_rects import ConstraintRect, compute_danger_zones
from button import Button
from level import Level
from utils import load_level, load_tile_images
from database import init_db, load_level_progress, save_level_progress, reset_level_progress, update_totals, get_player_totals, get_level_progress

pygame.init()
pygame.mixer.init()

init_db()

WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(TITLE)

pygame.mixer.music.load('assets/Sounds/music.mp3')
pygame.mixer.music.set_volume(0.3)
# pygame.mixer.music.play(-1, 0.0, 5000)


class ScreenFade:

    def __init__(self, width: int, height: int, duration_ms: int=500):
        self.w = width
        self.h = height
        self.duration_ms = max(1, duration_ms)

    def _draw_overlay(self, win: pygame.Surface, coverage: float):
        if coverage <= 0:
            return

        rw = int(self.w * coverage)
        rh = int(self.h * coverage)
        rects = [
            pygame.Rect(0, 0, rw, rh),                          
            pygame.Rect(self.w - rw, 0, rw, rh),                
            pygame.Rect(0, self.h - rh, rw, rh),                
            pygame.Rect(self.w - rw, self.h - rh, rw, rh),     
        ]

        overlay = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        for r in rects:
            pygame.draw.rect(overlay, (0, 0, 0, 255), r)

        win.blit(overlay, (0, 0))

    def fade_out(self, win: pygame.Surface, clock: pygame.time.Clock):
        """
        Corners close in to black.
        """
        elapsed = 0
        while elapsed < self.duration_ms:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
            coverage = elapsed / self.duration_ms
            self._draw_overlay(win, coverage)
            pygame.display.update()
            dt = clock.tick(FPS)
            elapsed += dt

        self._draw_overlay(win, 1.0)
        pygame.display.update()

    def fade_in(self, win: pygame.Surface, clock: pygame.time.Clock):
        """
        Corners open from black to reveal the screen.
        """
        elapsed = 0
        while elapsed < self.duration_ms:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
            coverage = 1.0 - (elapsed / self.duration_ms)
            self._draw_overlay(win, coverage)
            pygame.display.update()
            dt = clock.tick(FPS)
            elapsed += dt


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
        self.level_length = len(data[0])

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
                        fiercetooth_enemy.obj_id = f"enemy:ft:{x}:{y}"
                        self.fiercetooth_group.add(fiercetooth_enemy)               
                        # print(f"[WORLD] Spawn FierceTooth tile at ({x},{y}) -> pos=({x * TILE_SIZE},{y * TILE_SIZE})")
                    elif tile == 20:     # PinkStar enemy tile
                        PINKSTAR_SPRITES = load_enemy_sprites('Pink Star', 32, 32)
                        pink_star_enemy = PinkStar(x * TILE_SIZE, y * TILE_SIZE, 3, PINKSTAR_SPRITES, 100)
                        pink_star_enemy.obj_id = f"enemy:ps:{x}:{y}"
                        self.pink_star_group.add(pink_star_enemy)
                    elif tile == 21:     # SeashellPearl enemy tile
                        SEASHELL_SPRITES = load_enemy_sprites('Seashell Pearl', 32, 32)
                        seashell_pearl_enemy = SeashellPearl(x * TILE_SIZE, y * TILE_SIZE, 0, SEASHELL_SPRITES, 120, True) 
                        seashell_pearl_enemy.obj_id = f"enemy:ss:{x}:{y}" 
                        self.seashell_group.add(seashell_pearl_enemy)               
                        # print(f"[WORLD] Spawn Seashell tile at ({x},{y}) -> pos=({x * TILE_SIZE},{y * TILE_SIZE})")
                    elif tile >= 22 and tile <= 24:    # collectible gem tiles: player_ammo, player_health, coins
                        collectible_gem = CollectibleGem(x * TILE_SIZE, y * TILE_SIZE, self.GEM_SPRITES, tile)
                        collectible_gem.obj_id = f"gem:{x}:{y}:{tile}"
                        self.collectible_gem_group.add(collectible_gem)
                    elif tile == 25 or tile == 26 or tile == 29:    # constraint rect tiles: red, blue, orange (for enemies)
                        constraint_rect = ConstraintRect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE, tile)
                        self.constraint_rect_group.add(constraint_rect)
                    elif tile == 27:     # grenade box tile
                        grenade_box_img = load_image('28', 'Level Editor Tiles')
                        grenade_box_img = pygame.transform.scale(grenade_box_img, (TILE_SIZE // 2, TILE_SIZE // 2))
                        grenade_box = GrenadeBox(x * TILE_SIZE, y * TILE_SIZE, grenade_box_img)
                        grenade_box.obj_id = f"gbox:{x}:{y}"
                        self.grenade_box_group.add(grenade_box)

        self.danger_zones = compute_danger_zones(self.constraint_rect_group)

        return self.level_length, self.obstacle_group, self.player, self.level_end_flag, self.player_ammo_group, self.player_grenade_group, self.fiercetooth_group, self.cannon_ball_group, self.pink_star_group, \
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
        # for rect in self.constraint_rect_group:
        #     rect.draw(win)

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

        for obj, attr, old_x in shifted:
            rect = getattr(obj, attr)
            rect.x = old_x


def draw_main_menu(win):
    """
    Draw the main menu screen.
    Args:
        win (Surface): Main game window surface.
    """
    win.fill(ORANGE)
    draw_text("Main Menu", 'Comicsans', 50, WHITE, win, 1, 7, center_x=True)

    text = "Press I for the instructions and tips page"                         
    draw_text(text, 'Comicsans', 30, WHITE, win, 1, HEIGHT // 2 - 130, center_x=True)
    text2 = "Press T to view your stats, for each level and your total stats"
    draw_text(text2, 'Comicsans', 25, WHITE, win, 1, HEIGHT // 2 - 80, center_x=True)

    start_text = "Press Start below to start playing!"
    draw_text(start_text, 'Comicsans', 30, WHITE, win, 1, HEIGHT // 2, center_x=True)


def draw_instructions_page(win):
    """
    Draw the instructions and tips page.
    Args:
        win (Surface): Main game window surface.
    """
    win.fill(PINK)

    draw_text("Instructions and Tips", 'Comicsans', 50, WHITE, win, 1, 7, center_x=True)
    instructions = [
        "Use the arrow keys or WASD to move your character.",
        "Press SPACE to shoot ammo at enemies.",
        "Press G to charge and launch grenades - the longer you hold, the further it will go.",
        "Collect gems to increase your ammo and health.",
        "Avoid hazards like spikes and saws.",
        "Use checkpoints to save your progress within a level.",
        "In smart mode, enemies have enhanced AI logic. Beware of them,",
        "as they are smarter than you think! Especially Fiercetooth.",
        "Collect ammo gems, health gems and grenade boxes to help you.",
        "Also try and collect coins for extra points! Later on you can use them in the shop.",
        "When you enter a danger zone (guarded by a Pink Star enemy),",
        "be extra cautious; it always knows where you are and will chase relentlessly!",
        "Reach the end flag and make sure to press enter to complete the level.",
        "Good luck and have fun!"
    ]
    for i, line in enumerate(instructions):
        draw_text(line, 'Comicsans', 20, WHITE, win, 30, 90 + i * 40)


def build_level_buttons():
    buttons = []
    cols = 8
    spacing_x = 100
    spacing_y = 75
    start_x = 10
    start_y = 50

    for i in range(TOTAL_LEVELS):
        level_id_x = i + 1
        img_name = f"2_{level_id_x:02d}"
        img = load_image(img_name, 'GUI', 'Level Numbers', '2')
        col = i % cols
        row = i // cols
        btn = Button(start_x + col * spacing_x, start_y + row * spacing_y, img, 3)
        buttons.append(btn)

    return buttons


def draw_levels_page(win, bg1):
    """
    Draw the levels selection page.
    Args:
        win (Surface): Main game window surface.
    """
    bg1 = pygame.transform.scale(bg1, (WIDTH, HEIGHT))
    win.blit(bg1, (0, 0))

    draw_text("Levels", 'Comicsans', 30, CYAN, win, 1, 7, center_x=True)


def draw_stats_page(win):
    """
    Render total stats and latest per-level progress.
    """

    win.fill((20, 30, 40))

    totals = get_player_totals()
    level_rows = get_level_progress()

    y = 30
    draw_text("Stats", 'Comicsans', 42, WHITE, win, 1, y, center_x=True)
    y += 50

    draw_text("Total lifetime Stats", 'Comicsans', 30, CYAN, win, 20, y)
    y += 32
    draw_text(f"Coins: {totals['total_coins']}", 'Comicsans', 24, WHITE, win, 40, y); y += 26
    draw_text(f"Enemies defeated: {totals['total_enemies']}", 'Comicsans', 24, WHITE, win, 40, y); y += 26
    draw_text(f"Deaths: {totals['total_deaths']}", 'Comicsans', 24, WHITE, win, 40, y); y += 26
    draw_text(f"Time played (s): {int(totals['total_time'])}", 'Comicsans', 24, WHITE, win, 40, y); y += 40

    draw_text("Per-level (latest saved)", 'Comicsans', 30, CYAN, win, 20, y)
    y += 32
    if not level_rows:
        draw_text("No in-progress levels.", 'Comicsans', 22, WHITE, win, 40, y)
    else:
        for row in level_rows:
            if y > HEIGHT - 30:
                break  
            draw_text(f"Level {row['level_id']}", 'Comicsans', 26, WHITE, win, 40, y); y += 24
            draw_text(f"  Coins: {row['coin_count']}", 'Comicsans', 22, LIGHT_GRAY, win, 60, y); y += 22
            draw_text(f"  Enemies defeated: {len(row['killed_enemy_ids'])}", 'Comicsans', 22, LIGHT_GRAY, win, 60, y); y += 22
            draw_text(f"  Time (s): {int(row['time_taken'])}", 'Comicsans', 22, LIGHT_GRAY, win, 60, y); y += 22


def start_level(level_num):
    world_data = load_level(level_num)
    tile_images = load_tile_images()
    world = World(tile_images)
    (level_length, obstacle_list, player, level_end_flag, player_ammo_group, player_grenade_group,
    fiercetooth_group, cannon_ball_group, pink_star_group, seashell_group, pearl_group,
    collectible_gem_group, hazard_group, constraint_rect_group, danger_zones, grenade_box_group,
    checkpoint_group, GEM_SPRITES, GRENADE_SPRITES, CANNON_BALL_SPRITES, PEARL_SPRITES) = world.process_data(world_data)

    level_world_width = level_length * TILE_SIZE
    player.world_width = level_world_width
    camera = Camera(WIDTH, level_world_width, SCROLL_AREA_WIDTH)
    enemies = list(fiercetooth_group) + list(seashell_group) + list(pink_star_group)
    level_info = Level(player, world_data)
    return (world, level_info, obstacle_list, player, level_end_flag, player_ammo_group, player_grenade_group,
            fiercetooth_group, cannon_ball_group, pink_star_group, seashell_group, pearl_group,
            collectible_gem_group, hazard_group, constraint_rect_group, danger_zones, grenade_box_group,
            checkpoint_group, GEM_SPRITES, GRENADE_SPRITES, CANNON_BALL_SPRITES, PEARL_SPRITES,
            camera, enemies)


def apply_saved_progress(selected_level, world, level_info, obstacle_list, player, level_end_flag,
                         player_ammo_group, player_grenade_group, fiercetooth_group, cannon_ball_group,
                         pink_star_group, seashell_group, pearl_group, collectible_gem_group, hazard_group,
                         constraint_rect_group, danger_zones, grenade_box_group, checkpoint_group,
                         GEM_SPRITES, GRENADE_SPRITES, CANNON_BALL_SPRITES, PEARL_SPRITES, camera, enemies):
    progress = load_level_progress(selected_level)

    player.coin_count = progress["coin_count"]
    if progress["ammo"] is not None:
        player.ammo = progress["ammo"]
    if progress["grenades"] is not None:
        player.grenades = progress["grenades"]
    if progress["health"] is not None:
        player.health = progress["health"]
        player.max_health = max(player.max_health, player.health)

    if progress["last_checkpoint"]:
        player.last_checkpoint = progress["last_checkpoint"]
        player.position.x, player.position.y = progress["last_checkpoint"]
        player.rect.topleft = (int(player.position.x), int(player.position.y))
        player.mask = pygame.mask.from_surface(player.img)

    player.collected_ids = set(progress["collected_ids"])
    level_info.collected_ids = set(progress["collected_ids"])
    level_info.killed_enemy_ids = set(progress["killed_enemy_ids"])

    for gem in list(collectible_gem_group):
        if getattr(gem, "obj_id", None) in level_info.collected_ids:
            gem.kill()
    for gbox in list(grenade_box_group):
        if getattr(gbox, "obj_id", None) in level_info.collected_ids:
            gbox.kill()

    for enemy in list(fiercetooth_group) + list(seashell_group) + list(pink_star_group):
        if getattr(enemy, "obj_id", None) in level_info.killed_enemy_ids:
            enemy.kill()

    if progress.get("reached_end"):
        player.reached_level_end = True

    return (world, level_info, obstacle_list, player, level_end_flag, player_ammo_group, player_grenade_group,
            fiercetooth_group, cannon_ball_group, pink_star_group, seashell_group, pearl_group,
            collectible_gem_group, hazard_group, constraint_rect_group, danger_zones, grenade_box_group,
            checkpoint_group, GEM_SPRITES, GRENADE_SPRITES, CANNON_BALL_SPRITES, PEARL_SPRITES,
            camera, enemies)


def draw_death_screen(win):
    """
    Draw the death screen when the player dies.
    Args:
        win (Surface): Main game window surface.
    """
    win.fill(RED)
    draw_text("You Died!", 'Comicsans', 50, WHITE, win, 1, 10, center_x=True)
    text = "Click Restart to remove all level data and try again from the start of the level"
    draw_text(text, 'Comicsans', 20, WHITE, win, 1, HEIGHT // 3 - 60, center_x=True)
    text2 = "Click start to go to last checkpoint reached, or Exit to go to main menu"
    draw_text(text2, 'Comicsans', 20, WHITE, win, 1, HEIGHT // 2 + 10, center_x=True)


def draw_next_level_screen(win):
    """
    Draw the next level screen when the player completes a level.
    Args:
        win (Surface): Main game window surface.
    """
    win.fill(GREEN)
    draw_text("Level Complete!", 'Comicsans', 50, WHITE, win, 1, 10, center_x=True)
    text = "Click Restart to remove all level data and try again from the start of the level"
    draw_text(text, 'Comicsans', 20, WHITE, win, 1, HEIGHT // 3 - 60, center_x=True)
    text2 = "Press Start to proceed to the next level, or Exit to go back to the main menu"
    draw_text(text2, 'Comicsans', 20, WHITE, win, 1, HEIGHT // 2 + 10, center_x=True)


def main(win):
    """
    Main function to run the playing game loop.

    Args:
        win (Surface): Main game window surface.
    """
    clock = pygame.time.Clock()

    selected_level = 1

    bg1 = load_image('1', 'Locations', 'Backgrounds', 'Blue Nebula')

    start_img = load_image('start_btn', 'GUI', 'Buttons')
    restart_img = load_image('restart_btn', 'GUI', 'Buttons')
    exit_img = load_image('exit_btn', 'GUI', 'Buttons')
    back_img = load_image('Icon_14', 'GUI', 'Icons')

    main_start_btn = Button(WIDTH // 2 - 140, HEIGHT - 230, start_img, 1)
    level_start_btn = Button(WIDTH // 2 - 300, HEIGHT - 200, start_img, 1)
    back_btn = Button(10, 10, back_img, 2.5)
    restart_btn = Button(WIDTH // 2 - 170, HEIGHT // 3 - 10, restart_img, 3)
    exit_btn = Button(WIDTH // 2 + 75, HEIGHT - 200, exit_img, 1)

    level_btns = build_level_buttons()

    (world, level_info, obstacle_list, player, level_end_flag, player_ammo_group, player_grenade_group,
    fiercetooth_group, cannon_ball_group, pink_star_group, seashell_group, pearl_group,
    collectible_gem_group, hazard_group, constraint_rect_group, danger_zones, grenade_box_group,
    checkpoint_group, GEM_SPRITES, GRENADE_SPRITES, CANNON_BALL_SPRITES, PEARL_SPRITES,
    camera, enemies) = start_level(selected_level)

    fader = ScreenFade(WIDTH, HEIGHT, duration_ms=1250)

    scroll_left = False
    scroll_right = False
    scroll = 0
    scroll_speed = 1

    main_menu = True
    instructions_page = False
    levels_page = False
    stats_page = False
    playing_level = False
    death_screen = False
    next_level_screen = False

    run = True
    while run:
        clock.tick(FPS)

        if main_menu:
            draw_main_menu(win)
            if main_start_btn.draw(win):
                fader.fade_out(win, clock)
                main_menu = False
                levels_page = True
                draw_levels_page(win, bg1)
                fader.fade_in(win, clock)

        elif instructions_page:
            draw_instructions_page(win)

            if back_btn.draw(win):
                fader.fade_out(win, clock)
                instructions_page = False
                main_menu = True
                draw_main_menu(win)
                fader.fade_in(win, clock)

        elif levels_page:
            draw_levels_page(win, bg1)

            if back_btn.draw(win):
                fader.fade_out(win, clock)
                levels_page = False
                main_menu = True
                draw_main_menu(win)
                fader.fade_in(win, clock)

            for idx, btn in enumerate(level_btns, start=1):
                if btn.draw(win) and idx <= CURRENT_MAX_LEVELS:
                    fader.fade_out(win, clock)
                    selected_level = idx

                    progress = load_level_progress(selected_level)
                    if progress.get("reached_end"):
                        reset_level_progress(selected_level)

                    (world, level_info, obstacle_list, player, level_end_flag, player_ammo_group, player_grenade_group,
                    fiercetooth_group, cannon_ball_group, pink_star_group, seashell_group, pearl_group,
                    collectible_gem_group, hazard_group, constraint_rect_group, danger_zones, grenade_box_group,
                    checkpoint_group, GEM_SPRITES, GRENADE_SPRITES, CANNON_BALL_SPRITES, PEARL_SPRITES,
                    camera, enemies) = start_level(selected_level)

                    (world, level_info, obstacle_list, player, level_end_flag, player_ammo_group, player_grenade_group,
                    fiercetooth_group, cannon_ball_group, pink_star_group, seashell_group, pearl_group,
                    collectible_gem_group, hazard_group, constraint_rect_group, danger_zones, grenade_box_group,
                    checkpoint_group, GEM_SPRITES, GRENADE_SPRITES, CANNON_BALL_SPRITES, PEARL_SPRITES,
                    camera, enemies) = apply_saved_progress(
                        selected_level, world, level_info, obstacle_list, player, level_end_flag,
                        player_ammo_group, player_grenade_group, fiercetooth_group, cannon_ball_group,
                        pink_star_group, seashell_group, pearl_group, collectible_gem_group, hazard_group,
                        constraint_rect_group, danger_zones, grenade_box_group, checkpoint_group,
                        GEM_SPRITES, GRENADE_SPRITES, CANNON_BALL_SPRITES, PEARL_SPRITES, camera, enemies)

                    playing_level = True
                    levels_page = False
                    world.draw_world(bg1, camera, win)
                    fader.fade_in(win, clock)
            
        elif stats_page:
            draw_stats_page(win)

            if back_btn.draw(win):
                fader.fade_out(win, clock)
                stats_page = False
                main_menu = True
                draw_main_menu(win)
                fader.fade_in(win, clock)
        
        elif playing_level:
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
                        enemy.handle_death(obstacle_list)
                        if hasattr(enemy, "obj_id") and hasattr(level_info, "killed_enemy_ids"): 
                            level_info.killed_enemy_ids.add(enemy.obj_id)

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
                else:   # doesn't need a handle death method since it never moves from its spot anyway
                    if hasattr(enemy, "obj_id") and hasattr(level_info, "killed_enemy_ids"):
                        level_info.killed_enemy_ids.add(enemy.obj_id)

            for enemy in pink_star_group:
                if enemy.alive:
                    enemy.update(player, constraint_rect_group)   
                    enemy.handle_movement(obstacle_list, constraint_rect_group, player)
                    enemy.update_sprite(player)
                else:
                    if not enemy.death_handled:
                        enemy.handle_death(obstacle_list)
                    if hasattr(enemy, "obj_id") and hasattr(level_info, "killed_enemy_ids"):     
                        level_info.killed_enemy_ids.add(enemy.obj_id)
        
            if player.alive:
                player.update()
                player.handle_movement(keys, obstacle_list, hazard_group, enemies)      
                player.update_sprite()

                if player.shoot:
                    player.shoot_ammo(GEM_SPRITES, player_ammo_group)

                camera.update(player.rect)

                for zone_rect, validated in danger_zones:
                    if validated and zone_rect.colliderect(player.rect):
                        if player.rect.left > zone_rect.left and player.rect.right < zone_rect.right and \
                            player.rect.bottom < zone_rect.bottom and player.rect.top > zone_rect.top:

                            player.in_danger_zone = True
                            break
                    else:
                        player.in_danger_zone = False

                if player.collide(level_end_flag):
                    if keys[pygame.K_RETURN]:
                        player.reached_level_end = True
                        update_totals(
                            delta_coins=player.coin_count,
                            delta_enemies=len(getattr(level_info, "killed_enemy_ids", [])),
                            delta_time=level_info.time_taken
                        )
                        reset_level_progress(selected_level)
                        fader.fade_out(win, clock)
                        playing_level = False
                        next_level_screen = True
                        draw_next_level_screen(win)
                        fader.fade_in(win, clock)

                if scroll_left and scroll > 0:
                    scroll -= 5 * scroll_speed
                if scroll_right and scroll < (MAX_COLS * TILE_SIZE) - WIDTH:
                    scroll += 5 * scroll_speed
            else:
                if player.death_timer < player.death_duration:
                    player.death_timer += 1
                    player.handle_death(HEIGHT)
                else:
                    player.death_timer = 0
                    update_totals(delta_deaths=1)
                    fader.fade_out(win, clock)
                    death_screen = True
                    playing_level = False
                    draw_death_screen(win)
                    fader.fade_in(win, clock)

            for tile in obstacle_list:
                tile.update()

            for ammo in player_ammo_group:
                ammo.update(enemies, obstacle_list)   

            for grenade in player_grenade_group:
                grenade.update(player, enemies, obstacle_list)
                grenade.update_sprite()

            for cannon_ball in cannon_ball_group:
                cannon_ball.update(player, obstacle_list)
                cannon_ball.update_sprite()

            for pearl in pearl_group:
                pearl.update(player, obstacle_list)
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

            level_info.update_time()
            save_level_progress(selected_level, {
                "last_checkpoint": player.last_checkpoint,
                "coin_count": player.coin_count,
                "ammo": player.ammo,
                "grenades": player.grenades,
                "health": player.health,
                "time_taken": level_info.time_taken,
                "collected_ids": getattr(player, "collected_ids", set()),
                "killed_enemy_ids": getattr(level_info, "killed_enemy_ids", set()),
                "reached_end": player.reached_level_end,
            })
            
        elif death_screen:
            draw_death_screen(win)

            if restart_btn.draw(win):
                fader.fade_out(win, clock)
                reset_level_progress(selected_level)

                (world, level_info, obstacle_list, player, level_end_flag, player_ammo_group, player_grenade_group,
                fiercetooth_group, cannon_ball_group, pink_star_group, seashell_group, pearl_group,
                collectible_gem_group, hazard_group, constraint_rect_group, danger_zones, grenade_box_group,
                checkpoint_group, GEM_SPRITES, GRENADE_SPRITES, CANNON_BALL_SPRITES, PEARL_SPRITES,
                camera, enemies) = start_level(selected_level)

                next_level_screen = False
                playing_level = True
                world.draw_world(bg1, camera, win)
                fader.fade_in(win, clock)

            if exit_btn.draw(win):
                fader.fade_out(win, clock)
                death_screen = False
                main_menu = True
                draw_main_menu(win)
                fader.fade_in(win, clock)

            if level_start_btn.draw(win):
                fader.fade_out(win, clock)

                (world, level_info, obstacle_list, player, level_end_flag, player_ammo_group, player_grenade_group,
                fiercetooth_group, cannon_ball_group, pink_star_group, seashell_group, pearl_group,
                collectible_gem_group, hazard_group, constraint_rect_group, danger_zones, grenade_box_group,
                checkpoint_group, GEM_SPRITES, GRENADE_SPRITES, CANNON_BALL_SPRITES, PEARL_SPRITES,
                camera, enemies) = start_level(selected_level)

                (world, level_info, obstacle_list, player, level_end_flag, player_ammo_group, player_grenade_group,
                fiercetooth_group, cannon_ball_group, pink_star_group, seashell_group, pearl_group,
                collectible_gem_group, hazard_group, constraint_rect_group, danger_zones, grenade_box_group,
                checkpoint_group, GEM_SPRITES, GRENADE_SPRITES, CANNON_BALL_SPRITES, PEARL_SPRITES,
                camera, enemies) = apply_saved_progress(
                    selected_level, world, level_info, obstacle_list, player, level_end_flag,
                    player_ammo_group, player_grenade_group, fiercetooth_group, cannon_ball_group,
                    pink_star_group, seashell_group, pearl_group, collectible_gem_group, hazard_group,
                    constraint_rect_group, danger_zones, grenade_box_group, checkpoint_group,
                    GEM_SPRITES, GRENADE_SPRITES, CANNON_BALL_SPRITES, PEARL_SPRITES, camera, enemies)

                if player.health <= 0:
                    player.health = max(1, player.max_health // 2)
                player.alive = True
                player.death_timer = 0
                if hasattr(player, "death_anim_started"):
                    player.death_anim_started = False

                death_screen = False
                playing_level = True
                world.draw_world(bg1, camera, win)
                fader.fade_in(win, clock)

        elif next_level_screen:
            draw_next_level_screen(win)

            if restart_btn.draw(win):
                fader.fade_out(win, clock)
                reset_level_progress(selected_level)

                (world, level_info, obstacle_list, player, level_end_flag, player_ammo_group, player_grenade_group,
                fiercetooth_group, cannon_ball_group, pink_star_group, seashell_group, pearl_group,
                collectible_gem_group, hazard_group, constraint_rect_group, danger_zones, grenade_box_group,
                checkpoint_group, GEM_SPRITES, GRENADE_SPRITES, CANNON_BALL_SPRITES, PEARL_SPRITES,
                camera, enemies) = start_level(selected_level)

                next_level_screen = False
                playing_level = True
                world.draw_world(bg1, camera, win)
                fader.fade_in(win, clock)

            if exit_btn.draw(win):
                fader.fade_out(win, clock)
                next_level_screen = False
                main_menu = True
                draw_main_menu(win)
                fader.fade_in(win, clock)

            if selected_level < CURRENT_MAX_LEVELS:
                if level_start_btn.draw(win):
                    fader.fade_out(win, clock)
                    player.current_level += 1
                    selected_level += 1

                    (world, level_info, obstacle_list, player, level_end_flag, player_ammo_group, player_grenade_group,
                    fiercetooth_group, cannon_ball_group, pink_star_group, seashell_group, pearl_group,
                    collectible_gem_group, hazard_group, constraint_rect_group, danger_zones, grenade_box_group,
                    checkpoint_group, GEM_SPRITES, GRENADE_SPRITES, CANNON_BALL_SPRITES, PEARL_SPRITES,
                    camera, enemies) = start_level(selected_level)

                    (world, level_info, obstacle_list, player, level_end_flag, player_ammo_group, player_grenade_group,
                    fiercetooth_group, cannon_ball_group, pink_star_group, seashell_group, pearl_group,
                    collectible_gem_group, hazard_group, constraint_rect_group, danger_zones, grenade_box_group,
                    checkpoint_group, GEM_SPRITES, GRENADE_SPRITES, CANNON_BALL_SPRITES, PEARL_SPRITES,
                    camera, enemies) = apply_saved_progress(
                        selected_level, world, level_info, obstacle_list, player, level_end_flag,
                        player_ammo_group, player_grenade_group, fiercetooth_group, cannon_ball_group,
                        pink_star_group, seashell_group, pearl_group, collectible_gem_group, hazard_group,
                        constraint_rect_group, danger_zones, grenade_box_group, checkpoint_group,
                        GEM_SPRITES, GRENADE_SPRITES, CANNON_BALL_SPRITES, PEARL_SPRITES, camera, enemies)

                    next_level_screen = False
                    playing_level = True
                    world.draw_world(bg1, camera, win)
                    fader.fade_in(win, clock)

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    run = False
                if event.key in (pygame.K_UP, pygame.K_w):
                    if playing_level and player.alive:
                        player.jump()
                if event.key == pygame.K_i:
                    if main_menu or stats_page:
                        fader.fade_out(win, clock)
                        main_menu = False
                        stats_page = False
                        instructions_page = True
                        draw_instructions_page(win)
                        fader.fade_in(win, clock)
                if event.key == pygame.K_t:
                    if main_menu or instructions_page:
                        fader.fade_out(win, clock)
                        main_menu = False
                        instructions_page = False
                        stats_page = True
                        draw_stats_page(win)
                        fader.fade_in(win, clock)
                if event.key == pygame.K_SPACE:
                    if playing_level and player.alive:
                        player.shoot = True
                if event.key == pygame.K_g:
                    if playing_level and player.alive:
                        player.grenade_charging = True
                        player.grenade_charge_time = 0.0
                if event.key == pygame.K_z:
                    if playing_level and player.alive:
                        player.draw_num_grenades_timer = player.NUM_GRENADES_DURATION
                if event.key == pygame.K_x:
                    if playing_level and player.alive:
                        player.draw_num_ammo_timer = player.NUM_AMMO_DURATION
                if event.key == pygame.K_h:
                    if playing_level and player.alive:
                        player.health_bar_timer = player.HEALTH_BAR_DURATION
                if event.key == pygame.K_c:
                    if playing_level and player.alive:
                        player.stamina_bar_timer = player.STAMINA_BAR_DURATION

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_g:
                    if player.alive and player.grenade_charging and playing_level:
                        player.launch_grenade(GRENADE_SPRITES, player_grenade_group, 
                                              charge_seconds=player.grenade_charge_time)
    
    save_level_progress(selected_level, {
        "last_checkpoint": player.last_checkpoint,
        "coin_count": player.coin_count,
        "ammo": player.ammo,
        "grenades": player.grenades,
        "health": player.health,
        "time_taken": level_info.time_taken,
        "collected_ids": getattr(player, "collected_ids", set()),
        "killed_enemy_ids": getattr(level_info, "killed_enemy_ids", set()),
        "reached_end": player.reached_level_end,
    })
    pygame.quit()


if __name__ == "__main__":
    main(WIN)
