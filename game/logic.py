"""
Mastermind-style feedback and scoring for Locksmith.

Exact pegs are marked first; partial pegs use remaining multiset counts so
duplicates do not double-count (classic Mastermind rule).
"""

from __future__ import annotations

from typing import Sequence

CODE_LENGTH = 4
DIGIT_MIN = 1
DIGIT_MAX = 6
MAX_GUESSES = 10


def validate_guess(guess: Sequence[int]) -> list[int]:
    if len(guess) != CODE_LENGTH:
        raise ValueError(f"Guess must have length {CODE_LENGTH}")
    values: list[int] = []
    for d in guess:
        try:
            n = int(d)
        except (TypeError, ValueError) as exc:
            raise ValueError("Guess digits must be integers") from exc
        if n < DIGIT_MIN or n > DIGIT_MAX:
            raise ValueError(f"Digits must be in {DIGIT_MIN}..{DIGIT_MAX}")
        values.append(n)
    return values


def evaluate_guess(secret: Sequence[int], guess: Sequence[int]) -> tuple[int, int]:
    """Return (exact, partial) peg counts."""
    secret_list = list(secret)
    guess_list = validate_guess(guess)

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


def score_for_win(guesses_used: int) -> int:
    """Winning score: fewer guesses → higher score. Range 100..1000."""
    if guesses_used < 1 or guesses_used > MAX_GUESSES:
        raise ValueError("guesses_used out of range")
    return (11 - guesses_used) * 100


def generate_secret(rng=None) -> list[int]:
    import random

    r = rng or random
    return [r.randint(DIGIT_MIN, DIGIT_MAX) for _ in range(CODE_LENGTH)]
