import pygame
import math
import random
from constants import *
from objects import CannonBall
from enemies import Enemy
from level import shot_fx


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

        self.death_fall_speed_cap = 10
        self.death_handled = False

        self.vision_range = 350
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
        self.last_chase_direction = None 
        self.continue_chase_timer = 0  
        self.continue_chase_duration = 300 
        self.pursuing_purple_rect = None
        self.delayed_turn_duration = 0

        self.was_hit_from_behind = False
        self.hit_anim_timer = 0

        self.enemy_type = "Fiercetooth"

    def handle_death(self, obstacle_list):
        self.y_vel += self.GRAVITY
        if self.y_vel > self.death_fall_speed_cap:
            self.y_vel = self.death_fall_speed_cap

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
                    self.death_handled = True

        self.position += self.velocity
        self.rect.topleft = (int(self.position.x), int(self.position.y))

    def handle_movement(self, obstacle_list, constraint_rect_group, player):
        """
        Handles AI movement logic (specific movement for Fiercetooth enemies).
        """
        self.velocity.x = 0
        self.moving_left = False
        self.moving_right = False
        
        self.state_timer += 1
        if self.state_timer >= self.state_duration:
            if self.state == "idle":
                if not(self.suppress_random_turns_timer > 0) and random.random() < 0.5:
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
                self.y_vel = -11
                self.jump_count = 1
                self.on_ground = False

                if hasattr(player, "get_hit") and player.alive:
                    player.get_hit(20, attacker=self)
                    self.post_attack_recovery = True
                    self.attack_recovery_timer = 0
                    self.attack_cooldown = 60
            elif dy < 0 and self.rect.centery > player.rect.centery and self.rect.top <= player.rect.bottom:
                self.rect.top = player.rect.bottom
                self.position.y = self.rect.y
        
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

        if self.rect.left + self.velocity.x <= 0:
            self.direction = "right"
            self.velocity.x = 0
            self.position.x = 0
        elif self.rect.right + self.velocity.x > WORLD_WIDTH:
            self.direction = "left"
            self.velocity.x = 0
            self.position.x = WORLD_WIDTH - self.rect.width

    def _blocked_by_obstacle(self, start_pos, end_pos, obstacle_list, constraint_rect_group):
        if not obstacle_list and not constraint_rect_group:
            return False

        sx, sy = start_pos
        ex, ey = end_pos
        dist_to_end = math.hypot(ex - sx, ey - sy)

        def _normalise_clip(clip):
            if isinstance(clip[0], tuple):
                (ix1, iy1), (ix2, iy2) = clip
            else:
                ix1, iy1, ix2, iy2 = clip
            return ix1, iy1, ix2, iy2

        if obstacle_list:
            for tile in obstacle_list:
                clip = tile.collide_rect.clipline((sx, sy), (ex, ey))
                if clip:
                    ix1, iy1, ix2, iy2 = _normalise_clip(clip)
                    d1 = math.hypot(ix1 - sx, iy1 - sy)
                    d2 = math.hypot(ix2 - sx, iy2 - sy)
                    d = min(d1, d2)
                    if d < dist_to_end - 1e-6:
                        return True

        if constraint_rect_group:
            for constraint in constraint_rect_group:
                if constraint.colour != RED:
                    continue

                clip = constraint.rect.clipline((sx, sy), (ex, ey))
                if clip:
                    ix1, iy1, ix2, iy2 = _normalise_clip(clip)
                    d1 = math.hypot(ix1 - sx, iy1 - sy)
                    d2 = math.hypot(ix2 - sx, iy2 - sy)
                    d = min(d1, d2)
                    if d < dist_to_end - 1e-6:
                        return True

        return False
        
    def check_vision_cone(self, player, obstacle_list, constraint_rect_group):
        """
        Determine whether the player is within the enemy's vision cone.

        This updates `self.player_in_vision` and `self.attacking` state and returns
        one of: "attack" (player in close attack range and inside cone),
        "shoot" (player in long-range vision cone), or False if not visible.

        Args:
            player (Player): Player object whose position is tested.
            obstacle_list (Group): A list of obstacle rects for vision blocking checks.
            constraint_rect_group (Group): The constraint rects which are used to block enemy movement and vision.

        Returns:
            str|bool: "attack", "shoot", or False.
        """
        if not player or not player.alive:
            self.player_in_vision = False
            self.attacking = False
            return False

        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        distance = math.hypot(dx, dy)

        if distance > self.vision_range:
            self.player_in_vision = False
            self.attacking = False
            return False

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

        if not in_vision:
            self.attacking = False
            self.player_in_vision = False
            return False

        if obstacle_list or constraint_rect_group:
            start = (self.rect.centerx, self.rect.centery)
            end = (player.rect.centerx, player.rect.centery)
            if self._blocked_by_obstacle(start, end, obstacle_list, constraint_rect_group):
                self.player_in_vision = False
                self.attacking = False            
                return False

        if distance <= self.attack_range:
            self.attacking = True
            self.player_in_vision = True
            return "attack"
        else:
            self.attacking = False
            self.player_in_vision = True
            return "shoot"

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

        Dead > Hit > Recover > Attack > Jump > Fall > Run > Idle. When the player is dead, the enemy doesn't attack or recover.
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
        shot_fx.play()
        self.shoot_cooldown = 60
            
        if self.direction == "right":
            ammo_direction = pygame.math.Vector2(1, 0)
            ammo_ball = CannonBall(self.rect.right - self.img.get_width() // 2, self.rect.centery, ammo_sprites, ammo_direction)
        else:
            ammo_direction = pygame.math.Vector2(-1, 0)
            ammo_ball = CannonBall(self.rect.left, self.rect.centery, ammo_sprites, ammo_direction)
            
        ammo_ball.velocity = ammo_direction * ammo_ball.speed
        ammo_group.add(ammo_ball)

    def update(self, player, ammo_sprites, ammo_group, obstacle_list, constraint_rect_group):
        """
        Update enemy state for this frame, including vision checks, cooldowns, collisions,
        and smart-mode reactions to the player leaving the vision cone.

        Args:
            player (Player): The player object used for vision and collision checks.
            ammo_sprites (dict): Sprite frames for enemy ammo animations.
            ammo_group (Group): Group to add spawned CannonBall sprites.
            constraint_rect_group (Group): Group of constraint rects for collision checks.
        """
        self.check_alive()
        self.rect.topleft = (int(self.position.x), int(self.position.y))
        self.mask = pygame.mask.from_surface(self.img)

        # Capture previous vision state and update current vision once
        previous_vision = self.player_in_vision
        if player:
            vision_result = self.check_vision_cone(player, obstacle_list, constraint_rect_group)
        else:
            vision_result = False
        
        # Shooting logic
        if vision_result == "shoot" and self.hit_anim_timer == 0 and self.shoot_cooldown == 0 and random.randint(1, 2) == 1:
            self.shoot(ammo_sprites, ammo_group)

        def find_purple_rects():
            if not constraint_rect_group:
                return []

            purple_rects = []
            for constraint in constraint_rect_group:
                if constraint.colour != PURPLE:
                    continue

                if abs(constraint.rect.centery - self.rect.centery) < 50:
                    purple_rects.append(constraint)

            return purple_rects

        if constraint_rect_group and self.alive:
            for constraint in constraint_rect_group:
                if constraint.colour != PURPLE:
                    continue

                if not self.rect.colliderect(constraint.rect):
                    continue

                if self.speed == 2:
                    if random.randint(1, 10) == 1:
                        if self.on_ground and self.jump_count < 1:
                            self.jump()
                            break

                elif self.speed == 3:
                    if player:
                        dx = player.rect.centerx - self.rect.centerx
                        player_is_behind = (self.direction == "right" and dx <= -10) or (self.direction == "left" and dx >= 10)
                    else:
                        player_is_behind = False

                    if not player_is_behind and (not player or player.rect.y < self.rect.y):
                        if self.on_ground and self.jump_count < 1 and self.smartmode:
                            self.jump()
                            break

        if self.smartmode and player:
            if previous_vision and not self.player_in_vision:
                self.recently_lost_vision_timer = 30

                purple_rects = find_purple_rects()

                if self.on_ground and player.rect.y > self.rect.y:
                    self.last_chase_direction = self.direction
                    self.continue_chase_timer = self.continue_chase_duration
                    self.suppress_random_turns_timer = max(self.suppress_random_turns_timer, self.continue_chase_duration)
                else:
                    if self.turn_cooldown == 0:
                        self.recheck_turn_timer = self.RECHECK_TURN_DURATION

                        dx = player.rect.centerx - self.rect.centerx
                        player_is_behind = (self.direction == "right" and dx <= -10) or (self.direction == "left" and dx >= 10)
                        if not player_is_behind:
                            self.suppress_random_turns_timer = max(self.suppress_random_turns_timer, self.SUPPRESS_TURN_DURATION)

            elif self.recently_lost_vision_timer > 0:
                self.recently_lost_vision_timer -= 1

                purple_rects = find_purple_rects()
                if self.on_ground and player.on_ground and player.rect.y < self.rect.y and purple_rects:
                    if self.direction == "right":
                        far_purple = max(purple_rects, key=lambda r: r.rect.right)
                        self.last_chase_direction = "right"
                        self.pursuing_purple_rect = far_purple
                    else:
                        far_purple = min(purple_rects, key=lambda r: r.rect.left)
                        self.last_chase_direction = "left"
                        self.pursuing_purple_rect = far_purple

                    self.continue_chase_timer = self.continue_chase_duration
                    self.suppress_random_turns_timer = max(self.suppress_random_turns_timer, self.continue_chase_duration)

            if self.continue_chase_timer > 0:
                self.continue_chase_timer -= 1

                if self.on_ground and player.rect.y > self.rect.y and self.last_chase_direction:
                    self.direction = self.last_chase_direction
                    self.speed = 3
                    self.state = "running"
                    self.state_timer = 0
                    self.moving_left = (self.direction == "left")
                    self.moving_right = (self.direction == "right")
                elif self.pursuing_purple_rect and self.last_chase_direction:
                    purple_rect = self.pursuing_purple_rect

                    if self.last_chase_direction == "right":
                        if self.rect.left >= purple_rect.rect.right:  
                            self.direction = "left"
                            if self.on_ground and self.jump_count < 1:
                                self.jump()
                            self.continue_chase_timer = 0
                            self.pursuing_purple_rect = None
                            self.last_chase_direction = None
                            self.turn_cooldown = self.TURN_COOLDOWN
                        else:
                            self.direction = "right"
                            self.speed = 3
                            self.state = "running"
                            self.state_timer = 0
                            self.moving_left = False
                            self.moving_right = True
                    else:
                        if self.rect.right <= purple_rect.rect.left:
                            self.direction = "right"
                            if self.on_ground and self.jump_count < 1:
                                self.jump()
                            self.continue_chase_timer = 0
                            self.pursuing_purple_rect = None
                            self.last_chase_direction = None
                            self.turn_cooldown = self.TURN_COOLDOWN
                        else:
                            self.direction = "left"
                            self.speed = 3
                            self.state = "running"
                            self.state_timer = 0
                            self.moving_left = True
                            self.moving_right = False
                else:
                    if self.rect.y == player.rect.y and self.last_chase_direction and not self.pursuing_purple_rect:
                        self.direction = "left" if self.last_chase_direction == "right" else "right"
                        self.last_chase_direction = None
                        self.continue_chase_timer = 0
                        self.turn_cooldown = self.TURN_COOLDOWN
                    elif self.continue_chase_timer == 0:
                        self.last_chase_direction = None
                        self.pursuing_purple_rect = None

            if self.turn_cooldown > 0:
                self.turn_cooldown -= 1

            if self.suppress_random_turns_timer > 0:
                self.suppress_random_turns_timer -= 1

            if self.recheck_turn_timer > 0:
                if self.hit_anim_timer == 0:
                    self.recheck_turn_timer -= 1

                    if self.recheck_turn_timer == 0 and not self.player_in_vision and self.turn_cooldown == 0:
                        if self.continue_chase_timer == 0:
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

        if self.continue_chase_timer == 0:
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

        if player and self.attacking and self.attack_cooldown == 0 and self.hit_anim_timer == 0 and self.y_vel < 1:
            dx = player.rect.centerx - self.rect.centerx
            dy = player.rect.centery - self.rect.centery
            distance = math.hypot(dx, dy)
            height_difference = abs(player.rect.centery - self.rect.centery)

            if distance <= self.attack_range // 2 and height_difference < 10:
                if player.alive:
                    player.get_hit(30, attacker=self)
                self.post_attack_recovery = True
                self.attack_recovery_timer = 0
                self.attack_cooldown = 60

        if player and self.collide(player):   
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

    def draw_vision_cone(self, win, player, obstacle_list=None, constraint_rect_group=None):
        """
        Draw a debug visualisation of the enemy's vision cone and a line to the player when in vision.

        Behaviour:
          - Rays are clipped to the nearest obstacle intersection.
          - RED constraint rects immediately block vision: as soon as a ray touches a RED
            constraint rect it stops there (no sliding along edges).
          - For non-RED obstacle hits, rays slide along the top edge of obstacles/ground
            until vision range. Sliding is clamped by RED constraint rects so a ray
            cannot slide past a RED constraint.
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

        def _normalise_clip(clip):
            if isinstance(clip[0], tuple):
                (ix1, iy1), (ix2, iy2) = clip
            else:
                ix1, iy1, ix2, iy2 = clip
            return ix1, iy1, ix2, iy2

        def clip_ray(sx, sy, ex, ey):
            """
            Return (px, py, blocker_type) where blocker_type is:
              - 'constraint' if the nearest intersection is a RED constraint rect
              - 'obstacle' if the nearest intersection is a normal obstacle tile
              - None if no intersection
            """
            nearest = None
            nearest_dist = None
            nearest_type = None

            # check RED constraint rects first (they take absolute precedence)
            if constraint_rect_group:
                for constraint in constraint_rect_group:
                    if getattr(constraint, "colour", None) != RED:
                        continue
                    clip = constraint.rect.clipline((sx, sy), (ex, ey))
                    if not clip:
                        continue
                    ix1, iy1, ix2, iy2 = _normalise_clip(clip)
                    d1 = math.hypot(ix1 - sx, iy1 - sy)
                    d2 = math.hypot(ix2 - sx, iy2 - sy)
                    if d1 <= d2:
                        d = d1
                        px, py = ix1, iy1
                    else:
                        d = d2
                        px, py = ix2, iy2

                    if nearest is None or d < nearest_dist:
                        nearest = (px, py)
                        nearest_dist = d
                        nearest_type = 'constraint'

            # check obstacle tiles (only if no constraint was found or constraint is further)
            if obstacle_list:
                for tile in obstacle_list:
                    clip = tile.collide_rect.clipline((sx, sy), (ex, ey))
                    if not clip:
                        continue
                    ix1, iy1, ix2, iy2 = _normalise_clip(clip)
                    d1 = math.hypot(ix1 - sx, iy1 - sy)
                    d2 = math.hypot(ix2 - sx, iy2 - sy)
                    if d1 <= d2:
                        d = d1
                        px, py = ix1, iy1
                    else:
                        d = d2
                        px, py = ix2, iy2

                    # only use obstacle if no constraint found, or if obstacle is closer
                    if nearest_type != 'constraint' and (nearest is None or d < nearest_dist):
                        nearest = (px, py)
                        nearest_dist = d
                        nearest_type = 'obstacle'

            if nearest is not None:
                return nearest[0], nearest[1], nearest_type
            return ex, ey, None

        def find_edge_segment(hit_x, hit_y, edge):
            """
            edge: 'top' or 'bottom'
            Return merged interval (left, right, edge_y) covering contiguous tiles that share the same edge.
            """
            if not obstacle_list:
                return None

            tol = 6
            candidates = []
            for tile in obstacle_list:
                r = tile.collide_rect
                if r.collidepoint(hit_x, hit_y):
                    candidates.append(r)
                else:
                    edge_y = r.top if edge == "top" else r.bottom
                    if abs(hit_y - edge_y) <= tol and (r.left - 1) <= hit_x <= (r.right + 1):
                        candidates.append(r)

            if not candidates:
                return None

            edge_y = candidates[0].top if edge == "top" else candidates[0].bottom

            same_edge = []
            for tile in obstacle_list:
                r = tile.collide_rect
                r_edge = r.top if edge == "top" else r.bottom
                if abs(r_edge - edge_y) <= 2:
                    same_edge.append(r)

            if not same_edge:
                return None

            intervals = sorted([(r.left, r.right) for r in same_edge], key=lambda t: t[0])
            merged = []
            for a, b in intervals:
                if not merged or a > merged[-1][1] + 2:
                    merged.append([a, b])
                else:
                    merged[-1][1] = max(merged[-1][1], b)

            for a, b in merged:
                if a - 2 <= hit_x <= b + 2:
                    return (a, b, edge_y)

            best = None
            best_dist = float('inf')
            for a, b in merged:
                dist = min(abs(hit_x - a), abs(hit_x - b))
                if dist < best_dist:
                    best_dist = dist
                    best = (a, b, edge_y)
            return best

        def clamp_to_vision(px, py):
            dx = px - center_x
            dy = py - center_y
            d = math.hypot(dx, dy)
            if d <= self.vision_range or d == 0:
                return px, py
            scale = self.vision_range / d
            return center_x + dx * scale, center_y + dy * scale

        # clip rays and know whether hit was a constraint
        left_px, left_py, left_type = clip_ray(center_x, center_y, left_x, left_y)
        right_px, right_py, right_type = clip_ray(center_x, center_y, right_x, right_y)

        def slide_or_stop(px, py, hit_type):
            # immediate stop on RED constraint
            if hit_type == 'constraint':
                return px, py

            # For non-constraint hits, always slide along the top edge of obstacles/ground
            # This works for both upward and downward rays - we slide along walkable surfaces
            seg = find_edge_segment(px, py, "top")
            if not seg:
                return px, py
            a, b, edge_y = seg
            # Determine slide direction based on ray direction
            end_x = b if px >= center_x else a
            end_y = edge_y

            # clamp sliding endpoint so it does not pass any RED constraint that lies between
            # center_x and end_x at approximately the same vertical (edge_y).
            if constraint_rect_group:
                if end_x > center_x:
                    # sliding right -> clamp to nearest RED constraint.left that lies between center_x and end_x
                    for c in constraint_rect_group:
                        if getattr(c, "colour", None) != RED:
                            continue
                        r = c.rect
                        # check vertical overlap with edge_y (small tolerance)
                        if r.top - 2 <= end_y <= r.bottom + 2:
                            if r.left >= center_x and r.left <= end_x:
                                end_x = min(end_x, r.left)
                else:
                    # sliding left -> clamp to nearest RED constraint.right between end_x and center_x
                    for c in constraint_rect_group:
                        if getattr(c, "colour", None) != RED:
                            continue
                        r = c.rect
                        if r.top - 2 <= end_y <= r.bottom + 2:
                            if r.right <= center_x and r.right >= end_x:
                                end_x = max(end_x, r.right)

            end_x, end_y = clamp_to_vision(end_x, end_y)
            return end_x, end_y

        left_x, left_y = slide_or_stop(left_px, left_py, left_type)
        right_x, right_y = slide_or_stop(right_px, right_py, right_type)

        # safety flattening to floor
        floor_y = self.rect.bottom
        def flatten_to_floor(px, py):
            if py <= floor_y:
                return px, py
            direction_sign = 1 if px >= center_x else -1
            return center_x + direction_sign * self.vision_range, floor_y

        left_x, left_y = flatten_to_floor(left_x, left_y)
        right_x, right_y = flatten_to_floor(right_x, right_y)

        # draw the two edge rays and small hit markers
        pygame.draw.line(win, (255, 0, 0), (center_x, center_y), (int(left_x), int(left_y)), 2)
        pygame.draw.line(win, (255, 0, 0), (center_x, center_y), (int(right_x), int(right_y)), 2)

        pygame.draw.circle(win, (255, 0, 0), (int(left_x), int(left_y)), 3)
        pygame.draw.circle(win, (255, 0, 0), (int(right_x), int(right_y)), 3)

        # draw player line (green) stopping at nearest obstacle or RED constraint
        if self.player_in_vision:
            px, py = player.rect.centerx, player.rect.centery
            if self._blocked_by_obstacle((center_x, center_y), (px, py), obstacle_list, constraint_rect_group):
                nearest = None
                nearest_dist = None
                # check obstacles
                if obstacle_list:
                    for tile in obstacle_list:
                        clip = tile.collide_rect.clipline((center_x, center_y), (px, py))
                        if not clip:
                            continue
                        ix1, iy1, ix2, iy2 = _normalise_clip(clip)
                        d1 = math.hypot(ix1 - center_x, iy1 - center_y)
                        d2 = math.hypot(ix2 - center_x, iy2 - center_y)
                        if d1 <= d2:
                            d = d1
                            pt = (ix1, iy1)
                        else:
                            d = d2
                            pt = (ix2, iy2)
                        if nearest is None or d < nearest_dist:
                            nearest = pt
                            nearest_dist = d
                # check RED constraints (they should take precedence if nearer)
                if constraint_rect_group:
                    for constraint in constraint_rect_group:
                        if getattr(constraint, "colour", None) != RED:
                            continue
                        clip = constraint.rect.clipline((center_x, center_y), (px, py))
                        if not clip:
                            continue
                        ix1, iy1, ix2, iy2 = _normalise_clip(clip)
                        d1 = math.hypot(ix1 - center_x, iy1 - center_y)
                        d2 = math.hypot(ix2 - center_x, iy2 - center_y)
                        if d1 <= d2:
                            d = d1
                            pt = (ix1, iy1)
                        else:
                            d = d2
                            pt = (ix2, iy2)
                        if nearest is None or d < nearest_dist:
                            nearest = pt
                            nearest_dist = d

                if nearest:
                    pygame.draw.line(win, (0, 255, 0), (center_x, center_y), nearest, 2)
            else:
                pygame.draw.line(win, (0, 255, 0), (center_x, center_y), (px, py), 2)
