import pygame
from constants import WIDTH, FPS, TILE_SIZE
import math
from random import randint


class GrenadeBox(pygame.sprite.Sprite):
    """
    A box that contains grenades for the player to collect.

    Attributes:
        img (Surface): Pygame Surface used to draw the grenade box.
        position (Vector2): Current position of the grenade box.
        rect (Rect): Rectangular area representing the grenade box's position and size.
        mask (Mask): Pixel-perfect collision mask for the grenade box.
    """

    def __init__(self, x, y, img):
        """
        Initialise a GrenadeBox.
        Args:
            x (float): X-coordinate of the grenade box's position.
            y (float): Y-coordinate of the grenade box's position.
            img (Surface): Pygame Surface used to draw the grenade box.
        """
        super().__init__()

        self.img = img
        self.position = pygame.math.Vector2(x, y)
        self.rect = self.img.get_rect(topleft=(int(self.position.x), int(self.position.y)))
        self.mask = pygame.mask.from_surface(self.img)

    def draw(self, win):
        """
        Draw the grenade box on the provided surface.
        """
        win.blit(self.img, self.rect)

    def collide(self, obj):
        """
        Check collision between this gem and another sprite using masks.

        Args:
            obj (Sprite): Other sprite to test collision against.

        Returns:
            bool: True if masks overlap, False otherwise.
        """

        if self.rect.colliderect(obj.rect):
            offset_x = obj.rect.x - self.rect.x
            offset_y = obj.rect.y - self.rect.y
            return self.mask.overlap(obj.mask, (offset_x, offset_y)) is not None
        else:
            return False

    def update(self, player):
        """
        Update grenade box position/mask and remove it if the player collects it.

        Args:
            player (Player): Player object used to detect collection.
        """

        self.rect.topleft = (int(self.position.x), int(self.position.y))
        self.mask = pygame.mask.from_surface(self.img)

        if self.collide(player):
            if player.alive:
                self.kill()
                player.grenades += 5
                player.draw_num_grenades_timer = player.NUM_GRENADES_DURATION


class CollectibleGem(pygame.sprite.Sprite):

    ANIMATION_DELAY = 5

    def __init__(self, x, y, sprites, gem_type):
        """
        Initialise a collectible Gem.

        Args:
            x (float): X-coordinate of the gem's position.
            y (float): Y-coordinate of the gem's position.
            img (Surface): Pygame Surface used to draw the gem.
        """
        super().__init__()

        self.sprites = sprites
        self.gem_type = gem_type
        self.img = self.sprites[gem_type][0]
        self.position = pygame.math.Vector2(x, y)
        self.rect = self.img.get_rect(topleft=(int(self.position.x), int(self.position.y)))
        self.mask = pygame.mask.from_surface(self.img)
        self.animation_count = 0

    def collide(self, obj):
        """
        Check collision between this gem and another sprite using masks.

        Args:
            obj (Sprite): Other sprite to test collision against.

        Returns:
            bool: True if masks overlap, False otherwise.
        """

        if self.rect.colliderect(obj.rect):
            offset_x = obj.rect.x - self.rect.x
            offset_y = obj.rect.y - self.rect.y
            return self.mask.overlap(obj.mask, (offset_x, offset_y)) is not None
        else:
            return False

    def draw(self, win):
        """
        Draw the gem on the provided surface.
        """
        win.blit(self.img, self.rect)

    def update_sprite(self):
        """
        Update gem sprite animation frame.
        """
        sprite_sheet_name = self.gem_type
        
        if sprite_sheet_name in self.sprites:
            sprites = self.sprites[sprite_sheet_name]
            sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
            self.img = sprites[sprite_index]

        self.animation_count += 1

    def update(self, player):
        """
        Update gem position/mask and remove it if the player collects it.

        Args:
            player (Player): Player object used to detect collection.
        """
        self.rect.topleft = (int(self.position.x), int(self.position.y))
        self.mask = pygame.mask.from_surface(self.img)

        if self.collide(player):
            if player.alive:
                self.kill()

                if self.gem_type == "player_ammo":
                    player.ammo += randint(20, 40)
                    player.draw_num_ammo_timer = player.NUM_AMMO_DURATION
                elif self.gem_type == "player_health":
                    player.health += randint(50, 150)
                    if player.health > player.max_health:
                        player.health = player.max_health

                    player.health_bar_timer = player.HEALTH_BAR_DURATION


