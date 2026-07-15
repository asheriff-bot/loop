"""SQLite persistence for Locksmith games and scores."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Optional

DEFAULT_DB = Path(__file__).resolve().parent / "data" / "locksmith.db"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Database:
    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else DEFAULT_DB
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.init_schema()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init_schema(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS games (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_name TEXT NOT NULL,
                    secret TEXT NOT NULL,
                    status TEXT NOT NULL,
                    guesses_used INTEGER NOT NULL DEFAULT 0,
                    score INTEGER,
                    created_at TEXT NOT NULL,
                    finished_at TEXT,
                    mode TEXT NOT NULL DEFAULT 'classic',
                    challenge_date TEXT
                );

                CREATE TABLE IF NOT EXISTS guesses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id INTEGER NOT NULL,
                    guess_json TEXT NOT NULL,
                    exact INTEGER NOT NULL,
                    partial INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(game_id) REFERENCES games(id)
                );
                """
            )

    def create_game(
        self,
        player_name: str,
        secret: list[int],
        mode: str = "classic",
        challenge_date: Optional[str] = None,
    ) -> int:
        with self.connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO games (player_name, secret, status, guesses_used, score,
                                   created_at, mode, challenge_date)
                VALUES (?, ?, 'active', 0, NULL, ?, ?, ?)
                """,
                (
                    player_name.strip() or "Player",
                    json.dumps(secret),
                    utc_now(),
                    mode,
                    challenge_date,
                ),
            )
            return int(cur.lastrowid)

    def get_game(self, game_id: int) -> Optional[dict[str, Any]]:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM games WHERE id = ?", (game_id,)
            ).fetchone()
            if row is None:
                return None
            guesses = conn.execute(
                """
                SELECT guess_json, exact, partial, created_at
                FROM guesses WHERE game_id = ? ORDER BY id ASC
                """,
                (game_id,),
            ).fetchall()
        game = dict(row)
        game["secret"] = json.loads(game["secret"])
        game["guesses"] = [
            {
                "guess": json.loads(g["guess_json"]),
                "exact": g["exact"],
                "partial": g["partial"],
                "created_at": g["created_at"],
            }
            for g in guesses
        ]
        return game

    def add_guess(
        self,
        game_id: int,
        guess: list[int],
        exact: int,
        partial: int,
        status: str,
        score: Optional[int],
        guesses_used: int,
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO guesses (game_id, guess_json, exact, partial, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (game_id, json.dumps(guess), exact, partial, utc_now()),
            )
            finished_at = utc_now() if status != "active" else None
            conn.execute(
                """
                UPDATE games
                SET guesses_used = ?, status = ?, score = ?,
                    finished_at = COALESCE(?, finished_at)
                WHERE id = ?
                """,
                (guesses_used, status, score, finished_at, game_id),
            )

    def top_scores(self, limit: int = 10, mode: Optional[str] = None) -> list[dict[str, Any]]:
        query = """
            SELECT player_name, score, guesses_used, mode, challenge_date, finished_at
            FROM games
            WHERE status = 'won' AND score IS NOT NULL
        """
        params: list[Any] = []
        if mode:
            query += " AND mode = ?"
            params.append(mode)
        query += " ORDER BY score DESC, finished_at ASC LIMIT ?"
        params.append(limit)
        with self.connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
