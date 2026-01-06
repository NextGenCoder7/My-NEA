import pygame
from enemies import Enemy
import math
import heapq
import random
from constants import RED, PURPLE, TILE_SIZE


class Node:
    """
    Node for A* pathfinding. The purple rects serve as the nodes. Each node has a position, parent node, and g, h, f costs.

    Attributes:
        position (tuple): The (x, y) position of the node.
        parent (Node): The parent node in the path.
        g (int): Cost from start to current node.
        h (int): Heuristic cost from current node to goal.
        f (int): Total cost (g + h).
    """

    def __init__(self, position, parent=None):
        self.position = position  
        self.parent = parent
        self.g = 0  
        self.h = 0  
        self.f = 0     

    def __lt__(self, other):    
        """
        Less-than comparison for priority queue based on f cost.

        Args:
            other (Node): Another node to compare with.

        Returns:
            bool: True if this node's f cost is less than the other node's f cost.
        """

        return self.f < other.f


class PinkStar(Enemy):
    """
    A PinkStar enemy that chases the player and attacks when the player is in its lair (danger zone),
    using the A* algorithm to relentlessly chase the player.

    If it successfully attacks the player, it goes into a recovery state before chasing again.
    The algorithm uses purple constraint rectangles as nodes for pathfinding, and resets every second.

    Attributes:
        HIT_ANIM_DURATION (int): Duration of hit animation in frames.

        death_fall_speed_cap (int): Maximum fall speed when dead.
        death_handled (bool): Whether death handling has been completed.

        chasing_player (bool): Whether the enemy is currently chasing the player.
        path (list): List of (x, y) positions representing the current path to the player.
        current_path_index (int): Current index in the path list.
        path_update_timer (int): Timer for updating the path.
        path_update_interval (int): Interval for updating the path.

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

        self.death_fall_speed_cap = 10
        self.death_handled = False

        self.chasing_player = False
        self.path = []
        self.current_path_index = 0
        self.path_update_timer = 0
        self.path_update_interval = 60

        self.attacking = False
        self.attack_range = 50
        self.attack_cooldown = 0
        self.attack_recovery_timer = 0
        self.attack_recovery_duration = 350
        self.post_attack_recovery = False

        self.hit_anim_timer = 0

        self.enemy_type = "Pink Star"

    def heuristic(self, a, b):
        """
        Calculate the Manhattan distance between two positions (h function).
        """

        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def find_nearest_purple_rect(self, position, purple_rects):
        """
        Find the nearest purple rect to the given position.
        
        Args:
            position: (x, y) position to find nearest rect to.
            purple_rects: List of purple constraint rectangles.
            
        Returns:
            (x, y) center position of nearest purple rect, or None if no rects found.
        """

        if not purple_rects:
            return None
        
        min_dist = float('inf')
        nearest_pos = None
        
        for purple_rect in purple_rects:
            center_x = purple_rect.rect.centerx
            center_y = purple_rect.rect.centery
            dist = self.heuristic(position, (center_x, center_y))
            if dist < min_dist:
                min_dist = dist
                nearest_pos = (center_x, center_y)
        
        return nearest_pos

    def get_purple_rect_by_center(self, center_pos, purple_rects):
        """
        Given a center_pos (x, y), return the purple_rect whose center matches (or None).
        
        Args:
            center_pos: (x, y) center position to find matching rect to.
            purple_rects: List of purple constraint rectangles.
            
        Returns:
            PurpleRect: object matching the center position, or None if no rect found.
        """

        if not purple_rects or not center_pos:
            return None

        cx, cy = center_pos
        for pr in purple_rects:
            if pr.rect.centerx == cx and pr.rect.centery == cy:
                return pr

        return None 

    def get_node_edge_coord(self, node_center_pos, purple_rects, direction):
        """
        Convert a node center position to an edge coordinate depending on `direction`.
        If direction is "right" -> use node.rect.right, else node.rect.left.
        Does fall back to center if matching rect not found.

        Args:
            node_center_pos: (x, y) center position of the node.
            purple_rects: List of purple constraint rectangles.
            direction: "left" or "right" indicating which edge to return.

        Returns:
            (x, y): coordinate to aim for when following the path.       
        """

        pr = self.get_purple_rect_by_center(node_center_pos, purple_rects)
        if not pr:
            return node_center_pos
        if direction == "right":
            return (pr.rect.right, pr.rect.centery)
        else:
            return (pr.rect.left, pr.rect.centery)

    def get_purple_rect_connections(self, purple_rects):
        """
        Build a graph of connections between purple rects.
        Two rects are connected if:
        - They're on the same Y level and horizontally reachable
        - One is above the other (vertical connection, which requires a jump)
        
        Returns:
            dict mapping (x, y) -> list of connected (x, y) positions.
        """

        connections = {}
        
        for purple_rect in purple_rects:
            pos = (purple_rect.rect.centerx, purple_rect.rect.centery)
            connections[pos] = []
            
            for other_rect in purple_rects:
                if purple_rect == other_rect:
                    continue
                
                other_pos = (other_rect.rect.centerx, other_rect.rect.centery)
                
                if abs(pos[1] - other_pos[1]) < 10:  
                    connections[pos].append(other_pos)
                elif abs(pos[0] - other_pos[0]) < TILE_SIZE * 2 and other_pos[1] < pos[1]:  
                    gap = pos[1] - other_pos[1]
                    if gap <= (TILE_SIZE * 2) + 20:  
                        connections[pos].append(other_pos)
        
        return connections

    def astar_pathfinding(self, start_pos, goal_pos, purple_rects):
        """
        The A* pathfinding algorithm using purple rects as nodes.
        The move cost is 1 for horizontal moves and 2 for vertical moves (jumps).
        
        Args:
            start_pos: (x, y) starting position (nearest purple rect to enemy).
            goal_pos: (x, y) goal position (nearest purple rect to player).
            purple_rects: List of purple constraint rectangles.
            
        Returns:
            List: (x, y) positions representing the path, or None if no path is found.
        """

        if not start_pos or not goal_pos:
            return None
        
        if start_pos == goal_pos:
            return [start_pos]
        
        connections = self.get_purple_rect_connections(purple_rects)
        
        open_set = []
        closed_set = set()
        
        start_node = Node(start_pos)
        goal_node = Node(goal_pos)
        
        heapq.heappush(open_set, start_node)

        while open_set:
            current_node = heapq.heappop(open_set)
            closed_set.add(current_node.position)
            
            if current_node.position == goal_node.position:
                path = []
                while current_node:
                    path.append(current_node.position)
                    current_node = current_node.parent
                return path[::-1]

            neighbours = connections.get(current_node.position, [])
            
            for next_pos in neighbours:
                if next_pos in closed_set:
                    continue

                is_vertical = abs(current_node.position[1] - next_pos[1]) > 10
                move_cost = 2 if is_vertical else 1
                
                neighbour = Node(next_pos, current_node)
                neighbour.g = current_node.g + move_cost
                neighbour.h = self.heuristic(neighbour.position, goal_node.position)
                neighbour.f = neighbour.g + neighbour.h
                
                found_better = False
                for i, open_node in enumerate(open_set):
                    if open_node.position == neighbour.position:
                        if open_node.g <= neighbour.g:
                            found_better = True
                            break
                        else:
                            open_set.pop(i)
                            heapq.heapify(open_set)
                            break
                
                if not found_better:
                    heapq.heappush(open_set, neighbour)

        return None

    def handle_death(self, obstacle_list):
        """
        Handles death fall logic for the PinkStar enemy. Falls until hitting the ground, if not already on the ground.

        Args:
            obstacle_list (list): List of obstacle tiles for collision detection.
        """

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
        Handles AI movement logic (specific movement for Pink Star enemies).
        Uses A* pathfinding when player is in danger zone, otherwise patrols randomly.
        """

        self.velocity.x = 0
        self.moving_left = False
        self.moving_right = False

        purple_rects = []
        if constraint_rect_group:
            for constraint in constraint_rect_group:
                if constraint.colour == PURPLE:
                    purple_rects.append(constraint)

        if self.chasing_player:
            if self.path and self.current_path_index < len(self.path):
                node_center_pos = self.path[self.current_path_index]
                target_x, target_y = self.get_node_edge_coord(node_center_pos, purple_rects, self.direction)
                target_is_node = self.get_purple_rect_by_center(node_center_pos, purple_rects) is not None

                dist_to_target = math.hypot(self.rect.centerx - target_x, self.rect.centery - target_y)

                if dist_to_target < 5:
                    self.current_path_index += 1
                    if self.current_path_index >= len(self.path):
                        self.path = []
                        self.current_path_index = 0
                else:
                    dx = target_x - self.rect.centerx
                    dy = target_y - self.rect.centery

                    if abs(dx) > 3:
                        if dx > 0:
                            self.velocity.x = self.speed
                            self.direction = "right"
                            self.moving_right = True
                        else:
                            self.velocity.x = -self.speed
                            self.direction = "left"
                            self.moving_left = True
                        self.state = "running"
                        self.state_timer = 0

                    if not target_is_node and dy < -12 and abs(dx) < 6 and self.on_ground:
                        self.path = []
                        self.current_path_index = 0
                        self.path_update_timer = self.path_update_interval
                    elif dy < -12 and self.on_ground and self.jump_count < 1:
                        self.jump()
            else:
                if player:
                    dx = player.rect.centerx - self.rect.centerx
                    dy = player.rect.centery - self.rect.centery

                    if abs(dx) > 3:
                        if dx > 0:
                            self.velocity.x = self.speed
                            self.direction = "right"
                            self.moving_right = True
                        else:
                            self.velocity.x = -self.speed
                            self.direction = "left"
                            self.moving_left = True
                        self.state = "running"
                        self.state_timer = 0

                    if dy < -12 and self.on_ground and self.jump_count < 1:
                        self.jump()
        else:
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
                    self.attacking = False
                    self.chasing_player = False
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

        Args:
            win (Surface): The Pygame surface to draw the enemy on.
        """

        win.blit(self.img, self.rect)

    def get_hit(self, damage=20, attacker=None):
        """
        Apply damage to this enemy based on the attacker.
        Sets hit animation timer if hit by a grenade, the only thing that can cause decent damage to this enemy.

        Args:
            damage (int): The amount of damage to apply.
            attacker (object): The entity that is attacking this enemy.
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

        If the player is alive, prioritises Hit, Recover and Attack. Same priority system as FierceTooth.

        Args:
            player (Player): The player object to interact with.
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
        Also handles cooldowns and collisions.

        Args:
            player (Player): The player object to interact with.
            constraint_rect_group (Group): Group of constraint rectangles for AI navigation.
        """

        self.check_alive()
        self.rect.topleft = (int(self.position.x), int(self.position.y))
        self.mask = pygame.mask.from_surface(self.img)

        self.attacking = False

        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        distance = math.hypot(dx, dy)
        if distance <= self.attack_range:
            self.attacking = True

        purple_rects = []
        if constraint_rect_group:
            for constraint in constraint_rect_group:
                if constraint.colour == PURPLE:
                    purple_rects.append(constraint)

        if not self.chasing_player:
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

        if player and player.alive and hasattr(player, 'in_danger_zone') and player.in_danger_zone and not self.post_attack_recovery and self.hit_anim_timer == 0:
            self.chasing_player = True
            
            self.path_update_timer += 1
            if self.path_update_timer >= self.path_update_interval or not self.path:
                self.path_update_timer = 0
                
                enemy_pos = (self.rect.centerx, self.rect.centery)
                start_node = self.find_nearest_purple_rect(enemy_pos, purple_rects)
                
                player_pos = (player.rect.centerx, player.rect.centery)
                goal_node = self.find_nearest_purple_rect(player_pos, purple_rects)
                
                if start_node and goal_node:
                    path_nodes = self.astar_pathfinding(start_node, goal_node, purple_rects)
                    if path_nodes:
                        path_nodes.append(player_pos)
                        self.path = path_nodes
                    else:
                        self.path = [player_pos]
                    self.current_path_index = 0
                    self.path_update_timer = 0
                else:
                    self.path = [player_pos]
                    self.current_path_index = 0
                    self.path_update_timer = 0
        else:
            self.chasing_player = False
            self.path = []
            self.current_path_index = 0

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

        if player and self.attacking and self.attack_cooldown == 0 and self.hit_anim_timer == 0 and self.y_vel < 1:
            dx = player.rect.centerx - self.rect.centerx
            dy = player.rect.centery - self.rect.centery
            distance = math.hypot(dx, dy)
            height_difference = abs(player.rect.centery - self.rect.centery)

            if distance <= self.attack_range // 2 and height_difference < 10:
                if player.alive:
                    player.get_hit(90, attacker=self)
                self.attacking = False
                self.chasing_player = False
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
        