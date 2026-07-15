"""
Mastermind-style feedback and scoring for Locksmith.

Exact pegs are marked first; partial pegs use remaining multiset counts so
duplicates do not double-count (classic Mastermind rule).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

# Classic defaults (base system)
CODE_LENGTH = 4
DIGIT_MIN = 1
DIGIT_MAX = 6
MAX_GUESSES = 10


@dataclass(frozen=True)
class ModeConfig:
    name: str
    code_length: int
    digit_min: int
    digit_max: int
    max_guesses: int
    score_base: int  # (score_base - guesses_used) * score_mult
    score_mult: int


MODES: dict[str, ModeConfig] = {
    "classic": ModeConfig("classic", 4, 1, 6, 10, 11, 100),
    "daily": ModeConfig("daily", 4, 1, 6, 10, 11, 100),
    "hard": ModeConfig("hard", 5, 1, 8, 12, 13, 120),
}


def get_mode(mode: str) -> ModeConfig:
    key = (mode or "classic").lower()
    if key not in MODES:
        raise ValueError(f"Unknown mode: {mode}")
    return MODES[key]


def validate_guess(
    guess: Sequence[int],
    *,
    code_length: int = CODE_LENGTH,
    digit_min: int = DIGIT_MIN,
    digit_max: int = DIGIT_MAX,
) -> list[int]:
    if len(guess) != code_length:
        raise ValueError(f"Guess must have length {code_length}")
    values: list[int] = []
    for d in guess:
        try:
            n = int(d)
        except (TypeError, ValueError) as exc:
            raise ValueError("Guess digits must be integers") from exc
        if n < digit_min or n > digit_max:
            raise ValueError(f"Digits must be in {digit_min}..{digit_max}")
        values.append(n)
    return values


def evaluate_guess(
    secret: Sequence[int],
    guess: Sequence[int],
    *,
    digit_min: int = DIGIT_MIN,
    digit_max: int = DIGIT_MAX,
) -> tuple[int, int]:
    """Return (exact, partial) peg counts."""
    secret_list = list(secret)
    guess_list = validate_guess(
        guess,
        code_length=len(secret_list),
        digit_min=digit_min,
        digit_max=digit_max,
    )

    exact = 0
    secret_remain: list[int] = []
    guess_remain: list[int] = []
    for s, g in zip(secret_list, guess_list):
        if s == g:
            exact += 1
        else:
            secret_remain.append(s)
            guess_remain.append(g)

    partial = 0
    pool = secret_remain[:]
    for g in guess_remain:
        if g in pool:
            partial += 1
            pool.remove(g)
    return exact, partial


def score_for_win(guesses_used: int, mode: str = "classic") -> int:
    cfg = get_mode(mode)
    if guesses_used < 1 or guesses_used > cfg.max_guesses:
        raise ValueError("guesses_used out of range")
    return (cfg.score_base - guesses_used) * cfg.score_mult


def generate_secret(mode: str = "classic", rng=None) -> list[int]:
    import random

    cfg = get_mode(mode if mode != "daily" else "classic")
    r = rng or random
    return [r.randint(cfg.digit_min, cfg.digit_max) for _ in range(cfg.code_length)]
