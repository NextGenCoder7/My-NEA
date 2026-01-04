import sqlite3
import json
from typing import Optional, Dict, Any

DB_PATH = "game_data.db"


def _connect():
    return sqlite3.connect(DB_PATH)


def init_db():
    with _connect() as conn:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS LevelProgress (
            level_id INTEGER PRIMARY KEY,
            last_checkpoint_x INTEGER,
            last_checkpoint_y INTEGER,
            coin_count INTEGER,
            ammo INTEGER,
            grenades INTEGER,
            health INTEGER,
            time_taken REAL,
            collected_ids TEXT,
            killed_enemy_ids TEXT,
            reached_end INTEGER DEFAULT 0
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS PlayerTotals (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            total_coins INTEGER DEFAULT 0,
            total_enemies INTEGER DEFAULT 0,
            total_deaths INTEGER DEFAULT 0,
            total_time REAL DEFAULT 0
        )
        """)
        cur.execute("INSERT OR IGNORE INTO PlayerTotals (id) VALUES (1)")
        conn.commit()


def save_level_progress(level_id: int, payload: Dict[str, Any]):
    """
    payload keys:
      last_checkpoint: (x, y) or None
      coin_count, ammo, grenades, health, time_taken, reached_end
      collected_ids: set[str]
      killed_enemy_ids: set[str]
    """
    last_cp = payload.get("last_checkpoint") or (None, None)
    collected = json.dumps(sorted(payload.get("collected_ids", [])))
    killed = json.dumps(sorted(payload.get("killed_enemy_ids", [])))
    with _connect() as conn:
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO LevelProgress (level_id, last_checkpoint_x, last_checkpoint_y, coin_count, ammo,
                                   grenades, health, time_taken, collected_ids, killed_enemy_ids, reached_end)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(level_id) DO UPDATE SET
            last_checkpoint_x=excluded.last_checkpoint_x,
            last_checkpoint_y=excluded.last_checkpoint_y,
            coin_count=excluded.coin_count,
            ammo=excluded.ammo,
            grenades=excluded.grenades,
            health=excluded.health,
            time_taken=excluded.time_taken,
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
            collected,
            killed,
            1 if payload.get("reached_end") else 0
        ))
        conn.commit()


def load_level_progress(level_id: int) -> Dict[str, Any]:
    with _connect() as conn:
        cur = conn.cursor()
        cur.execute("""
        SELECT last_checkpoint_x, last_checkpoint_y, coin_count, ammo, grenades, health,
               time_taken, collected_ids, killed_enemy_ids, reached_end
        FROM LevelProgress WHERE level_id = ?
        """, (level_id,))
        row = cur.fetchone()
        if not row:
            return {
                "last_checkpoint": None,
                "coin_count": 0,
                "ammo": None,
                "grenades": None,
                "health": None,
                "time_taken": 0.0,
                "collected_ids": set(),
                "killed_enemy_ids": set(),
                "reached_end": False
            }
        collected = set(json.loads(row[7] or "[]"))
        killed = set(json.loads(row[8] or "[]"))
        return {
            "last_checkpoint": (row[0], row[1]) if row[0] is not None and row[1] is not None else None,
            "coin_count": row[2] or 0,
            "ammo": row[3],
            "grenades": row[4],
            "health": row[5],
            "time_taken": row[6] or 0.0,
            "collected_ids": collected,
            "killed_enemy_ids": killed,
            "reached_end": bool(row[9])
        }


def reset_level_progress(level_id: int):
    with _connect() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM LevelProgress WHERE level_id = ?", (level_id,))
        conn.commit()


def update_totals(delta_coins=0, delta_enemies=0, delta_deaths=0, delta_time=0.0):
    with _connect() as conn:
        cur = conn.cursor()
        cur.execute("""
        UPDATE PlayerTotals
        SET total_coins   = total_coins   + ?,
            total_enemies = total_enemies + ?,
            total_deaths  = total_deaths  + ?,
            total_time    = total_time    + ?
        WHERE id = 1
        """, (delta_coins, delta_enemies, delta_deaths, delta_time))
        conn.commit()


def get_player_totals():
    with _connect() as conn:
        cur = conn.cursor()
        cur.execute("""
        SELECT total_coins, total_enemies, total_deaths, total_time
        FROM PlayerTotals WHERE id = 1
        """)
        row = cur.fetchone()
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
    Returns a list of dicts for each saved LevelProgress row.
    If a level has been completed and reset, it won't appear here.
    """
    with _connect() as conn:
        cur = conn.cursor()
        cur.execute("""
        SELECT level_id, last_checkpoint_x, last_checkpoint_y, coin_count, ammo,
               grenades, health, time_taken, collected_ids, killed_enemy_ids, reached_end
        FROM LevelProgress
        ORDER BY level_id ASC
        """)
        rows = cur.fetchall()
        results = []
        for r in rows:
            results.append({
                "level_id": r[0],
                "coin_count": r[3] or 0,
                "time_taken": r[7] or 0.0,
                "killed_enemy_ids": set(json.loads(r[9] or "[]")),
                "reached_end": bool(r[10]),
            })

        return results
