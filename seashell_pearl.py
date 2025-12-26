import pygame
import math
import random
from constants import *
from enemies import Enemy
from objects import Pearl


class SeashellPearl(Enemy):
    """
    SeashellPearl enemy that remains stationary and attacks the player with pearl projectiles or bites when close.
    Can also turn direction and tracker player based on recent vision.

    Attributes:
        HIT_ANIM_DURATION (int): Duration of hit animation in frames.
        TURN_COOLDOWN (int): Cooldown duration for turning direction in smartmode.

        vision_range (int): Maximum distance at which the enemy can see the player.
        vision_angle (int): Angle of the enemy's vision cone.
        player_in_vision (bool): Whether the player is currently within the enemy's vision cone.
        fire_cooldown (int): Cooldown timer for firing pearl projectiles.
        bite_range (int): Distance within which the enemy can perform a bite attack.
        bite_cooldown (int): Cooldown timer for bite attacks.
        biting (bool): Whether the enemy is currently performing a bite attack.
        bite_animation_timer (int): Timer for keeping track of biting animation.
        bite_animation_duration (int): A set duration to make sure the enemy completes bite motion before switching sprite.
        smartmode (bool): If True, the enemy will turn to face the player when hit.
        recently_lost_vision_timer (int): Timer for recently lost vision state in smartmode.
        recheck_turn_timer (int): Timer for rechecking direction after turning in smartmode.
        turn_cooldown (int): Cooldown timer for turning direction in smartmode.
        was_hit_from_behind (bool): Whether the enemy was hit from behind.
        hit_anim_timer (int): Timer for displaying hit animation when damaged by the player.
        enemy_type (str): Type identifier for the enemy.
    """

    HIT_ANIM_DURATION = 120
    TURN_COOLDOWN = 15

    def __init__(self, x, y, x_vel, sprites, health, smartmode=False):
        """
        Initialises a SeashellPearl enemy with the given parameters. This enemy does not move from its position.

        Args:
            x (float): Initial x position.
            y (float): Initial y position.
            x_vel (float): Base horizontal speed.
            sprites (dict): Sprite frames for animations.
            health (int): Starting health.
        """
        super().__init__(x, y, x_vel, sprites, health)

        self.vision_range = 400
        self.vision_angle = 20
        self.player_in_vision = False

        self.fire_cooldown = 0

        self.bite_range = 40
        self.bite_cooldown = 0
        self.biting = False
        self.bite_animation_timer = 0
        self.bite_animation_duration = 30

        self.smartmode = smartmode
        self.recently_lost_vision_timer = 0
        self.recheck_turn_timer = 0  
        self.turn_cooldown = 0

        self.was_hit_from_behind = False
        self.hit_anim_timer = 0

        self.enemy_type = "Seashell Pearl"

    def check_vision_cone(self, player):
        """
        Determine whether the player is within the enemy's vision cone.

        Args:
            player (Player): Player object whose position is tested.

        Returns:
            string: "bite" if the player is within the bite range, "fire" if the player is within the vision range, False otherwise.
        """
        if not player or not player.alive:
            self.player_in_vision = False
            self.biting = False
            return False
        
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        distance = math.hypot(dx, dy)

        if player.rect.bottom > self.rect.bottom:
            self.player_in_vision = False
            self.biting = False
            return False

        if distance > self.vision_range:
            self.player_in_vision = False
            self.biting = False
            return False

        if distance <= self.bite_range:
            angle_to_player = math.degrees(math.atan2(dy, dx))
            if angle_to_player < 0:
                angle_to_player += 360

            if self.direction == "right":
                left_bound = 360 - (self.vision_angle / 2)
                right_bound = self.vision_angle / 2
                in_vision = (angle_to_player >= left_bound or angle_to_player <= right_bound)
            else:
                left_bound = 180 - (self.vision_angle / 2)
                right_bound = 180 + (self.vision_angle / 2)
                in_vision = (left_bound <= angle_to_player <= right_bound)

            if in_vision:
                self.biting = True
                self.player_in_vision = True
                return "bite"
            else:
                self.biting = False
                self.player_in_vision = False
                return False

        elif distance <= self.vision_range:
            angle_to_player = math.degrees(math.atan2(dy, dx))
            if angle_to_player < 0:
                angle_to_player += 360

            if self.direction == "right":
                left_bound = 360 - (self.vision_angle / 2)
                right_bound = self.vision_angle / 2
                in_vision = (angle_to_player >= left_bound or angle_to_player <= right_bound)
            else:
                left_bound = 180 - (self.vision_angle / 2)
                right_bound = 180 + (self.vision_angle / 2)
                in_vision = (left_bound <= angle_to_player <= right_bound)

            if in_vision:
                self.biting = False
                self.player_in_vision = True
                return "fire"
            else:
                self.biting = False
                self.player_in_vision = False
                return False

        return False 

    def react_to_grenades(self, player, player_grenade_group):
        if not self.smartmode or not self.alive:
            return

        for grenade in player_grenade_group:
            if not grenade.alive:
                continue

            dx = grenade.rect.centerx - self.rect.centerx
            dy = grenade.rect.centery - self.rect.centery
            distance = math.hypot(dx, dy)

            if distance < 150:
                angle_to_grenade = math.degrees(math.atan2(dy, dx))
                if angle_to_grenade < 0:
                    angle_to_grenade += 360
                if self.direction == "right":
                    left_bound = 360 - (self.vision_angle / 2)
                    right_bound = self.vision_angle / 2
                    in_vision = (angle_to_grenade >= left_bound or angle_to_grenade <= right_bound)
                else:
                    left_bound = 180 - (self.vision_angle / 2)
                    right_bound = 180 + (self.vision_angle / 2)
                    in_vision = (left_bound <= angle_to_grenade <= right_bound)

                if in_vision:
                    if self.turn_cooldown == 0:
                        dx = player.rect.centerx - self.rect.centerx
                        if self.direction == "right" and dx < 0:
                            self.direction = "left"                       
                        elif self.direction == "left" and dx > 0:
                            self.direction = "right"

                        self.turn_cooldown = self.TURN_COOLDOWN
                    break

    def draw(self, win):
        """
        Draw the enemy on the provided surface.
        """
        win.blit(self.img, self.rect)

    def update_sprite(self, player):
        """
        Update enemy sprite based on the current state (idle/seashell bite/seashell fire/seashell hit/dead).

        Dead > Hit > Bite > Fire > Idle. When the player is dead, the enemy won't pick bite/fire.
        """
        if not self.alive:
            sprite_sheet = "Dead"
        else:
            if player and player.alive:
                if self.hit_anim_timer > 0:
                    sprite_sheet = "Seashell Hit"
                elif self.biting:
                    sprite_sheet = "Seashell Bite"
                elif self.player_in_vision:
                    sprite_sheet = "Seashell Fire"
                else:
                    sprite_sheet = "Idle"
            else:
                if self.hit_anim_timer > 0:
                    sprite_sheet = "Seashell Hit"
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

    def get_hit(self, damage=20, attacker=None):
        """
        Apply damage to this enemy when hit

        When in smartmode and an attacker is provided, the enemy will turn to face the attacker.
        """
        if self.hit_anim_timer > 0:
            return

        self.health -= damage
        self.health_bar_timer = self.HEALTH_BAR_DURATION

        if self.smartmode and attacker:
            if hasattr(attacker, 'rect'):
                dx = attacker.rect.centerx - self.rect.centerx
            else:
                dx = attacker[0] - self.rect.centerx

            if self.direction == "right" and dx < 0:
                self.direction = "left"
                self.was_hit_from_behind = True
            elif self.direction == "left" and dx > 0:
                self.direction = "right"
                self.was_hit_from_behind = True

        if attacker and ((hasattr(attacker, 'is_player') and attacker.is_player) or \
            (hasattr(attacker, 'is_grenade') and attacker.is_grenade)):
            self.hit_anim_timer = self.HIT_ANIM_DURATION

    def fire(self, ammo_sprites, ammo_group):
        """
        Fire a pearl projectile in the current facing direction.

        Args:
            ammo_sprites (dict): Sprite frames for enemy ammo animations.
            ammo_group (Group): Group to add spawned Pearl sprites.
        """

        self.fire_cooldown = 32  

        if self.direction == "right":
            ammo_direction = pygame.math.Vector2(1, 0)
            ammo_ball = Pearl(self.rect.left - 2, self.rect.centery, ammo_sprites, ammo_direction)
        else:
            ammo_direction = pygame.math.Vector2(-1, 0)
            ammo_ball = Pearl(self.rect.left + 5, self.rect.centery, ammo_sprites, ammo_direction)

        ammo_ball.velocity = ammo_direction * ammo_ball.speed
        ammo_group.add(ammo_ball)

    def update(self, player, ammo_sprites, ammo_group):
        """
        Update enemy state for this frame, including vision checks, cooldowns and collisions.

        Args:
            player (Player): The player object used for vision and collision checks.
            ammo_sprites (dict): Sprite frames for enemy ammo animations.
            ammo_group (Group): Group to add spawned Pearl sprites.
        """

        self.check_alive()
        self.rect.topleft = (int(self.position.x), int(self.position.y))
        self.mask = pygame.mask.from_surface(self.img)

        previous_vision = self.player_in_vision
        if player:
            vision_result = self.check_vision_cone(player)
        else:
            vision_result = False

        if player and self.biting:
            if self.bite_animation_timer < self.bite_animation_duration:
                self.bite_animation_timer += 1
            else:
                # Bite finished
                self.bite_animation_timer = 0
                self.biting = False

        # Firing logic
        if vision_result == "fire" and self.fire_cooldown == 0 and self.hit_anim_timer == 0: 
            self.fire(ammo_sprites, ammo_group)

        if self.smartmode and player:
            if previous_vision and not self.player_in_vision:
                self.recently_lost_vision_timer = 30
                if self.turn_cooldown == 0:
                    self.recheck_turn_timer = self.RECHECK_TURN_DURATION
            elif self.recently_lost_vision_timer > 0:
                self.recently_lost_vision_timer -= 1

            if self.turn_cooldown > 0:
                self.turn_cooldown -= 1

            if self.recheck_turn_timer > 0:
                if self.hit_anim_timer == 0:
                    self.recheck_turn_timer -= 1

                    if self.recheck_turn_timer == 0 and not self.player_in_vision and self.turn_cooldown == 0:
                        self.direction = "left" if self.direction == "right" else "right"
                        self.turn_cooldown = self.TURN_COOLDOWN

        if self.health_bar_timer > 0:
            self.health_bar_timer -= 1

        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1
        if self.bite_cooldown > 0:
            self.bite_cooldown -= 1

        if self.hit_anim_timer > 0:    
            self.bite_cooldown = 60

        if self.smartmode and player and self.recently_lost_vision_timer > 0:
            dx = player.rect.centerx - self.rect.centerx
            player_is_behind = (self.direction == "right" and dx <= -10) or (self.direction == "left" and dx >= 10)
            if player_is_behind and self.turn_cooldown == 0:
                self.direction = "left" if self.direction == "right" else "right"
                self.recently_lost_vision_timer = 0
                self.recheck_turn_timer = self.RECHECK_TURN_DURATION    
                self.turn_cooldown = self.TURN_COOLDOWN

        # Handle bite damage after bite starts
        if player and self.biting and self.bite_cooldown == 0:
            dx = player.rect.centerx - self.rect.centerx
            dy = player.rect.centery - self.rect.centery
            distance = math.hypot(dx, dy)
            
            if distance <= self.bite_range:
                if player.alive:
                    player.get_hit(40, attacker=self)
                self.bite_cooldown = 90
                if self.bite_animation_timer == 0:
                    self.bite_animation_timer = 1

        if player and self.collide(player):
            player_center_y = player.rect.centery
            enemy_center_y = self.rect.centery
            height_difference = abs(player_center_y - enemy_center_y)

            if height_difference < 10:
                if self.smartmode:
                    dx = player.rect.centerx - self.rect.centerx
                    player_is_behind = (self.direction == "right" and dx <= -10) or \
                                (self.direction == "left" and dx >= 10)

                    if player_is_behind and self.hit_anim_timer == 0 and self.turn_cooldown == 0:
                        self.direction = "left" if self.direction == "right" else "right"
                        self.biting = True
                        self.bite_cooldown = 0
                        self.recheck_turn_timer = self.RECHECK_TURN_DURATION
                        self.turn_cooldown = self.TURN_COOLDOWN

        if self.hit_anim_timer > 0:
            self.hit_anim_timer -= 1   

    def draw_vision_cone(self, win, player):
        """
        Draw a debug visualisation of the enemy's vision cone and a line to the player when in vision.

        Args:
            win (Surface): Surface to draw on.
            player (Player): Player object for drawing a line when visible.
        """
        if not self.alive:
            return

        center_x = self.rect.centerx
        center_y = self.rect.centery

        base_angle = 0 if self.direction == "right" else 180
        half_angle = self.vision_angle / 2
        left_angle = math.radians(base_angle - half_angle)
        right_angle = math.radians(base_angle + half_angle)
        
        left_x = center_x + self.vision_range * math.cos(left_angle)
        left_y = center_y + self.vision_range * math.sin(left_angle)
        right_x = center_x + self.vision_range * math.cos(right_angle)
        right_y = center_y + self.vision_range * math.sin(right_angle)

        # Seashell is stationary: always clip rays at its floor level
        floor_y = self.rect.bottom

        def clip_and_flatten(x, y):
            if y <= floor_y:
                return x, y
            # Flatten to floor level and extend forward horizontally from center
            direction_sign = 1 if x >= center_x else -1
            return center_x + direction_sign * self.vision_range, floor_y

        left_x, left_y = clip_and_flatten(left_x, left_y)
        right_x, right_y = clip_and_flatten(right_x, right_y)

        cone_points = [
            (center_x, center_y),
            (left_x, left_y),
            (right_x, right_y)
        ]
        pygame.draw.polygon(win, (255, 0, 0, 100), cone_points, 2)
        
        if self.player_in_vision:
            pygame.draw.line(win, (0, 255, 0), (center_x, center_y), 
                        (player.rect.centerx, player.rect.centery), 2)
