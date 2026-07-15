"""Deterministic daily challenge codes (Step 2 extension)."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from game.logic import CODE_LENGTH, DIGIT_MAX, DIGIT_MIN


def today_utc() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def daily_secret(date_str: str) -> list[int]:
    """
    Derive a stable 4-digit secret from a YYYY-MM-DD string.

    Same date → same code for every player (shared daily leaderboard).
    """
    digest = hashlib.sha256(f"locksmith-daily:{date_str}".encode("utf-8")).digest()
    secret: list[int] = []
    for i in range(CODE_LENGTH):
        # Map byte → digit in [DIGIT_MIN, DIGIT_MAX]
        span = DIGIT_MAX - DIGIT_MIN + 1
        secret.append(DIGIT_MIN + (digest[i] % span))
    return secret