# Purple Gem class (moves horizontally across the screen as player ammo)
class PurpleGem(CollectibleGem):

    def __init__(self, x, y, sprites, gem_type, direction):
        """
        Initialise a PurpleGem which acts as player's projectile.

        Args:
            x (float): Initial x position.
            y (float): Initial y position.
            img (Surface): Sprite image for the projectile.
            direction (Vector2): Direction vector the projectile will travel.
        """
        super().__init__(x, y, sprites, gem_type)

        base_img = self.sprites[self.gem_type][0]
        self.img = pygame.transform.scale(base_img, (TILE_SIZE // 4, TILE_SIZE // 4))
        self.speed = 10
        self.direction = direction
        self.velocity = pygame.math.Vector2(0, 0)

    def update(self, enemies_group):
        """
        Move the projectile and check collision with enemies or screen bounds.

        Args:
            enemies_group (Group): Pygame Group of enemies to test collisions with.
        """
        self.position += self.velocity
        self.rect.topleft = (int(self.position.x), int(self.position.y))
        self.mask = pygame.mask.from_surface(self.img)
        
        if self.rect.right < 0 or self.rect.left > WIDTH:
            self.kill()

        for enemy in enemies_group:
            if self.collide(enemy):
                if enemy.alive:
                    enemy.get_hit(20, attacker=self)
                    self.kill()


class Pearl(pygame.sprite.Sprite):
    """
    Pearl projectile used by Seashell enemies.

    Attributes:
        ANIMATION_DELAY (int): Delay in frames between sprite animations.

        sprites (dict): Sprite frames for pearl animations.
        img (Surface): Current image/sprite of the pearl.
        position (Vector2): Current position of the pearl.
        velocity (Vector2): Current velocity of the pearl.
        direction (Vector2): Direction vector for movement.
        rect (Rect): Rectangular area representing the pearl's position and size.
        mask (Mask): Pixel-perfect collision mask for the pearl.
        animation_count (int): Counter for animation frame updates.
        speed (float): Movement speed of the pearl.
        state (str): Current state of the pearl ("flying").
    """

    ANIMATION_DELAY = 3

    def __init__(self, x, y, sprites, direction):
        """
        Initialise a Pearl used by Seashell enemies as ammo.
        Args:
            x (float): X-coordinate of the pearl's position.
            y (float): Y-coordinate of the pearl's position.
            sprites (dict): Sprite frames for cannon ball animations.
            direction (Vector2): Direction vector for movement.
        """
        super().__init__()

        self.sprites = sprites
        self.img = self.sprites["Pearl Idle"][0]
        self.position = pygame.math.Vector2(x, y)
        self.velocity = pygame.math.Vector2(0, 0)
        self.direction = direction
        self.rect = self.img.get_rect(topleft=(int(self.position.x), int(self.position.y)))
        self.mask = pygame.mask.from_surface(self.img)
        self.animation_count = 0
        self.speed = 5
        self.state = "flying"

    def collide(self, obj):
        """
        Check pixel-perfect collision between this pearl and another sprite using masks.
        Args:
            obj (Sprite): Other sprite to test collision against.

        Returns:
            bool: True if collision occurred, False otherwise.
        """

        if self.rect.colliderect(obj.rect):
            offset_x = obj.rect.x - self.rect.x
            offset_y = obj.rect.y - self.rect.y
            return self.mask.overlap(obj.mask, (offset_x, offset_y)) is not None
        else:
            return False

    def draw(self, win):
        """
        Draw the pearl on the given surface.
        """
        win.blit(self.img, self.rect)

    def start_explosion(self, player):
        """
        Transition the pearl to exploding state and reset animation counter.
        """
        self.state = "exploding"
        self.animation_count = 0

        self.velocity = pygame.math.Vector2(0, 0)

        explosion = self.sprites.get("Pearl Explosion")
        if explosion:
            self.img = explosion[0]

            self.rect = self.img.get_rect(center=player.rect.center)
            self.position = pygame.math.Vector2(self.rect.topleft)

    def update_sprite(self):
        """
        Advance the pearl animation frame.
        """
        if self.state == "flying":
            sprite_sheet_name = "Pearl Idle"
        else:
            sprite_sheet_name = "Pearl Explosion"

        sprites = self.sprites.get(sprite_sheet_name, [])
        if not sprites:
            return

        frame_index = self.animation_count // self.ANIMATION_DELAY

        if self.state == "exploding" and frame_index >= len(sprites):
            self.kill()
            return

        frame_index = min(frame_index, len(sprites) - 1)
        self.img = sprites[frame_index]
        self.animation_count += 1

    def update(self, player):
        """
        Move the pearl and check collisions with the player and screen bounds.

        Args:
            player (Player): Player object to test collision against.
        """
        if self.state == "flying":
            self.position += self.velocity
            self.rect.topleft = (int(self.position.x), int(self.position.y))
            self.mask = pygame.mask.from_surface(self.img)

            if self.rect.right < 0 or self.rect.left > WIDTH:
                self.kill()
                return

            if self.collide(player):
                if player.alive:
                    player.get_hit(10, attacker=self)
                self.start_explosion(player)
        else:
            pass


class CannonBall(pygame.sprite.Sprite):
    """
    CannonBall projectile used by FierceTooth enemies.

    Attributes:
        ANIMATION_DELAY (int): Delay in frames between sprite animations.

        sprites (dict): Sprite frames for cannon ball animations.
        img (Surface): Current image/sprite of the cannon ball.
        position (Vector2): Current position of the cannon ball.
        velocity (Vector2): Current velocity of the cannon ball.
        direction (Vector2): Direction vector for movement.
        rect (Rect): Rectangular area representing the cannon ball's position and size.
        mask (Mask): Pixel-perfect collision mask for the cannon ball.
        animation_count (int): Counter for animation frame updates.
        speed (float): Movement speed of the cannon ball.
        state (str): Current state of the cannon ball ("flying" or "exploding").
    """

    ANIMATION_DELAY = 3

    def __init__(self, x, y, sprites, direction):
        """
        Initialise a CannonBall used by Fierecetooth enemies as ammo.

        Args:
            x (float): Initial x position.
            y (float): Initial y position.
            sprites (dict): Sprite frames for cannon ball animations.
            direction (Vector2): Direction vector for movement.
        """
        super().__init__()

        self.sprites = sprites
        self.img = self.sprites["Cannon Ball Flying"][0]
        self.position = pygame.math.Vector2(x, y)
        self.velocity = pygame.math.Vector2(0, 0)
        self.direction = direction
        self.rect = self.img.get_rect(topleft=(int(self.position.x), int(self.position.y)))
        self.mask = pygame.mask.from_surface(self.img)
        self.animation_count = 0
        self.speed = 12
        self.state = "flying"

    def collide(self, obj):
        """
        Check pixel-perfect collision with another sprite using masks.

        Args:
            obj (Sprite): The other sprite to test collision against.

        Returns:
            bool: True if collision occurred, False otherwise.
        """
        if self.rect.colliderect(obj.rect):
            offset_x = obj.rect.x - self.rect.x
            offset_y = obj.rect.y - self.rect.y
            return self.mask.overlap(obj.mask, (offset_x, offset_y)) is not None
        else:
            return False

    def draw(self, win):
        """
        Draw the cannon ball on the given surface.
        """
        win.blit(self.img, self.rect)

    def start_explosion(self, player):
        """
        Transition the cannon ball to exploding state and reset animation counter.
        """
        self.state = "exploding"
        self.animation_count = 0

        self.velocity = pygame.math.Vector2(0, 0)

        explosion = self.sprites.get("Cannon Ball Explosion")
        if explosion:
            self.img = explosion[0]

            self.rect = self.img.get_rect(center=player.rect.center)
            self.position = pygame.math.Vector2(self.rect.topleft)

    def update_sprite(self):
        """
        Advance the cannon ball animation frame.
        """
        if self.state == "flying":
            sprite_sheet_name = "Cannon Ball Flying"
        else:
            sprite_sheet_name = "Cannon Ball Explosion"

        sprites = self.sprites.get(sprite_sheet_name, [])
        if not sprites:
            return

        frame_index = self.animation_count // self.ANIMATION_DELAY

        if self.state == "exploding" and frame_index >= len(sprites):
            self.kill()
            return

        frame_index = min(frame_index, len(sprites) - 1)
        self.img = sprites[frame_index]
        self.animation_count += 1
        
    def update(self, player):
        """
        Move the cannon ball and check collisions with the player and screen bounds.

        Args:
            player (Player): Player object to test collision against.
        """
        if self.state == "flying":
            self.position += self.velocity
            self.rect.topleft = (int(self.position.x), int(self.position.y))
            self.mask = pygame.mask.from_surface(self.img)

            if self.rect.right < 0 or self.rect.left > WIDTH:
                self.kill()
                return

            if self.collide(player):
                if player.alive:
                    player.get_hit(10, attacker=self)

                self.start_explosion(player)
        else:
            pass


class Grenade(pygame.sprite.Sprite):
    """
    Thrown grenade with arc, horizontal drag, timed explosion and blast animation.

    Behaviour:
    - On creation the grenade receives an initial horizontal velocity from `direction.x * THROW_SPEED`
      and an initial upward velocity (`THROW_VY`). Gravity integrates the vertical motion.
    - Horizontal velocity is multiplied by `X_DRAG` each frame until it falls below STOP_THRESHOLD.
    - After `timer` frames the grenade transitions to `blast` state:
        - Explosion sprite is anchored so its bottom matches the grenade bottom.
        - Explosion animation plays; when frames finish it holds the last frame for BLAST_DURATION frames.
        - Blast damage (pixel-perfect) is applied once at the start of the blast (uses mask overlap).
        - After BLAST_DURATION expires the sprite is removed via `kill()`.

    Attributes:
        GRAVITY (float): Gravity strength affecting the grenade falling.
        BOUNCE_DAMPING_Y (float): Damping factor for vertical bounce.
        MIN_BOUNCE_VY (float): Minimum vertical velocity to trigger a bounce.
        AIR_DRAG (float): Horizontal drag factor while airborne.
        ROLL_DECEL (float): Horizontal deceleration factor when rolling on ground.
        ROLL_STOP_THRESHOLD (float): Minimum horizontal velocity to stop rolling.
        THROW_SPEED (float): Initial horizontal speed multiplier when thrown.
        THROW_VY (float): Initial upward velocity when thrown.
        ANIMATION_DELAY (int): Delay in frames between sprite animations.
        SPIN_FACTOR (float): Factor for rotation speed based on horizontal velocity.
        BLAST_DURATION (int): Duration in frames for which the blast remains visible.

        sprites (dict): Sprite frames for grenade and explosion animations.
        base_img (Surface): Current image/sprite of the grenade.
        img (Surface): For rotating the base image.
        position (Vector2): Current position of the grenade.
        velocity (Vector2): Current velocity of the grenade.
        direction (Vector2): Direction vector for initial throw.
        rect (Rect): Rectangular area representing the grenade's position and size.
        mask (Mask): Pixel-perfect collision mask for the grenade.
        animation_count (int): Counter for animation frame updates.
        state (str): Current state of the grenade ("thrown" or "blast").
        timer (int): Countdown timer until explosion.
        blast_timer (int): Countdown timer for visible blast duration.
        _blast_applied (bool): Internal flag to ensure blast damage is applied only once.
        is_grenade (bool): Proving that this object is a Grenade.
    """

    GRAVITY = 0.7
    GROUND_Y = 400
    BOUNCE_DAMPING_Y = 0.35
    MIN_BOUNCE_VY = 1.2
    AIR_DRAG = 0.995
    ROLL_DECEL = 1.95
    ROLL_STOP_THRESHOLD = 0.6
    THROW_SPEED = 8
    THROW_VY = -12
    ANIMATION_DELAY = 3
    SPIN_FACTOR = 0.7
    BLAST_DURATION = 0.3 * FPS

    def __init__(self, x, y, sprites, direction):
        """
        Initialise a Grenade Object.

        Args:
            x: (float): Initial x position.
            y: (float): Initial y position.
            sprites (dict): Sprite frames for grenade and explosion animations.
            direction (Vector2): Direction vector for initial throw.
        """
        super().__init__()

        self.sprites = sprites
        self.base_img = self.sprites["Grenade Idle"][0]
        self.img = self.base_img
        self.rotation_angle = 0
        self.position = pygame.math.Vector2(x, y)
        self.direction = direction
        self.velocity = pygame.math.Vector2(self.direction.x * self.THROW_SPEED, self.THROW_VY)
        self.rect = self.img.get_rect(topleft=(int(self.position.x), int(self.position.y)))
        self.mask = pygame.mask.from_surface(self.img)
        self.animation_count = 0
        self.state = "thrown"   
        self.timer = 100    
        self.blast_timer = 0   
        self._blast_applied = False

        self.is_grenade = True

    def draw(self, win):
        win.blit(self.img, self.rect)

    def collide(self, obj):
        if self.rect.colliderect(obj.rect):
            offset_x = obj.rect.x - self.rect.x
            offset_y = obj.rect.y - self.rect.y
            return self.mask.overlap(obj.mask, (offset_x, offset_y)) is not None
        return False

    def start_explosion(self):
        """
        Switch to blast state, anchor explosion bottom to grenade bottom, update mask and set blast timer.
        """
        midbottom = self.rect.midbottom

        self.state = "blast"
        self.animation_count = 0
        self.velocity = pygame.math.Vector2(0, 0)
        self._blast_applied = False

        explosion_frames = self.sprites.get("Explosion", None)
        if explosion_frames:
            self.img = explosion_frames[0]
            self.rect = self.img.get_rect(midbottom=midbottom)
            self.position = pygame.math.Vector2(self.rect.topleft)
            self.mask = pygame.mask.from_surface(self.img)

        self.blast_timer = int(self.BLAST_DURATION)

    def update_sprite(self):
        """Advance animation; for blast state play frames then hold last frame while blast_timer counts down."""
        if self.state == "thrown":
            sheet = "Grenade Idle"
        else:
            sheet = "Explosion"

        sprites = self.sprites.get(sheet, [])
        if not sprites:
            return

        frame_index = self.animation_count // self.ANIMATION_DELAY

        midbottom = self.rect.midbottom

        if self.state == "blast":
            if frame_index < len(sprites):
                self.img = sprites[frame_index]
            else:
                self.img = sprites[-1]
        else:
            frame_index = min(frame_index, len(sprites) - 1)
            base_frame = sprites[frame_index]
            self.img = pygame.transform.rotate(base_frame, self.rotation_angle)

        self.rect = self.img.get_rect(midbottom=midbottom)
        self.position = pygame.math.Vector2(self.rect.topleft)
        self.mask = pygame.mask.from_surface(self.img)

        self.animation_count += 1

    def update(self, player, enemies_group):
        """
        Update grenade every frame.
        - While thrown: integrate physics and count down timer.
        - When timer hits 0: call start_explosion() and apply blast damage once.
        - While in blast: apply damage once and count down blast_timer, then kill().
        """

        if self.state == "thrown":
            self.timer -= 1
            if self.timer <= 0:
                self.start_explosion()
                return

            self.rotation_angle -= self.velocity.x * self.SPIN_FACTOR
            self.rotation_angle %= 360

            airborne = (self.position.y + self.rect.height) < self.GROUND_Y

            if airborne:
                self.velocity.y += self.GRAVITY
                self.velocity.x *= self.AIR_DRAG

            self.position += self.velocity

            if self.position.y + self.rect.height >= self.GROUND_Y:
                self.position.y = self.GROUND_Y - self.rect.height

                if abs(self.velocity.y) > self.MIN_BOUNCE_VY:
                    self.velocity.y = -self.velocity.y * self.BOUNCE_DAMPING_Y
                else:
                    self.velocity.y = 0

                if self.velocity.x > 0:
                    self.velocity.x -= self.ROLL_DECEL
                    if self.velocity.x < self.ROLL_STOP_THRESHOLD:
                        self.velocity.x = 0
                elif self.velocity.x < 0:
                    self.velocity.x += self.ROLL_DECEL
                    if self.velocity.x > -self.ROLL_STOP_THRESHOLD:
                        self.velocity.x = 0

            self.rect.topleft = (round(self.position.x), round(self.position.y))
            self.mask = pygame.mask.from_surface(self.img)

        elif self.state == "blast":
            if not self._blast_applied:
                max_damage_distance = math.hypot(self.rect.width // 2, self.rect.height // 2) + 10

                for enemy in enemies_group:
                    if not enemy.alive:
                        continue

                    dx = enemy.rect.centerx - self.rect.centerx
                    dy = enemy.rect.centery - self.rect.centery
                    distance = math.hypot(dx, dy)

                    if distance <= max_damage_distance:
                        if distance <= (0.5 * max_damage_distance):
                            enemy.get_hit(120, attacker=self)
                        elif distance <= (0.75 * max_damage_distance):
                            enemy.get_hit(90, attacker=self)
                        else:
                            enemy.get_hit(60, attacker=self)

                if player.alive:
                    player_dx = player.rect.centerx - self.rect.centerx
                    player_dy = player.rect.centery - self.rect.centery
                    distance = math.hypot(player_dx, player_dy)

                    if distance <= max_damage_distance:
                        if distance <= (0.5 * max_damage_distance):
                            player.get_hit(200, attacker=self)
                        elif distance <= (0.75 * max_damage_distance):
                            player.get_hit(150, attacker=self)
                        else:
                            player.get_hit(100, attacker=self)

                self._blast_applied = True

            if self.blast_timer > 0:
                self.blast_timer -= 1
            else:
                self.kill()
