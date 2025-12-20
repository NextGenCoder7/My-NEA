import pygame
from enemies import Enemy
import math


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

        self.chasing_player = False

        self.attacking = False
        self.attack_range = 40
        self.attack_cooldown = 0
        self.attack_recovery_timer = 0
        self.attack_recovery_duration = 350
        self.post_attack_recovery = False

        self.hit_anim_timer = 0

        self.enemy_type = "Pink Star"

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
        """
        if not self.alive:
            sprite_sheet = "Dead"
        else:
            if not player.alive:
                sprite_sheet = "Idle"
            else:
                if self.post_attack_recovery:
                    sprite_sheet = "Recover"  
                elif self.attacking:
                    sprite_sheet = "Attack"
                elif self.hit_anim_timer > 0:
                    sprite_sheet = "Hit"
                else:
                    if self.y_vel < 0:
                        sprite_sheet = "Jump"
                    elif self.y_vel > 0:
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

    def update(self, player):
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

        # for now I'll just make it so that if the player is within a certain distance, it starts "chasing" (will adjust this later)
        # will overwrite handle movement function from Enemy class for movement on path from A* algorithm
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        distance = math.hypot(dx, dy)

        if distance <= self.attack_range:
            if self.direction == "left" and dx < 0:
                self.attacking = True
            elif self.direction == "right" and dx > 0:
                self.attacking = True
        elif distance <= 170 and not self.post_attack_recovery and self.hit_anim_timer == 0:
            self.chasing_player = True
        else:
            self.chasing_player = False

        if self.health_bar_timer > 0:
            self.health_bar_timer -= 1
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        if player and self.collide(player):
            if self.y_vel > 0 and self.rect.centery < player.rect.centery and self.rect.bottom >= player.rect.top:
                self.rect.bottom = player.rect.top
                self.position.y = self.rect.y
                self.y_vel = 0
                self.jump_count = 0
                if hasattr(player, "get_hit"):
                    player.get_hit(50, attacker=self)
        
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
            self.attack_cooldown = 100
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
                    self.attack_cooldown = 100

        if self.post_attack_recovery:
            self.attack_recovery_timer += 1
            if self.attack_recovery_timer >= self.attack_recovery_duration:
                self.post_attack_recovery = False
                self.attack_recovery_timer = 0

        if self.hit_anim_timer > 0:
            self.hit_anim_timer -= 1 
        