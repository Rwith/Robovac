"""Tiny SQLite helper for map metadata.

Map images live as PNG files in store/maps/; this table just remembers their
metadata (resolution, size, origin) so the dashboard can place them correctly.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from shared.schemas import MapUpload, OccupancyGridMeta, Pose2D

DB_PATH = Path(__file__).parent / "robovac.db"


def _conn() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def init() -> None:
    with _conn() as c:
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS maps (
                name TEXT PRIMARY KEY,
                robot_id TEXT,
                resolution REAL,
                width INTEGER,
                height INTEGER,
                origin_x REAL,
                origin_y REAL,
                origin_theta REAL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def save_map_meta(m: MapUpload) -> None:
    with _conn() as c:
        c.execute(
            """
            INSERT INTO maps
                (name, robot_id, resolution, width, height,
                 origin_x, origin_y, origin_theta)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                robot_id=excluded.robot_id,
                resolution=excluded.resolution,
                width=excluded.width, height=excluded.height,
                origin_x=excluded.origin_x, origin_y=excluded.origin_y,
                origin_theta=excluded.origin_theta,
                updated_at=CURRENT_TIMESTAMP
            """,
            (
                m.name, m.robot_id, m.meta.resolution, m.meta.width, m.meta.height,
                m.meta.origin.x, m.meta.origin.y, m.meta.origin.theta,
            ),
        )


def load_map_meta(name: str) -> OccupancyGridMeta | None:
    with _conn() as c:
        row = c.execute(
            "SELECT resolution, width, height, origin_x, origin_y, origin_theta "
            "FROM maps WHERE name = ?",
            (name,),
        ).fetchone()
    if not row:
        return None
    res, w, h, ox, oy, ot = row
    return OccupancyGridMeta(
        resolution=res, width=w, height=h,
        origin=Pose2D(x=ox, y=oy, theta=ot),
    )
