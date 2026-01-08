Hello! Welcome to this project. This is my NEA (Non-Examined Assessment), which is part of the year 13 A-level Computer Science course. 

I am making a platformer-inspired game engine, using python. The library I am using is called pygame, which is used to make 2D games with python.

The player can collect collectibles such as coins, health and ammo gems, and grenade boxes. The player can also sprint, but has stamina
so the player cannot sprint forever. The player has health, and if the player's health reaches 0, the level ends.

The player can shoot ammo, and throw grenades. The longer the player holds g, the greater the distance the grenade will be thrown at 
(until a certain max limit of course).

There are 3 types of enemies:
	- Fierce Tooth
	- Seashell Pearl
	- Pink Star

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
to return to its original position. 

Fierce Tooth and Pink Star enemies have a post bite recovery time, where after they bite the player, they have to wait a few seconds 
before they can start chasing/attacking the player again (Pink Star having the longer recovery time). This gives the player a chance to escape 
or retaliate. Seashell Pearl enemies however do not have a recovery time after biting, as they are stationary and cannot chase the player.
The player will be continually damaged by the bite if they stay in very close proximity to the Seashell Pearl. Seashell Pearl also has the
longer vision range than Fierce Tooth enemies.

This project also has an in-built level editor, which allows the user to create their own levels using the game engine. The user can place 
the selected tiles on the right side, platforms, enemies, collectibles, checkpoints etc, and the player spawn point. 
The user can then save the level to a file and edit or load it later to play. Loading a level file reads the data and generates the 
level based on the data in the file, if it exists.

I hope you enjoy my game engine!
