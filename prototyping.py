# import heapq


# class Node:
#     def __init__(self, position, parent=None):
#         self.position = position  
#         self.parent = parent
#         self.g = 0  
#         self.h = 0 
#         self.f = 0 

#     def __lt__(self, other):
#         return self.f < other.f  


# def heuristic(a, b):
#     """Manhattan distance used to calculate distance from node a to node b"""
#     return abs(a[0] - b[0]) + abs(a[1] - b[1])


# def astar(start, goal, grid):
#     """
#     A* pathfinding on a 2D grid.
#     grid: 2D list where 0 = free, 1 = obstacle
#     start: (x, y)
#     goal: (x, y)
#     """
#     open_set = []
#     closed_set = set()

#     start_node = Node(start)
#     goal_node = Node(goal)

#     heapq.heappush(open_set, start_node)

#     while open_set:
#         current_node = heapq.heappop(open_set)
#         closed_set.add(current_node.position)

#         if current_node.position == goal_node.position:
#             path = []
#             while current_node:
#                 path.append(current_node.position)
#                 current_node = current_node.parent
#             return path[::-1]  

#         x, y = current_node.position
#         neighbors = [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]

#         for next_pos in neighbors:
#             if (
#                 0 <= next_pos[0] < len(grid[0]) and
#                 0 <= next_pos[1] < len(grid) and
#                 grid[next_pos[1]][next_pos[0]] == 0 and
#                 next_pos not in closed_set
#             ):
#                 neighbor = Node(next_pos, current_node)
#                 neighbor.g = current_node.g + 1
#                 neighbor.h = heuristic(neighbor.position, goal_node.position)
#                 neighbor.f = neighbor.g + neighbor.h

#                 if not any(open_node.position == neighbor.position and open_node.g <= neighbor.g for open_node in open_set):
#                     heapq.heappush(open_set, neighbor)

#     return None 

# # -----------------------
# # Prototype test
# # -----------------------
# # 0 = walkable, 1 = obstacle
# grid = [
#     [0, 0, 0, 0, 0],
#     [0, 1, 1, 0, 0],
#     [0, 0, 0, 0, 1],
#     [0, 1, 0, 1, 0],
#     [0, 0, 0, 0, 0]
# ]

# start = (4, 4)
# goal = (1, 0)

# path = astar(start, goal, grid)
# print("path:", path)

# if path:
#     grid_with_path = [row[:] for row in grid]  
#     for (x, y) in path:
#         if grid_with_path[y][x] == 0:   
#             grid_with_path[y][x] = "*"

#     grid_with_path[start[1]][start[0]] = "S"  
#     grid_with_path[goal[1]][goal[0]] = "E"      

#     for row in grid_with_path:
#         print(" ".join(str(cell) for cell in row))

# --------------------------------------------------------------------------------------------------------------------------

import sqlite3

conn = sqlite3.connect("game_data.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS Levels (
    level_id INTEGER PRIMARY KEY,
    total_coins INTEGER,
    total_enemies INTEGER,
    total_checkpoints INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS PlayerStats (
    stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
    level_id INTEGER,
    coins_collected INTEGER,
    enemies_killed INTEGER,
    time_taken REAL,
    deaths INTEGER,
    last_checkpoint INTEGER,
    FOREIGN KEY (level_id) REFERENCES Levels(level_id)
)
""")

levels = [
    (1, "Level 1", 50, 10, 3),
    (2, "Level 2", 30, 15, 2),
    (3, "Level 3", 100, 25, 5)
]

cursor.executemany("INSERT OR IGNORE INTO Levels VALUES (?, ?, ?, ?, ?)", levels)


player_stats = [
    (1, 45, 8, 120.5, 2, 3), 
    (2, 20, 10, 300.0, 5, 2), 
    (3, 80, 18, 500.2, 7, 4)  
]


cursor.executemany("""
INSERT INTO PlayerStats (level_id, coins_collected, enemies_killed, time_taken, deaths, last_checkpoint)
VALUES (?, ?, ?, ?, ?, ?)
""", player_stats)


cursor.execute("""
SELECT L.level_name, 
       P.coins_collected, L.total_coins,
       P.enemies_killed, L.total_enemies,
       P.time_taken, P.deaths
FROM PlayerStats P
JOIN Levels L ON P.level_id = L.level_id
""")

rows = cursor.fetchall()
print("Player stats vs Level totals:")
for row in rows:
    print(row)


cursor.execute("""
SELECT L.level_name, 
       ROUND((P.coins_collected * 100.0) / L.total_coins, 2) as coin_completion,
       ROUND((P.enemies_killed * 100.0) / L.total_enemies, 2) as enemy_completion
FROM PlayerStats P
JOIN Levels L ON P.level_id = L.level_id
""")

completion = cursor.fetchall()
print("\nCompletion %:")
for row in completion:
    print(row)


conn.commit()
conn.close()

