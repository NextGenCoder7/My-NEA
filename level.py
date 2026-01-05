import pygame

pygame.mixer.init()

pygame.mixer.music.load('assets/Sounds/music.mp3')
pygame.mixer.music.set_volume(0.0)
pygame.mixer.music.play(-1, 0.0, 5000)

jump_fx = pygame.mixer.Sound('assets/Sounds/jump.wav')
jump_fx.set_volume(0.5)
explosion_fx = pygame.mixer.Sound('assets/Sounds/explosion.wav')
explosion_fx.set_volume(0.5)
shot_fx = pygame.mixer.Sound('assets/Sounds/shot.wav')
shot_fx.set_volume(0.5)


def unmute_music():
    pygame.mixer.music.set_volume(0.3)


def mute_music():
    pygame.mixer.music.set_volume(0.0)


class Level:

    def __init__(self, player, world_data):
        self.level_num = player.current_level
        self.time_taken = 0
        self.start_time = pygame.time.get_ticks()
        self.level_complete = False
        self.world_data = world_data
        self.num_of_checkpoints = self.count_checkpoints()
        self.player = player
        self.player_died = False
        self.player_lost_health = False
        self.deaths = 0

    def count_checkpoints(self):
        """
        Count the number of checkpoints in the level data.
        """
        return sum(1 for row in self.world_data for tile in row if tile == 28)

    def update_time(self):
        """Update the time taken for the level."""
        if not self.level_complete:
            current_time = pygame.time.get_ticks()
            self.time_taken = (current_time - self.start_time) // 1000

    def complete_level(self):
        """Mark the level as complete."""
        self.level_complete = True

    def reset_level(self):
        """Reset the level to its initial state."""
        self.time_taken = 0
        self.start_time = pygame.time.get_ticks()
        self.level_complete = False
        self.player.current_level = self.level_num
        self.player_died = False
        self.player_lost_health = False

    def get_level_info(self):
        return {
            "level": self.level_num,
            "time_taken_sec": self.time_taken,
            "checkpoints": self.num_of_checkpoints,
            "player_health": self.player.health,
            "player_ammo": self.player.ammo,
            "player_grenades": self.player.grenades,
        }