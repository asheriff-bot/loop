from game.logic import evaluate_guess, score_for_win, validate_guess
import pytest


def test_all_exact():
    assert evaluate_guess([1, 2, 3, 4], [1, 2, 3, 4]) == (4, 0)


def test_all_partial_permutation():
    assert evaluate_guess([1, 2, 3, 4], [4, 3, 2, 1]) == (0, 4)


def test_duplicate_secret_partial_not_overcounted():
    # Secret has two 1s; guess has one 1 elsewhere → at most one partial from that.
    exact, partial = evaluate_guess([1, 1, 2, 3], [4, 1, 5, 6])
    assert exact == 1
    assert partial == 0


def test_duplicate_guess_partial():
    exact, partial = evaluate_guess([1, 2, 3, 4], [1, 1, 1, 1])
    assert exact == 1
    assert partial == 0


def test_mixed():
    assert evaluate_guess([1, 2, 3, 4], [1, 3, 5, 6]) == (1, 1)


def test_validate_rejects_out_of_range():
    with pytest.raises(ValueError):
        validate_guess([1, 2, 3, 7])


def test_score_bounds():
    assert score_for_win(1) == 1000
    assert score_for_win(10) == 100


def test_hard_score_and_length():
    from game.logic import get_mode, evaluate_guess

    cfg = get_mode("hard")
    assert cfg.code_length == 5
    assert cfg.digit_max == 8
    assert score_for_win(1, "hard") == 12 * 120
    assert evaluate_guess([1, 2, 3, 4, 5], [1, 2, 3, 4, 5], digit_min=1, digit_max=8) == (5, 0)
