import sqlite3
import json
from typing import Dict, Any

DB_PATH = "game_data.db"


def _connect():
    """
    Create and return a database connection to the database file.

    Returns:
        sqlite3.Connection: A new connection to the SQLite database.
    """

    return sqlite3.connect(DB_PATH)


def init_db():
    """
    Initialise the database with the 3 required tables if they do not exist.

    1) LevelProgress: Stores per-level progress data.
    2) PlayerTotals: Stores cumulative player statistics.
    3) LevelBestStats: Stores the player's best stats per level.
    """

    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS LevelProgress (
            level_id INTEGER PRIMARY KEY,
            last_checkpoint_x INTEGER,
            last_checkpoint_y INTEGER,
            coin_count INTEGER,
            ammo INTEGER,
            grenades INTEGER,
            health INTEGER,
            time_taken REAL,
            deaths INTEGER DEFAULT 0,
            collected_ids TEXT,
            killed_enemy_ids TEXT,
            reached_end INTEGER DEFAULT 0
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS PlayerTotals (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            total_coins INTEGER DEFAULT 0,
            total_enemies INTEGER DEFAULT 0,
            total_deaths INTEGER DEFAULT 0,
            total_time REAL DEFAULT 0
        )
        """)

        cursor.execute("INSERT OR IGNORE INTO PlayerTotals (id) VALUES (1)")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS LevelBestStats (
            level_id INTEGER PRIMARY KEY,
            best_deaths INTEGER,
            best_coins INTEGER,
            best_enemies INTEGER,
            best_time REAL
        )
        """)

        conn.commit()


def save_level_progress(level_id: int, payload: Dict[str, Any]):
    """
    Throughout the level, save the player's progress in the level. The payload is expected to have the following:

    payload keys:
      last_checkpoint: (x, y) or None
      coin_count, ammo, grenades, health, time_taken, reached_end
      collected_ids: set[str]
      killed_enemy_ids: set[str]

    Args:
        level_id (int): The ID of the level.
        payload (Dict[str, Any]): A dictionary containing the level progress data.
    """

    last_cp = payload.get("last_checkpoint") or (None, None)
    collected = json.dumps(sorted(payload.get("collected_ids", [])))
    killed = json.dumps(sorted(payload.get("killed_enemy_ids", [])))

    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO LevelProgress (level_id, last_checkpoint_x, last_checkpoint_y, coin_count, ammo,
                                   grenades, health, time_taken, deaths, collected_ids, killed_enemy_ids, reached_end)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(level_id) DO UPDATE SET
            last_checkpoint_x=excluded.last_checkpoint_x,
            last_checkpoint_y=excluded.last_checkpoint_y,
            coin_count=excluded.coin_count,
            ammo=excluded.ammo,
            grenades=excluded.grenades,
            health=excluded.health,
            time_taken=excluded.time_taken,
            deaths=excluded.deaths,
            collected_ids=excluded.collected_ids,
            killed_enemy_ids=excluded.killed_enemy_ids,
            reached_end=excluded.reached_end
        """, (
            level_id,
            last_cp[0], last_cp[1],
            payload.get("coin_count", 0),
            payload.get("ammo", 0),
            payload.get("grenades", 0),
            payload.get("health", 0),
            payload.get("time_taken", 0.0),
            payload.get("deaths", 0),
            collected,
            killed,
            1 if payload.get("reached_end") else 0
        ))
        
        conn.commit()


def load_level_progress(level_id: int) -> Dict[str, Any]:
    """
    Load the player's progress in the level. Returns the same payload as save_level_progress function.

    Args:
        level_id (int): The ID of the level.

    Returns:
        Dict[str, Any]: A dictionary containing the level progress data.
    """

    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT last_checkpoint_x, last_checkpoint_y, coin_count, ammo, grenades, health,
               time_taken, deaths, collected_ids, killed_enemy_ids, reached_end
        FROM LevelProgress WHERE level_id = ?
        """, (level_id,))

        row = cursor.fetchone()
        if not row:
            return {
                "last_checkpoint": None,
                "coin_count": 0,
                "ammo": None,
                "grenades": None,
                "health": None,
                "time_taken": 0.0,
                "deaths": 0,
                "collected_ids": set(),
                "killed_enemy_ids": set(),
                "reached_end": False
            }

        collected = set(json.loads(row[8] or "[]"))
        killed = set(json.loads(row[9] or "[]"))

        return {
            "last_checkpoint": (row[0], row[1]) if row[0] is not None and row[1] is not None else None,
            "coin_count": row[2] or 0,
            "ammo": row[3],
            "grenades": row[4],
            "health": row[5],
            "time_taken": row[6] or 0.0,
            "deaths": row[7] or 0,
            "collected_ids": collected,
            "killed_enemy_ids": killed,
            "reached_end": bool(row[10])
        }


