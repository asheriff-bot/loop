import pytest

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
    res = client.post("/api/games", json={"player_name": "Ada"})
    assert res.status_code == 201
    game_id = res.get_json()["game_id"]

    # Peek secret only via DB helper path is blocked — brute-force tiny space for test:
    # Instead force win by reading through finished reveal after we patch... use many tries
    # until win by querying after each. Simpler: create, then use evaluate against revealed
    # only after loss. For unit test, keep guessing unknown — use daily mode with known secret.
    res = client.post("/api/games", json={"player_name": "Ada", "mode": "daily", "challenge_date": "2026-07-14"})
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
    res = client.post("/api/games", json={"player_name": "Ada", "mode": "daily", "challenge_date": "2026-07-14"})
    game_id = res.get_json()["game_id"]
    secret = daily_secret("2026-07-14")
    client.post(f"/api/games/{game_id}/guess", json={"guess": secret})
    scores = client.get("/api/scores").get_json()["scores"]
    assert scores and scores[0]["player_name"] == "Ada"


def test_index_renders(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"Locksmith" in res.data
