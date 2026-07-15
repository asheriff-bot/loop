import pytest

import game.app as ga
from game.app import create_app
from game.daily import daily_secret


@pytest.fixture()
def client(tmp_path):
    app = create_app(db_path=str(tmp_path / "test.db"))
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.get_json()["ok"] is True


def test_create_and_guess_win_path(client):
    res = client.post(
        "/api/games",
        json={"player_name": "Ada", "mode": "daily", "challenge_date": "2026-07-14"},
    )
    game_id = res.get_json()["game_id"]
    secret = daily_secret("2026-07-14")

    g = client.get(f"/api/games/{game_id}").get_json()
    assert "secret" not in g

    res = client.post(f"/api/games/{game_id}/guess", json={"guess": secret})
    body = res.get_json()
    assert res.status_code == 200
    assert body["status"] == "won"
    assert body["score"] == 1000
    assert body["game"]["secret"] == secret


def test_bad_guess_rejected(client):
    game_id = client.post("/api/games", json={"player_name": "Bob"}).get_json()["game_id"]
    res = client.post(f"/api/games/{game_id}/guess", json={"guess": [1, 2, 3]})
    assert res.status_code == 400


def test_scores_list(client):
    res = client.post(
        "/api/games",
        json={"player_name": "Ada", "mode": "daily", "challenge_date": "2026-07-14"},
    )
    game_id = res.get_json()["game_id"]
    secret = daily_secret("2026-07-14")
    client.post(f"/api/games/{game_id}/guess", json={"guess": secret})
    scores = client.get("/api/scores").get_json()["scores"]
    assert scores and scores[0]["player_name"] == "Ada"


def test_index_renders(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"Locksmith" in res.data


def test_daily_endpoint(client):
    res = client.get("/api/daily")
    assert res.status_code == 200
    body = res.get_json()
    assert body["mode"] == "daily"
    assert "date" in body
    assert "secret" not in body


def test_hard_mode_win(tmp_path, monkeypatch):
    secret = [1, 2, 3, 4, 5]
    monkeypatch.setattr(ga, "generate_secret", lambda mode="classic", rng=None: secret)
    app = create_app(db_path=str(tmp_path / "hard.db"))
    c = app.test_client()

    res = c.post("/api/games", json={"player_name": "Hardy", "mode": "hard"})
    assert res.status_code == 201
    meta = res.get_json()
    assert meta["code_length"] == 5
    assert meta["digit_max"] == 8
    assert meta["max_guesses"] == 12

    body = c.post(
        f"/api/games/{meta['game_id']}/guess", json={"guess": secret}
    ).get_json()
    assert body["status"] == "won"
    assert body["score"] == (13 - 1) * 120
    scores = c.get("/api/scores?mode=hard").get_json()["scores"]
    assert scores[0]["mode"] == "hard"