def reset_level_progress(level_id: int):
    """
    Reset the progress and stats for the level.
    When the player clicks on this level next time, they start it afresh.

    Args:
        level_id (int): the ID of the level.
    """

    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM LevelProgress WHERE level_id = ?", (level_id,))
        conn.commit()


def update_totals(delta_coins=0, delta_enemies=0, delta_deaths=0, delta_time=0.0):
    """
    Update the total lifetime player stats while the player is playing a level
    (coins, deaths, enemies killed, time played).

    Args:
        delta_coins (int): number of coins to add to total.
        delta_enemies (int): number of enemies killed to add to total.
        delta_deaths (int): number of deaths to add to total.
        delta_time (float): amount of time to add to total.
    """

    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE PlayerTotals
        SET total_coins   = total_coins   + ?,
            total_enemies = total_enemies + ?,
            total_deaths  = total_deaths  + ?,
            total_time    = total_time    + ?
        WHERE id = 1
        """, (delta_coins, delta_enemies, delta_deaths, delta_time))
        conn.commit()


def get_player_totals():
    """
    Retrieve the total lifetime player stats (coins, deaths, enemies killed, time played).

    Returns:
        dict: the saved total stats for the player.
    """

    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT total_coins, total_enemies, total_deaths, total_time
        FROM PlayerTotals WHERE id = 1
        """)

        row = cursor.fetchone()
        if not row:
            return {"total_coins": 0, "total_enemies": 0, "total_deaths": 0, "total_time": 0.0}
        return {
            "total_coins": row[0] or 0,
            "total_enemies": row[1] or 0,
            "total_deaths": row[2] or 0,
            "total_time": row[3] or 0.0,
        }


def get_level_progress():
    """
    Return a list of dicts for each saved LevelProgress row.
    If a level has been completed and reset, it won't appear here.
    """

    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT level_id, last_checkpoint_x, last_checkpoint_y, coin_count, ammo,
               grenades, health, time_taken, deaths, collected_ids, killed_enemy_ids, reached_end
        FROM LevelProgress
        ORDER BY level_id ASC
        """)

        rows = cursor.fetchall()
        results = []
        for r in rows:
            results.append({
                "level_id": r[0],
                "coin_count": r[3] or 0,
                "time_taken": r[7] or 0.0,
                "deaths": r[8] or 0,
                "killed_enemy_ids": set(json.loads(r[10] or "[]")),
                "reached_end": bool(r[11]),
            })

        return results


def update_best_stats(level_id: int, deaths: int, coins: int, enemies: int, time_taken: float):
    """
    Update the player's best stats per level after level completion. It takes into account:

      1) deaths (lower is better)
      2) coins (higher is better)
      3) enemies (higher is better)
      4) time taken (lower is better).
    """

    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT best_deaths, best_coins, best_enemies, best_time
        FROM LevelBestStats WHERE level_id = ?
        """, (level_id,))

        row = cursor.fetchone()
        if not row:
            cursor.execute("""
            INSERT INTO LevelBestStats (level_id, best_deaths, best_coins, best_enemies, best_time)
            VALUES (?, ?, ?, ?, ?)
            """, (level_id, deaths, coins, enemies, time_taken))
            conn.commit()
            return

        best = {
            "deaths": row[0] if row[0] is not None else 1_000_000,
            "coins": row[1] if row[1] is not None else 0,
            "enemies": row[2] if row[2] is not None else 0,
            "time": row[3] if row[3] is not None else 1e12,
        }

        picks = (deaths, -coins, -enemies, time_taken)
        current = (best["deaths"], -best["coins"], -best["enemies"], best["time"])
        if picks < current:
            cursor.execute("""
            UPDATE LevelBestStats
            SET best_deaths = ?, best_coins = ?, best_enemies = ?, best_time = ?
            WHERE level_id = ?
            """, (deaths, coins, enemies, time_taken, level_id))
            conn.commit()


def get_level_best_stats():
    """
    Retrieve and return the player's best stats for each level
    (deaths, coins, enemies killed and time taken).
    """

    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT level_id, best_deaths, best_coins, best_enemies, best_time
        FROM LevelBestStats
        ORDER BY level_id ASC
        """)

        rows = cursor.fetchall()
        results = []
        for r in rows:
            results.append({
                "level_id": r[0],
                "best_deaths": r[1],
                "best_coins": r[2],
                "best_enemies": r[3],
                "best_time": r[4],
            })
            
        return results
