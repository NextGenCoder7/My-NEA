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
    """
    Unmute the background music by setting its volume to 30% (the original sound file is very loud).
    """

    pygame.mixer.music.set_volume(0.3)


def mute_music():
    """
    Mute the background music by setting its volume to 0%.
    """

    pygame.mixer.music.set_volume(0.0)


class Level:
    """
    This is a class to manage level data and state.

    Attributes:
        level_num (int): The current level number.
        time_taken (int): The time taken to complete the level in seconds.
        start_time (int): The start time of the level in milliseconds.
        level_complete (bool): Whether the level has been completed.
        world_data (list): The 2D list representing the level's tile data.
        num_of_checkpoints (int): The number of checkpoints in the level.
        player (Player): The player object associated with the level.
        player_died (bool): Whether the player has died in the level.
        player_lost_health (bool): Whether the player has lost health in the level.
        deaths (int): The number of times the player has died in the level.
    """

    def __init__(self, player, world_data):
        """
        Initialise the Level with player and world data.

        Args:
            player (Player): The player object associated with the level.
            world_data (list): The 2D list representing the level's tile data.
        """

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
        """
        Update the time taken for the level.
        """

        if not self.level_complete:
            current_time = pygame.time.get_ticks()
            self.time_taken = (current_time - self.start_time) // 1000

    def complete_level(self):
        """
        Mark the level as complete.
        """

        self.level_complete = True

    def reset_level(self):
        """
        Reset the level to its initial state.
        """

        self.time_taken = 0
        self.start_time = pygame.time.get_ticks()
        self.level_complete = False
        self.player.current_level = self.level_num
        self.player_died = False
        self.player_lost_health = False

    def get_level_info(self):
        """
        Get a summary of the level information. This includes level number, time taken, number of checkpoints, and a few player stats.

        Returns:
            dict: A dictionary containing the level information: level number, time taken, number of checkpoints and a few player stats.
        """

        return {
            "level": self.level_num,
            "time_taken_sec": self.time_taken,
            "checkpoints": self.num_of_checkpoints,
            "player_health": self.player.health,
            "player_ammo": self.player.ammo,
            "player_grenades": self.player.grenades,
        }
