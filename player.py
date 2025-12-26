import pygame
from constants import *
from objects import PurpleGem, Grenade
from utils import draw_text


class Player(pygame.sprite.Sprite):
    """
    Player class represents the player character in the game.
    It handles player movement, animation, shooting, and health.

    Attributes:
        ANIMATION_DELAY (int): Delay in frames between sprite animations.
        HEALTH_BAR_DURATION (int): Duration for which the health bar is displayed after taking damage.
        GRAVITY (float): Gravity strength affecting the player.
        HIT_ANIM_DURATION (int): Duration for player hit animation in frames.

        sprites (dict): Dictionary containing different sprites for the player animations.
        direction (str): Current facing direction of the player ('right' or 'left').
        img (Surface): Current image/sprite of the player.
        animation_count (int): Counter for animation frames.
        position (Vector2): Current position of the player in the game world.
        velocity (Vector2): Current velocity of the player.
        speed (float): Movement speed of the player.
        y_vel (float): Vertical velocity of the player.
        moving_left (bool): Flag indicating if the player is moving left.
        moving_right (bool): Flag indicating if the player is moving right.
        ammo (int): Current ammo count for the player.
        start_ammo (int): Initial ammo count for the player.
        rect (Rect): Pygame Rect object representing the player's position and size.
        mask (Mask): Pygame Mask object for collision detection with enemies.
        alive (bool): Flag indicating if the player is alive.
        jump_count (int): Counter for jump instances (single or double jump).
        shoot (bool): Flag indicating if the player is attempting to shoot.
        shoot_cooldown (int): Counter for the shoot cooldown period.
        health (int): Current health of the player.
        max_health (int): Maximum health of the player.
        health_bar_timer (int): Timer for managing health bar display duration.
        hit_anim_timer (int): Timer for managing player hit animation duration. 
        is_player (bool): Proves that this object is a Player.
    """

    ANIMATION_DELAY = 3
    HEALTH_BAR_DURATION = STAMINA_BAR_DURATION = NUM_AMMO_DURATION = NUM_GRENADES_DURATION = 180
    GRAVITY = 0.7  
    HIT_ANIM_DURATION = 120
    SPRINT_SPEED = 5
    SPRINT_DEPLETION = 0.6
    SPRINT_RECOVERY = 0.3
    SPRINT_THRESHOLD = 10

    def __init__(self, x, y, x_vel, SPRITES, ammo, grenades, GEM_SPRITES, GRENADE_SPRITES):
        """
        Initialises the Player object with the given position, velocity, sprites, and ammo.

        Args:
            x (float): Initial x-coordinate of the player.
            y (float): Initial y-coordinate of the player.
            x_vel (float): Initial horizontal velocity of the player.
            SPRITES (dict): Dictionary containing different sprites for the player animations.
            ammo (int): Initial ammo count for the player.
        """
        super().__init__()
        self.sprites = SPRITES
        self.gem_sprites = GEM_SPRITES
        self.grenade_sprites = GRENADE_SPRITES
        self.direction = "right"
        self.img = self.sprites['Idle_' + self.direction][0]   
        self.animation_count = 0
        self.position = pygame.math.Vector2(x, y)
        self.velocity = pygame.math.Vector2(0, 0)
        self.base_speed = x_vel
        self.speed = x_vel
        self.y_vel = 0
        self.moving_left = False
        self.moving_right = False
        self.ammo = ammo 
        self.grenades = grenades
        self.rect = self.img.get_rect(topleft=(int(self.position.x), int(self.position.y)))
        self.mask = pygame.mask.from_surface(self.img)
        self.alive = True
        self.jump_count = 0
        self.shoot = False
        self.throw_grenade = False
        self.shoot_cooldown = 0
        self.grenade_cooldown = 0
        self.sprint_allowed = True
        self.stamina = 100
        self.max_stamina = self.stamina
        self.stamina_bar_timer = 0
        self.is_sprinting = False
        self.health = 400
        self.max_health = self.health
        self.health_bar_timer = 0
        self.hit_anim_timer = 0
        self.draw_num_ammo_timer = 0
        self.draw_num_grenades_timer = 0
        self.is_player = True

    def handle_movement(self, keys, enemies_group=None):
        """
        Handles the player movement based on keyboard input and collision with enemies.

        Args:
            keys (Iterable): Collection of boolean values representing the state of keyboard keys.
            enemies_group (Group, optional): Pygame Group containing enemy objects for collision detection.
        """
        shift_pressed = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]

        self.velocity.x = 0
        self.moving_left = False
        self.moving_right = False

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            if shift_pressed and self.stamina > 0 and self.sprint_allowed:
                self.speed = self.SPRINT_SPEED
                self.is_sprinting = True
                self.stamina_bar_timer = self.STAMINA_BAR_DURATION
            else:
                self.speed = self.base_speed
                self.is_sprinting = False

            self.velocity.x = -self.speed
            self.moving_left = True
            self.direction = "left"

        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            if shift_pressed and self.stamina > 0 and self.sprint_allowed:
                self.speed = self.SPRINT_SPEED
                self.is_sprinting = True
                self.stamina_bar_timer = self.STAMINA_BAR_DURATION
            else:
                self.speed = self.base_speed
                self.is_sprinting = False

            self.velocity.x = self.speed
            self.moving_right = True
            self.direction = "right"

        else:
            self.speed = self.base_speed
            self.is_sprinting = False

        self.y_vel += self.GRAVITY
        if self.y_vel > 10:
            self.y_vel = 10

        dy = self.y_vel
        if self.rect.bottom + dy > 400:
            dy = 400 - self.rect.bottom
            self.jump_count = 0
            self.y_vel = 0

        self.position.y += dy
        self.rect.topleft = (int(self.position.x), int(self.position.y))
        self.mask = pygame.mask.from_surface(self.img)

        if enemies_group:
            for enemy in enemies_group:
                if enemy.alive and self.collide(enemy):   
                    dx = abs(self.rect.centerx - enemy.rect.centerx)

                    if self.y_vel > 2 and dx <= (enemy.rect.width // 2 + 7):   
                        self.y_vel = -11
                        self.jump_count = 1
                        
                        in_recovery = False
                        if hasattr(enemy, "post_bite_recovery"):
                            in_recovery = enemy.post_bite_recovery
                        elif hasattr(enemy, "post_attack_recovery"):
                            in_recovery = enemy.post_attack_recovery

                        if hasattr(enemy, "get_hit") and not in_recovery:
                            enemy.get_hit(20, attacker=self)
                    else:
                        if self.y_vel < 0:
                            self.rect.top = enemy.rect.bottom                    

                        self.position.y = self.rect.y
                        self.y_vel = 0

        self.position.x += self.velocity.x
        self.rect.topleft = (int(self.position.x), int(self.position.y))
        self.mask = pygame.mask.from_surface(self.img)

        if enemies_group:
            for enemy in enemies_group:
                if enemy.alive:                     # don't collide with a dead enemy!
                    if self.collide(enemy):                
                        dx = abs(self.rect.centerx - enemy.rect.centerx)
                        
                        if self.y_vel > 2 and dx <= (enemy.rect.width // 2 + 7):   
                            continue
                        else:
                            if self.rect.centerx < enemy.rect.centerx:
                                self.rect.right = enemy.rect.left
                            else:
                                self.rect.left = enemy.rect.right

                            self.position.x = self.rect.x

    def handle_death(self, screen_height):
        """
        Run the death animation once: small upward impulse, spin onto back,
        then fall off the bottom of the screen. It is safe to call every frame after death.
        """
        if self.alive:
            return  
        
        if not getattr(self, 'death_anim_started', False):
            self.death_anim_started = True
            self.y_vel = -13  
            self.jump_count = 2
            self.death_rotation = 0
            self.death_spin_speed = -8 if self.direction == "right" else 8
            self.death_og_img = self.img.copy()
            self.death_fall_speed_cap = 12
            self.death_finished = False
            self.velocity.x = 0
            self.speed = 0

        self.y_vel += self.GRAVITY
        if self.y_vel > self.death_fall_speed_cap:
            self.y_vel = self.death_fall_speed_cap

        self.position.y += self.y_vel
        self.rect.topleft = (int(self.position.x), int(self.position.y))

        self.death_rotation = (self.death_rotation + self.death_spin_speed) % 360
        rotated = pygame.transform.rotate(self.death_og_img, self.death_rotation)
        old_center = self.rect.center
        self.img = rotated
        self.rect = self.img.get_rect(center=old_center)

        if self.rect.top > screen_height:
            self.death_finished = True

    def jump(self):
        """
        Makes the player jump by applying a vertical velocity.
        Supports single and double jumps.
        """
        if self.jump_count < 2:
            if self.jump_count == 0:
                self.y_vel = -13
            else:
                self.y_vel = -8

            self.jump_count += 1

    def draw(self, win):
        """
        Draws the player on the given surface.

        Args:
            win (Surface): The surface on which to draw the player.
        """
        win.blit(self.img, self.rect)

    def get_hit(self, damage=10, attacker=None):
        """
        Reduces the player's health by the given damage amount.
        Initiates the health bar display timer and the hit timer.

        Args:
            damage (int, optional): The amount of damage to apply to the player. Defaults to 10.
        """
        self.health -= damage
        self.health_bar_timer = self.HEALTH_BAR_DURATION

        if attacker and ((hasattr(attacker, 'is_enemy') and attacker.is_enemy) or \
            (hasattr(attacker, 'is_grenade') and attacker.is_grenade)):
            self.hit_anim_timer = self.HIT_ANIM_DURATION

    def check_alive(self):
        """
        Checks if the player is alive based on health.
        If the player's health drops to 0 or below, they die.
        """
        if self.health <= 0:
            self.health = 0
            self.speed = 0
            self.alive = False

    def collide(self, obj):
        """
        Checks for a collision between the player and another object.

        Args:
            obj (Sprite): The object to check for collision with.

        Returns:
            bool: True if there is a collision, False otherwise.
        """
        if self.rect.colliderect(obj.rect):
            offset_x = obj.rect.x - self.rect.x
            offset_y = obj.rect.y - self.rect.y
            return self.mask.overlap(obj.mask, (offset_x, offset_y)) is not None
        else:
            return False  

    def draw_stamina_bar(self, win):
        """
        Draws stamina bar above the player when the player is sprinting.

        Args:
            win (Surface): The surface on which to draw the stamina bar.
        """
        if self.stamina <= self.max_stamina and self.stamina_bar_timer > 0:
            bar_width = 40
            bar_height = 6
            bar_x = self.rect.centerx - bar_width // 2
            if self.health_bar_timer > 0:
                if self.draw_num_ammo_timer > 0 or self.draw_num_grenades_timer > 0:
                    bar_y = self.rect.top - 29
                else:
                    bar_y = self.rect.top - 17
            elif self.draw_num_ammo_timer > 0 or self.draw_num_grenades_timer > 0:
                bar_y = self.rect.top - 17
            else:
                bar_y = self.rect.top - 5

            stamina_ratio = self.stamina / self.max_stamina
            current_stamina_width = int(bar_width * stamina_ratio)

            pygame.draw.rect(win, GRAY, (bar_x, bar_y, bar_width, bar_height))

            if current_stamina_width > 0:
                pygame.draw.rect(win, CYAN, (bar_x, bar_y, current_stamina_width, bar_height))

            if self.max_stamina > 0:
                threshold_ratio = float(self.SPRINT_THRESHOLD) / float(self.max_stamina)
            else:
                threshold_ratio = 0.0

            threshold_px = int(bar_width * threshold_ratio)
            if threshold_px < 0:
                threshold_px = 0
            if threshold_px > bar_width:
                threshold_px = bar_width

            line_x = bar_x + threshold_px
            pygame.draw.line(win, BLACK, (line_x, bar_y), (line_x, bar_y + bar_height), 1)

            pygame.draw.rect(win, BLACK, (bar_x, bar_y, bar_width, bar_height), 1)


    def draw_health_bar(self, win):
        """
        Draws health bar above the player when the player is hit.

        Args:
            win (Surface): The surface on which to draw the health bar.
        """
        if self.health <= self.max_health and self.health_bar_timer > 0:
            bar_width = 40
            bar_height = 6
            bar_x = self.rect.centerx - bar_width // 2
            if self.draw_num_ammo_timer > 0 or self.draw_num_grenades_timer > 0:
                bar_y = self.rect.top - 17
            else:
                bar_y = self.rect.top - 5

            health_ratio = self.health / self.max_health
            current_health_width = int(bar_width * health_ratio)

            pygame.draw.rect(win, RED, (bar_x, bar_y, bar_width, bar_height))

            if current_health_width > 0:
                pygame.draw.rect(win, LIGHT_GREEN, (bar_x, bar_y, current_health_width, bar_height))

            pygame.draw.rect(win, BLACK, (bar_x, bar_y, bar_width, bar_height), 1)

    def draw_ammo_count(self, win):
        """
        Draws the number of ammo above the player when the player collects more ammo.
        """
        if (self.ammo > 0 and self.draw_num_ammo_timer > 0):
            ammo_img = self.gem_sprites["player_ammo"][0]
            ammo_img = pygame.transform.scale(ammo_img, (TILE_SIZE // 4, TILE_SIZE // 4))
            ammo_x = self.rect.left - 5
            ammo_y = self.rect.top - 7 
            win.blit(ammo_img, (ammo_x, ammo_y))
            ammo_text = str(self.ammo)
            draw_text(ammo_text, "Arial", 13, PINK, win, ammo_x + 11, ammo_y - 3, False)

    def draw_grenade_count(self, win):
        """
        Draws the number of grenades above the player when the player collects more grenades.
        """
        if (self.grenades > 0 and self.draw_num_grenades_timer > 0):
            grenade_img = self.grenade_sprites["Grenade Idle"][0]
            grenade_img = pygame.transform.scale(grenade_img, (TILE_SIZE // 4, TILE_SIZE // 4))
            grenade_x = self.rect.right - 13
            grenade_y = self.rect.top - 7 
            win.blit(grenade_img, (grenade_x, grenade_y))
            grenade_text = str(self.grenades)
            draw_text(grenade_text, "Arial", 13, GREEN, win, grenade_x + 11, grenade_y - 4, False)

    def shoot_ammo(self, ammo_sprites, ammo_group):
        """
        Shoots ammo in the direction the player is facing.
        Creates a PurpleGem object representing the ammo and adds it to the ammo group.

        Args:
            ammo_img (Surface): The image of the ammo sprite.
            ammo_group (Group): Pygame Group to which the ammo object will be added.
        """
        if self.shoot_cooldown == 0 and self.ammo > 0 and self.hit_anim_timer == 0:
            self.shoot_cooldown = 20
            self.ammo -= 1

            if self.direction == "right":
                ammo_direction = pygame.math.Vector2(1, 0)
                ammo_gem = PurpleGem(self.rect.right - self.img.get_width() // 2, self.rect.centery, ammo_sprites, "player_ammo", ammo_direction)
            else:
                ammo_direction = pygame.math.Vector2(-1, 0)
                ammo_gem = PurpleGem(self.rect.left, self.rect.centery, ammo_sprites, "player_ammo", ammo_direction)

            ammo_gem.velocity = ammo_direction * ammo_gem.speed
            ammo_group.add(ammo_gem)

        self.shoot = False

    def launch_grenade(self, grenade_sprites, grenade_group):
        if self.grenade_cooldown == 0 and self.grenades > 0 and self.hit_anim_timer == 0:
            self.grenade_cooldown = 100
            self.grenades -= 1

            if self.direction == "right":
                grenade_direction = pygame.math.Vector2(1, 0)
                grenade = Grenade(self.rect.right - self.img.get_width() // 2, self.rect.centery, grenade_sprites, grenade_direction)
            else:
                grenade_direction = pygame.math.Vector2(-1, 0)
                grenade = Grenade(self.rect.left, self.rect.centery, grenade_sprites, grenade_direction)

            grenade_group.add(grenade)

        self.throw_grenade = False

    def update_sprite(self):
        """
        Updates the player's sprite based on the current animation state (jumping, falling, running, or idle).
        """
        sprite_sheet = "Idle"

        if self.hit_anim_timer > 0:
            sprite_sheet = "Hit"
        else:
            if self.y_vel < 0:
                if self.jump_count == 1:
                    sprite_sheet = "Jump"
                elif self.jump_count == 2:
                    sprite_sheet = "Double_Jump"
            elif self.y_vel > 0:
                sprite_sheet = "Fall"
            elif self.moving_left or self.moving_right:
                sprite_sheet = "Run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        if sprite_sheet_name in self.sprites:
            sprites = self.sprites[sprite_sheet_name]
            sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
            self.img = sprites[sprite_index]
        else:
            fallback_name = "Idle_" + self.direction
            if fallback_name in self.sprites:
                sprites = self.sprites[fallback_name]
                if self.alive:
                    sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
                    self.img = sprites[sprite_index]
                else:
                    self.img = sprites[0]

        self.animation_count += 1

    def update(self):
        """
        Updates the player's state, including animation, position, and cooldowns.
        """
        self.check_alive()
        self.rect.topleft = (int(self.position.x), int(self.position.y))
        self.mask = pygame.mask.from_surface(self.img)

        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if self.grenade_cooldown > 0:
            self.grenade_cooldown -= 1
        if self.stamina_bar_timer > 0:
            self.stamina_bar_timer -= 1
        if self.health_bar_timer > 0:
            self.health_bar_timer -= 1
        if self.hit_anim_timer > 0:
            self.hit_anim_timer -= 1
        if self.draw_num_ammo_timer > 0:
            self.draw_num_ammo_timer -= 1
        if self.draw_num_grenades_timer > 0:
            self.draw_num_grenades_timer -= 1

        if self.is_sprinting:
            self.stamina -= self.SPRINT_DEPLETION
            if self.stamina <= 0:
                self.stamina = 0
                self.is_sprinting = False
                self.speed = self.base_speed
                self.sprint_allowed = False
        else:
            if self.stamina < self.max_stamina:
                self.stamina += self.SPRINT_RECOVERY
                if self.stamina > self.max_stamina:
                    self.stamina = self.max_stamina

            if not self.is_sprinting:
                if self.stamina >= self.SPRINT_THRESHOLD:
                    self.sprint_allowed = True
                else:
                    self.sprint_allowed = False
