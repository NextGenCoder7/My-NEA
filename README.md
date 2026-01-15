Hello! Welcome to this project. This is my NEA (Non-Examined Assessment), which is part of the year 13 A-level Computer Science course. 

I have made platformer-inspired game engine, using python. The library I am using is called pygame, which is used to make 2D games with python.

The player can collect collectibles such as coins, health and ammo gems, and grenade boxes. The player can also sprint, but has stamina
so the player cannot sprint forever. The player has health, and if the player's health reaches 0, the level ends.

The player can shoot ammo, and throw grenades. The longer the player holds g, the greater the distance the grenade will be thrown at 
(until a certain max limit of course).

There are 3 types of enemies: Fierce Tooth, Seashell Pearl and Pink Star.

FierceTooth is your general platformer enemy, which patrols in particular areas and has vision. If the player is in vision, it will
shoot the player and try to move closer to the player. If within a certain close range, it will try and attack the player (bite) 
instead of shooting, and if the enemy and player collide then the attack causes more damage than just shooting the player. When
smartmode is enabled, it can dodge player bullets and run away from grenades if the enemy sees them, and it can track where the player
goes even if the player goes out of vision. If the player jumps over the enemy's head, goes up on a nearby platform in the area,
steps down from the platform, tries to juke the enemy by double jumping over his head, Fiercetooth tries to calculate where the player
would be. 

Seashell Pearl is a stationary enemy that shoots at the player when they are in vision. It does not move from its position, but it can
shoot and cause more shooting damage than FierceTooth. Seashell also bites when the player comes too close to the enemy. 

Pink Star is a unique enemy. It guards an area called the danger zone, which is a risk and reward zone. The area has lots of coins and a few
collectibles for the player to collect, but it is also guarded by the Pink Star. The Pink Star moves around the danger zone. As soon as
the player enters the danger zone, the Pink Star chases after the player relentlessly, trying to attack the player to cause damage. It
uses the A* algorithm and updates the path every second to try and find the fastest path to the player. It moves faster than the player
when chasing, and the player cannot sprint. The only way to escape the Pink Star is to leave the danger zone, which causes the Pink Star 
to return to random behaviour (idling and patrolling). These enemies have much higher health than Fierce Tooth and Seashell Pearl enemies.

Fierce Tooth and Pink Star enemies have a post bite recovery time, where after they bite the player, they have to wait a few seconds 
before they can start chasing/attacking the player again (Pink Star having the longer recovery time). This gives the player a chance to escape 
or retaliate. Seashell Pearl enemies however do not have a recovery time after biting, as they are stationary and cannot chase the player.
The player will be continually damaged by the bite if they stay in very close proximity to the Seashell Pearl. Seashell Pearl also has the
longer vision range than Fierce Tooth enemies, as it is designed to be slightly more advatnageous in some ways since it cannot move.

The project also saves the level progress of the player. While the player is playing a level, the game updates the player's progress every
frame, such as player's last checkpoint, health, collectibles collected, deaths, enemies killed etc. If the player exits the level or dies, 
the progress is saved. When the player loads the level again, the game reads the data from the file and updates the level to match the player's 
last progress and allows the player to continue from there. The player also has an option to simply restart the whole level and hence delete
the current level progress. When the player completes a level, there are four stats the game shows to the player, which reflect the best stats
per level: deaths, time taken, coins collcted and enemies killed. The lower the better for the first 2 and vice versa for the last 2 respectively.
The stats page in general shows those four stats for the current level progress too, but best stats only get updated if the player completes the 
level. Total lifetime stats are also tracked across all levels, only for the four stats just mentioned. The sqlite3 library is used to achieve all this.

The reason I call this project a game engine and not just a game is because the design is modular and resuable. 

This project has an in-built level editor, which allows the user to create their own levels and save them. The user can place 
the selected tiles on the right side, platforms, enemies, collectibles, checkpoints etc, and the player spawn point. 
The user can then save the level to a file and edit or load it later to play. Loading a level file reads the data and generates the 
level based on the data in the file, if it exists. Level files are saved in json format.

To add another entity or object, add the image in the level editor tiles folder in assets, increment TILE_TYPES in constants.py,
go to level editor and place it wherver you want in the levels, create a class for it in its own file or in another existing file, import 
in main.py, in the process_data method in the World class make sure to add a condition to create an instance of the class when the tile type is detected,
and finally add any necessary logic in the game loop in main.py if needed.
If you want this to be saved in the database as well, you will need to add it as a new row in the functions in database.py file. Make sure to
also update the functions in main.py that use the database functions to include the new row.

I hope you enjoy my game engine!
