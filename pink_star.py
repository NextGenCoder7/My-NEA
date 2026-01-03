import pygame
from enemies import Enemy
import math
import random
from constants import RED, PURPLE


class PinkStar(Enemy):
    """
    A PinkStar enemy that chases the player and attacks when the player is in its lair,
    using the A* algorithm to relentlessly chase the player.

    Attributes:
        HIT_ANIM_DURATION (int): Duration of hit animation in frames.

        chasing_player (bool): Whether the enemy is currently chasing the player.
        attacking (bool): Whether the enemy is attacking.
        attack_range (int): Distance within which the enemy can attack the player.
        attack_cooldown (int): Cooldown timer for attacks.
        attack_recovery_timer (int): Timer for recovery after an attack.
        attack_recovery_duration (int): Duration of recovery after an attack.
        post_attack_recovery (bool): Whether the enemy is in post-attack recovery state.
        hit_anim_timer (int): Timer for hit animation duration.
        enemy_type (str): Type identifier for the enemy.
    """

    HIT_ANIM_DURATION = 300

    def __init__(self, x, y, x_vel, sprites, health):
        """
        Initialises a PinkStar enemy with the given parameters. This enemy has no vision because it 'senses' the player.

        Args:
            x (float): Initial x position.
            y (float): Initial y position.
            x_vel (float): Base horizontal speed.
            sprites (dict): Sprite frames for animations.
            health (int): Starting health.
        """
        super().__init__(x, y, x_vel, sprites, health)
        self.death_fall_speed_cap = 1
        self.death_handled = False

        self.chasing_player = False
        self.path = []

        self.attacking = False
        self.attack_range = 50
        self.attack_cooldown = 0
        self.attack_recovery_timer = 0
        self.attack_recovery_duration = 350
        self.post_attack_recovery = False

        self.hit_anim_timer = 0

        self.enemy_type = "Pink Star"

    def handle_death(self):
        self.y_vel += self.GRAVITY
        if self.y_vel > self.death_fall_speed_cap:
            self.y_vel = self.death_fall_speed_cap

        self.velocity.y += self.y_vel

        if self.rect.bottom + self.velocity.y > 400:
            self.velocity.y = 400 - self.rect.bottom
            self.jump_count = 0
            self.y_vel = 0
            self.death_handled = True

        self.position += self.velocity
        self.rect.topleft = (int(self.position.x), int(self.position.y))

    def handle_movement(self, obstacle_list, constraint_rect_group, player):
        """
        Handles AI movement logic (specific movement for Pink Star enemies).
        """
        self.velocity.x = 0
        self.moving_left = False
        self.moving_right = False

        self.state_timer += 1
        if self.state_timer >= self.state_duration:
            if self.state == "idle":
                if random.random() < 0.5:
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

        if player and self.collide(player):
            if dy > 0 and self.rect.centery < player.rect.centery and self.rect.bottom >= player.rect.top:
                self.rect.bottom = player.rect.top
                self.position.y = self.rect.y
                self.y_vel = -7
                self.jump_count = 1
                self.on_ground = False

                if hasattr(player, "get_hit") and player.alive:
                    player.get_hit(50, attacker=self)
                    self.post_attack_recovery = True
                    self.attack_recovery_timer = 0
                    self.attack_cooldown = 150
            elif dy < 0 and self.rect.centery > player.rect.centery and self.rect.top <= player.rect.bottom:
                self.rect.top = player.rect.bottom
                self.position.y = self.rect.y

        for constraint in constraint_rect_group:
            if constraint.colour == RED:
                if self.rect.colliderect(constraint.rect):
                    if dy > 0:  
                        self.rect.bottom = constraint.rect.top
                        self.position.y = self.rect.y
                        self.y_vel = 0
                        self.jump_count = 0
                        self.on_ground = True
                    elif dy < 0:  
                        self.rect.top = constraint.rect.bottom
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

        if player and self.collide(player):
            if self.velocity.x > 0:  
                self.rect.right = player.rect.left
            elif self.velocity.x < 0:  
                self.rect.left = player.rect.right

            self.position.x = self.rect.x

        for constraint in constraint_rect_group:
            if constraint.colour == RED:
                if self.rect.colliderect(constraint.rect):
                    if self.velocity.x > 0:  
                        self.direction = "left"
                        self.rect.right = constraint.rect.left
                    elif self.velocity.x < 0:
                        self.direction = "right"
                        self.rect.left = constraint.rect.right

                    self.position.x = self.rect.x

    def draw(self, win):
        """
        Draw the enemy on the provided surface.
        """
        win.blit(self.img, self.rect)

    def get_hit(self, damage=20, attacker=None):
        """
        Apply damage to this enemy based on the attacker.
        """
        if self.hit_anim_timer > 0:
            return

        self.health -= damage
        self.health_bar_timer = self.HEALTH_BAR_DURATION

        if attacker and hasattr(attacker, 'is_grenade') and attacker.is_grenade:
            self.hit_anim_timer = self.HIT_ANIM_DURATION
        
    def update_sprite(self, player):
        """
        Update the enemy's sprite based on its current state (idle/run/jump/fall/attack/recover/hit/dead).

        Same priority system as FierceTooth.
        """
        if not self.alive:
            sprite_sheet = "Dead"
        else:
            if player and player.alive:
                if self.hit_anim_timer > 0:
                    sprite_sheet = "Hit"
                elif self.post_attack_recovery:
                    sprite_sheet = "Recover"
                elif self.attacking:
                    sprite_sheet = "Attack"
                else:
                    if self.y_vel < 0:
                        sprite_sheet = "Jump"
                    elif self.y_vel > 0 and not self.on_ground:
                        sprite_sheet = "Fall"
                    elif self.moving_left or self.moving_right:
                        sprite_sheet = "Run"
                    else:
                        sprite_sheet = "Idle"
            else:
                if self.hit_anim_timer > 0:
                    sprite_sheet = "Hit"
                elif self.y_vel < 0:
                    sprite_sheet = "Jump"
                elif self.y_vel > 0 and not self.on_ground:
                    sprite_sheet = "Fall"
                elif self.moving_left or self.moving_right:
                    sprite_sheet = "Run"
                else:
                    sprite_sheet = "Idle"

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

    def update(self, player, constraint_rect_group):
        """
        Update the enemy's state, which includes chasing and attacking the player.
        Also handles cooldowns, collisions.

        Args:
            player (Player): The player object to interact with.
        """
        self.check_alive()
        self.rect.topleft = (int(self.position.x), int(self.position.y))
        self.mask = pygame.mask.from_surface(self.img)

        self.attacking = False

        if constraint_rect_group and self.alive:
            for constraint in constraint_rect_group:
                if constraint.colour != PURPLE:
                    continue

                if not self.rect.colliderect(constraint.rect):
                    continue
                else:
                    if self.direction == "right":
                        if self.rect.right != constraint.rect.right:
                            continue
                    else:
                        if self.rect.left != constraint.rect.left:
                            continue

                    if self.on_ground and self.jump_count < 1: 
                        self.speed = 4
                        self.jump()
                        break

        if self.health_bar_timer > 0:
            self.health_bar_timer -= 1
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        
        if self.chasing_player and not self.post_attack_recovery and self.hit_anim_timer == 0:
            self.speed = 4
            if self.state == "idle":
                self.state = "running"
                self.state_timer = 0
        elif self.post_attack_recovery:
             self.speed = 0
             self.state = "idle"
             self.jump_timer = 0
        elif self.hit_anim_timer > 0:
            self.attack_cooldown = 150
            self.speed = 0
            self.state = "idle"       
            self.state_timer = 0
            self.jump_timer = 0
        else:
            self.speed = 3

        if player and self.collide(player): 
            player_center_y = player.rect.centery
            enemy_center_y = self.rect.centery
            height_difference = abs(player_center_y - enemy_center_y)

            if height_difference < 10:
                if self.attacking and self.attack_cooldown == 0 and self.hit_anim_timer == 0:
                    player.get_hit(90, attacker=self)
                    self.attacking = False
                    self.post_attack_recovery = True
                    self.attack_recovery_timer = 0
                    self.attack_cooldown = 150

        if self.post_attack_recovery:
            self.attack_recovery_timer += 1
            if self.attack_recovery_timer >= self.attack_recovery_duration:
                self.post_attack_recovery = False
                self.attack_recovery_timer = 0

        if self.hit_anim_timer > 0:
            self.hit_anim_timer -= 1 
        