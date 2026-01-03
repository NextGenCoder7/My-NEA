import pygame
import random
from constants import *


class Enemy(pygame.sprite.Sprite):
    """
    Base class for all enemy types in the game.
    Handles movement, health, collision, and sprite updates.

    Attributes:
        ANIMATION_DELAY (int): Delay in frames between sprite animations.
        HEALTH_BAR_DURATION (int): Duration for which the health bar is displayed after taking damage.
        GRAVITY (float): Gravity strength affecting the enemy.

        sprites (dict): Dictionary containing different sprites for the enemy animations.
        direction (str): Current facing direction ("left" or "right").
        img (Surface): Current image/sprite of the enemy.
        animation_count (int): Counter for animation frame updates.
        position (Vector2): Current position of the enemy.
        velocity (Vector2): Current velocity of the enemy.
        speed (float): Horizontal movement speed of the enemy.
        y_vel (float): Current vertical velocity of the enemy.
        alive (bool): Whether the enemy is alive.
        rect (Rect): Rectangular area representing the enemy's position and size.
        mask (Mask): Pixel-perfect collision mask for the enemy.
        is_enemy (bool): Proving that this object is an Enemy.
        jump_count (int): Counter for jumps made by the enemy.
        shoot_cooldown (int): Cooldown timer for shooting projectiles.
        health (int): Current health of the enemy.
        max_health (int): Maximum health of the enemy.
        health_bar_timer (int): Timer for displaying the health bar after taking damage.

        state (str): Current AI state ("idle" or "running").
        state_timer (int): Timer for the current AI state duration.
        state_duration (int): Duration for the current AI state.
        jump_timer (int): Timer for jump intervals.
        jump_interval (int): Interval between jumps.

        moving_left (bool): Whether the enemy is currently moving left.
        moving_right (bool): Whether the enemy is currently moving right.

        is_enemy (bool): Flag to identify this object as an enemy.
    """

    ANIMATION_DELAY = 6
    HEALTH_BAR_DURATION = 180
    GRAVITY = 0.7
    RECHECK_TURN_DURATION = 55
    
    def __init__(self, x, y, x_vel, sprites, health):
        """
        Initialise the enemy with position, speed, sprites, and health.

        Args:
            x (float): Initial x position.
            y (float): Initial y position.
            x_vel (float): Horizontal movement speed.
            sprites (dict): Dictionary of sprite frames for animations.
            health (int): Initial health of the enemy.
        """
        super().__init__()
        self.sprites = sprites
        self.direction = "left"
        self.img = self.sprites['Idle_' + self.direction][0]
        self.animation_count = 0
        self.position = pygame.math.Vector2(x, y)
        self.velocity = pygame.math.Vector2(0, 0)
        self.speed = x_vel
        self.on_ground = False
        self.y_vel = 0
        self.alive = True
        self.rect = self.img.get_rect(topleft=(int(self.position.x), int(self.position.y)))
        self.mask = pygame.mask.from_surface(self.img)
        self.jump_count = 0
        self.shoot_cooldown = 0
        self.health = health
        self.max_health = self.health
        self.health_bar_timer = 0
        
        self.state = "idle"  # "idle" or "running"
        self.state_timer = 0
        self.state_duration = random.randint(60, 180)  
        self.jump_timer = 0
        self.jump_interval = random.randint(120, 300) 
        
        self.moving_left = False
        self.moving_right = False

        self.is_enemy = True
        self.enemy_type = ""
        
    def handle_movement(self, obstacle_list, constraint_rect_group, player):
        """
        Handles AI movement logic (general default movement for all enemies).
        """
        self.velocity.x = 0
        self.moving_left = False
        self.moving_right = False
        
        self.state_timer += 1
        if self.state_timer >= self.state_duration:
            if self.state == "idle":
                if not (getattr(self, 'suppress_random_turns_timer', 0) > 0) and random.random() < 0.5:
                    self.direction = "left" if self.direction == "right" else "right"
                self.state = "running"
                self.state_duration = random.randint(60, 180)
            else:
                self.state = "idle"
                self.state_duration = random.randint(60, 180)
            self.state_timer = 0
        
        if self.state == "running":
            if self.direction == "right":
                self.velocity.x = self.speed
                self.moving_right = True
            else:
                self.velocity.x = -self.speed
                self.moving_left = True
        
        self.y_vel += self.GRAVITY
        if self.y_vel > 10:
            self.y_vel = 10
        
        dy = self.y_vel

        self.position.y += dy
        self.rect.topleft = (int(self.position.x), int(self.position.y))
        self.mask = pygame.mask.from_surface(self.img)

        for tile in obstacle_list:
            if self.rect.colliderect(tile.collide_rect):         
                if dy > 0:  
                    self.rect.bottom = tile.collide_rect.top
                    self.position.y = self.rect.y
                    self.y_vel = 0
                    self.jump_count = 0
                    self.on_ground = True
                elif dy < 0:  
                    self.rect.top = tile.collide_rect.bottom
                    self.position.y = self.rect.y
                    self.y_vel = 0
        
        self.position.x += self.velocity.x
        self.rect.topleft = (int(self.position.x), int(self.position.y))
        self.mask = pygame.mask.from_surface(self.img)

        for tile in obstacle_list:
            if self.rect.colliderect(tile.collide_rect):
                if self.velocity.x > 0:  
                    self.direction = "left"
                    self.rect.right = tile.collide_rect.left
                elif self.velocity.x < 0:  
                    self.direction = "right"
                    self.rect.left = tile.collide_rect.right

                self.position.x = self.rect.x

        if self.rect.left + self.velocity.x <= 0:
            self.direction = "right"
            self.velocity.x = 0
            self.position.x = 0
        elif self.rect.right + self.velocity.x > WORLD_WIDTH:
            self.direction = "left"
            self.velocity.x = 0
            self.position.x = WORLD_WIDTH - self.rect.width
    
    def jump(self):
        """
        Make the enemy jump once by setting vertical velocity.

        This method supports a single jump only for the enemies, and increments the internal jump counter.
        """
        if self.jump_count < 1:
            if self.enemy_type == "Fiercetooth":
                self.y_vel = -14
            elif self.enemy_type == "Pink Star":
                self.y_vel = -13

            self.jump_count += 1
            self.on_ground = False

    def get_hit(self, damage=20):
        """
        Apply damage to the enemy and start the health bar display timer.

        Args:
            damage (int): Amount of health to subtract (default 20).
        """
        self.health -= damage
        self.health_bar_timer = self.HEALTH_BAR_DURATION
    
    def draw(self, win):
        """
        Draw the enemy image to the provided surface.
        """
        win.blit(self.img, self.rect)

    def draw_health_bar(self, win):
        """
        Draw health bar above enemy when enemy is hit

        Args:
            win (Surface): The surface on which to draw the health bar.
        """
        if self.health < self.max_health and self.health_bar_timer > 0 and self.alive:
            bar_width = 40
            bar_height = 6
            bar_x = self.rect.centerx - bar_width // 2
            bar_y = self.rect.top - 5

            health_ratio = self.health / self.max_health
            current_health_width = int(bar_width * health_ratio)

            pygame.draw.rect(win, (255, 0, 0), (bar_x, bar_y, bar_width, bar_height))

            if current_health_width > 0:
                pygame.draw.rect(win, (0, 255, 0), (bar_x, bar_y, current_health_width, bar_height))

            pygame.draw.rect(win, (0, 0, 0), (bar_x, bar_y, bar_width, bar_height), 1)

    def check_alive(self):
        """
        Check enemy health and mark it dead if health is zero or below.
        """
        if self.health <= 0:
            self.health = 0
            self.speed = 0
            self.alive = False 

    def collide(self, obj):
        """
        Check pixel-perfect collision with another sprite using masks.

        Returns True if masks overlap, otherwise False.
        """
        if self.rect.colliderect(obj.rect):
            offset_x = obj.rect.x - self.rect.x
            offset_y = obj.rect.y - self.rect.y
            return self.mask.overlap(obj.mask, (offset_x, offset_y)) is not None
        else:
            return False
    
    def update_sprite(self):
        """
        Update enemy sprite based on current state.
        """
        if not self.alive:
            sprite_sheet = "Dead"
        else:
            sprite_sheet = "Idle"

            if self.y_vel < 0:
                sprite_sheet = "Jump"
            elif self.y_vel > 0 and not self.on_ground:
                sprite_sheet = "Fall"
            elif self.moving_left or self.moving_right:
                sprite_sheet = "Run"
        
        sprite_sheet_name = sprite_sheet + "_" + self.direction
        if sprite_sheet_name in self.sprites:
            sprites = self.sprites[sprite_sheet_name]
            if not self.alive:
                sprite_index = min(self.animation_count // self.ANIMATION_DELAY, len(sprites) - 1)
            else:
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
        Update enemy state.
        """
        self.check_alive()
        self.rect.topleft = (int(self.position.x), int(self.position.y))
        self.mask = pygame.mask.from_surface(self.img)

        if self.health_bar_timer > 0:
            self.health_bar_timer -= 1
