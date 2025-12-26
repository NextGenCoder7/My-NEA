import pygame
import math
import random
from constants import *
from objects import CannonBall
from enemies import Enemy


class FierceTooth(Enemy):
    """
    FierceTooth enemy with vision cone, shooting, attacking, and smart behaviour such as dodging bullets 
    and turning direction tracking player based on recent vision.

    Attributes:
        HIT_ANIM_DURATION (int): Duration of hit animation in frames.
        GRENADE_FLEE_DURATION (int): Duration to flee from grenades in frames.
        TURN_COOLDOWN (int): Cooldown time for turning direction in frames.
        SUPPRESS_TURN_DURATION (int): Duration to suppress random turns after losing vision.

        vision_range (int): The range of the enemy's vision.
        vision_angle (int): The angle of the enemy's vision.
        player_in_vision (bool): Whether the player is in the enemy's vision.
        shoot_cooldown (int): The cooldown time for the enemy's shooting.
        attack_range (int): The range of the enemy's attack.
        attack_cooldown (int): The cooldown time for the enemy's attack.
        attacking (bool): Whether the enemy is attacking.
        attack_recovery_timer (int): The timer for the enemy's attack recovery.
        attack_recovery_duration (int): The duration of the enemy's attack recovery.
        post_attack_recovery (bool): Whether the enemy is in post-attack recovery.
        smartmode (bool): Whether the enemy uses advanced AI behaviors.
        recently_lost_vision_timer (int): Timer for recently lost vision state.
        recheck_turn_timer (int): Timer for rechecking turn after losing vision.
        dodge_cooldown (int): The cooldown time for the enemy's dodge.
        grenade_flee_timer (int): Timer for fleeing from grenades.
        turn_cooldown (int): Cooldown timer for turning direction.
        suppress_random_turns_timer (int): Timer to suppress random turns.
        was_hit_from_behind (bool): Whether the enemy was hit from behind.
        hit_anim_timer (int): Timer for Fiercetooth's hit animation.
        enemy_type (string): Showing the enemy species is Fiercetooth.
    """

    HIT_ANIM_DURATION = 120
    GRENADE_FLEE_DURATION = 100
    TURN_COOLDOWN = 15
    SUPPRESS_TURN_DURATION = 120

    def __init__(self, x, y, x_vel, sprites, health, smartmode=False):
        """
        Initialises a FierceTooth enemy with the given parameters.

        Args:
            x (float): Initial x position.
            y (float): Initial y position.
            x_vel (float): Base horizontal speed.
            sprites (dict): Sprite frames for animations.
            health (int): Starting health.
            smartmode (bool): Whether the enemy uses advanced AI behaviors.
        """
        super().__init__(x, y, x_vel, sprites, health)

        self.vision_range = 320
        self.vision_angle = 40
        self.player_in_vision = False

        self.shoot_cooldown = 0

        self.attack_range = 50
        self.attack_cooldown = 0
        self.attacking = False
        self.attack_recovery_timer = 0
        self.attack_recovery_duration = 120
        self.post_attack_recovery = False

        self.smartmode = smartmode
        self.recently_lost_vision_timer = 0
        self.recheck_turn_timer = 0  
        self.dodge_cooldown = 0
        self.grenade_flee_timer = 0

        self.turn_cooldown = 0
        self.suppress_random_turns_timer = 0

        self.was_hit_from_behind = False
        self.hit_anim_timer = 0

        self.enemy_type = "Fiercetooth"
        
    def check_vision_cone(self, player):
        """
        Determine whether the player is within the enemy's vision cone.

        This updates `self.player_in_vision` and `self.attacking` state and returns
        one of: "attack" (player in close attack range and inside cone),
        "shoot" (player in long-range vision cone), or False if not visible.

        Args:
            player (Player): Player object whose position is tested.

        Returns:
            str|bool: "attack", "shoot", or False.
        """
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        distance = math.hypot(dx, dy)

        if (self.y_vel == 0 or self.y_vel == 10) and player.rect.bottom > self.rect.bottom:
            self.player_in_vision = False
            self.attacking = False
            return False

        if distance > self.vision_range:
            self.player_in_vision = False
            self.attacking = False
            return False

        if distance <= self.attack_range:
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
                self.attacking = True
                self.player_in_vision = True
                return "attack"
            else:
                self.attacking = False
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
                self.attacking = False
                self.player_in_vision = True
                return "shoot"
            else:
                self.attacking = False
                self.player_in_vision = False
                return False

        return False

    def check_and_dodge_bullets(self, player_ammo_group):
        """
        If in smartmode, check nearby player projectiles and randomly dodge by jumping.

        This scans the provided ammo group. If a projectile is within a short range
        and within the enemy's forward cone, the enemy may jump to attempt a dodge.

        Args:
            player_ammo_group (Group): Group of player ammo sprites.
        """
        if not self.smartmode or not self.alive:
            return

        if self.dodge_cooldown > 0:
            self.dodge_cooldown -= 1
            return

        for ammo in player_ammo_group:
            if not ammo.alive:
                continue

            dx = ammo.rect.centerx - self.rect.centerx
            dy = ammo.rect.centery - self.rect.centery
            distance = math.hypot(dx, dy)

            if distance < 100:
                angle_to_ammo = math.degrees(math.atan2(dy, dx))
                if angle_to_ammo < 0:
                    angle_to_ammo += 360

                if self.direction == "right":
                    left_bound = 360 - (self.vision_angle / 2)
                    right_bound = self.vision_angle / 2
                    in_vision = (angle_to_ammo >= left_bound or angle_to_ammo <= right_bound)
                else:
                    left_bound = 180 - (self.vision_angle / 2)
                    right_bound = 180 + (self.vision_angle / 2)
                    in_vision = (left_bound <= angle_to_ammo <= right_bound)

                if in_vision and random.random() < 0.3:
                    self.jump()
                    self.dodge_cooldown = 30
                    break  

    def check_and_dodge_grenades(self, player_grenade_group):
        """
        If in smartmode, check nearby player grenades and try to dodge by jumping and/or moving away.

        This scans the provided grenade group. If a projectile is within a short range
        and within the enemy's forward cone, the enemy will to attempt a dodge to prevent death.
        """

        if not self.smartmode or not self.alive:
            return

        if self.dodge_cooldown > 0:
            self.dodge_cooldown -= 1
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
                    self.grenade_flee_timer = self.GRENADE_FLEE_DURATION

                    if dx >= 0:
                        self.direction = "left"
                    else:
                        self.direction = "right"

                    self.state = "running"
                    self.state_timer = 0
                    self.speed = max(self.speed, 3)
                    self.moving_left = (self.direction == "left")
                    self.moving_right = (self.direction == "right")

                    if distance < 60 and abs(dy) < 40:
                        self.jump()

                    self.dodge_cooldown = 30
                    break

    def draw(self, win):
        """
        Draw the enemy on the provided surface.
        """
        win.blit(self.img, self.rect)

    def update_sprite(self, player):
        """
        Update enemy sprite based on the current state (idle/run/jump/fall/attack/recover/hit/dead).
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

    def get_hit(self, damage=20, attacker=None):
        """
        Apply damage to this enemy and optionally update facing direction based on attacker.

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

    def shoot(self, ammo_sprites, ammo_group):
        self.shoot_cooldown = 60
            
        if self.direction == "right":
            ammo_direction = pygame.math.Vector2(1, 0)
            ammo_ball = CannonBall(self.rect.right - self.img.get_width() // 2, self.rect.centery, ammo_sprites, ammo_direction)
        else:
            ammo_direction = pygame.math.Vector2(-1, 0)
            ammo_ball = CannonBall(self.rect.left, self.rect.centery, ammo_sprites, ammo_direction)
            
        ammo_ball.velocity = ammo_direction * ammo_ball.speed
        ammo_group.add(ammo_ball)

    def update(self, player, ammo_sprites, ammo_group):
        """
        Update enemy state for this frame, including vision checks, cooldowns, collisions,
        and smart-mode reactions to the player leaving the vision cone.

        Args:
            player (Player): The player object used for vision and collision checks.
            ammo_sprites (dict): Sprite frames for enemy ammo animations.
            ammo_group (Group): Group to add spawned CannonBall sprites.
        """
        self.check_alive()
        self.rect.topleft = (int(self.position.x), int(self.position.y))
        self.mask = pygame.mask.from_surface(self.img)

        # Capture previous vision state and update current vision once
        previous_vision = self.player_in_vision
        if player:
            vision_result = self.check_vision_cone(player)
        else:
            vision_result = False
        
        # Shooting logic
        if vision_result == "shoot" and self.hit_anim_timer == 0 and self.shoot_cooldown == 0 and random.randint(1, 2) == 1:
            self.shoot(ammo_sprites, ammo_group)

        if self.smartmode and player:
            if previous_vision and not self.player_in_vision:
                self.recently_lost_vision_timer = 30
                if self.turn_cooldown == 0:
                    self.recheck_turn_timer = self.RECHECK_TURN_DURATION

                    dx = player.rect.centerx - self.rect.centerx
                    player_is_behind = (self.direction == "right" and dx <= -10) or (self.direction == "left" and dx >= 10)
                    if not player_is_behind:
                        self.suppress_random_turns_timer = max(self.suppress_random_turns_timer, self.SUPPRESS_TURN_DURATION)
            elif self.recently_lost_vision_timer > 0:
                self.recently_lost_vision_timer -= 1

            if self.turn_cooldown > 0:
                self.turn_cooldown -= 1

            if self.suppress_random_turns_timer > 0:
                self.suppress_random_turns_timer -= 1

            if self.recheck_turn_timer > 0:
                if self.hit_anim_timer == 0:
                    self.recheck_turn_timer -= 1

                    if self.recheck_turn_timer == 0 and not self.player_in_vision and self.turn_cooldown == 0:
                        self.direction = "left" if self.direction == "right" else "right"
                        self.turn_cooldown = self.TURN_COOLDOWN

        if self.health_bar_timer > 0:
            self.health_bar_timer -= 1

        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        if self.grenade_flee_timer > 0:
            self.grenade_flee_timer -= 1

            self.state = "running"
            self.state_timer = 0
            self.speed = max(self.speed, 3)
            self.moving_left = (self.direction == "left")
            self.moving_right = (self.direction == "right")

        if player and self.collide(player):
            if self.y_vel > 0 and self.rect.centery < player.rect.centery and self.rect.bottom >= player.rect.top:
                self.rect.bottom = player.rect.top
                self.position.y = self.rect.y
                self.y_vel = 0
                self.jump_count = 0
                if hasattr(player, "get_hit"):
                    player.get_hit(20, attacker=self)
                    self.post_attack_recovery = True
                    self.attack_recovery_timer = 0
                    self.attack_cooldown = 60

        if self.player_in_vision and not self.post_attack_recovery and self.hit_anim_timer == 0:
            if self.grenade_flee_timer == 0:
                self.speed = 3
                if self.state == "idle":
                    self.state = "running"
                    self.state_timer = 0
        elif self.post_attack_recovery:
            self.speed = 0
            self.state = "idle"
            self.shoot_cooldown = 120
            self.jump_timer = 0
            if self.smartmode and player and self.recently_lost_vision_timer > 0:
                dx = player.rect.centerx - self.rect.centerx
                player_is_behind = (self.direction == "right" and dx <= -10) or (self.direction == "left" and dx >= 10)
                if player_is_behind:
                    self.direction = "left" if self.direction == "right" else "right"
                    self.recently_lost_vision_timer = 0
                    self.recheck_turn_timer = self.RECHECK_TURN_DURATION
                    self.turn_cooldown = self.TURN_COOLDOWN
        elif self.hit_anim_timer > 0:      
            self.attack_cooldown = 60
            self.speed = 0
            self.state = "idle"       
            self.state_timer = 0
            self.jump_timer = 0
            if self.smartmode and player and self.recently_lost_vision_timer > 0:
                dx = player.rect.centerx - self.rect.centerx
                player_is_behind = (self.direction == "right" and dx <= -10) or (self.direction == "left" and dx >= 10)
                if player_is_behind:
                    self.direction = "left" if self.direction == "right" else "right"
                    self.recently_lost_vision_timer = 0
                    self.recheck_turn_timer = self.RECHECK_TURN_DURATION
                    self.turn_cooldown = self.TURN_COOLDOWN
        elif self.smartmode and player and self.recently_lost_vision_timer > 0:
            dx = player.rect.centerx - self.rect.centerx
            player_is_behind = (self.direction == "right" and dx <= -10) or (self.direction == "left" and dx >= 10)
            if player_is_behind and self.turn_cooldown == 0:
                self.direction = "left" if self.direction == "right" else "right"
                # self.jump()
                self.speed = 3
                self.state = "running"
                self.state_timer = 0
                self.recently_lost_vision_timer = 0
                self.recheck_turn_timer = self.RECHECK_TURN_DURATION 
                self.turn_cooldown = self.TURN_COOLDOWN
        else:
            if self.grenade_flee_timer == 0:
                self.speed = 2

        # the collision check for attacking 
        if player and self.collide(player):   
            player_center_y = player.rect.centery
            enemy_center_y = self.rect.centery
            height_difference = abs(player_center_y - enemy_center_y)

            if height_difference < 10:
                if self.attacking and self.attack_cooldown == 0 and self.hit_anim_timer == 0 and self.y_vel < 1:
                    player.get_hit(30, attacker=self)
                    self.post_attack_recovery = True
                    self.attack_recovery_timer = 0
                    self.attack_cooldown = 60
            if self.smartmode and self.grenade_flee_timer == 0:
                dx = player.rect.centerx - self.rect.centerx
                player_is_behind = (self.direction == "right" and dx <= -10) or \
                            (self.direction == "left" and dx >= 10)

                if player_is_behind and not self.post_attack_recovery and self.hit_anim_timer == 0 and self.turn_cooldown == 0:
                    self.direction = "left" if self.direction == "right" else "right"
                    self.attacking = True
                    self.attack_cooldown = 0
                    self.recheck_turn_timer = self.RECHECK_TURN_DURATION
                    self.turn_cooldown = self.TURN_COOLDOWN

        if self.post_attack_recovery:
            self.attack_recovery_timer += 1
            if self.attack_recovery_timer >= self.attack_recovery_duration:
                self.post_attack_recovery = False
                self.attack_recovery_timer = 0

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

        # Clip rays at the floor when grounded; allow full rays when airborne
        if self.y_vel == 0 or self.y_vel == 10:
            floor_y = self.rect.bottom

            def clip_and_flatten(x, y):
                if y <= floor_y:
                    return x, y
                # If the ray points below the floor, flatten it to floor level and extend forward horizontally
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