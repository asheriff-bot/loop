"""
Locksmith Flask application.

Run:
  python -m game.app
  → http://127.0.0.1:5055
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request

from game.db import Database
from game.logic import (
    MAX_GUESSES,
    CODE_LENGTH,
    evaluate_guess,
    generate_secret,
    score_for_win,
    validate_guess,
)

ROOT = Path(__file__).resolve().parent


def create_app(db_path: str | None = None) -> Flask:
    app = Flask(
        __name__,
        template_folder=str(ROOT / "templates"),
        static_folder=str(ROOT / "static"),
    )
    db = Database(db_path or os.environ.get("LOCKSMITH_DB"))

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/health")
    def health():
        return jsonify({"ok": True, "service": "locksmith"})

    @app.post("/api/games")
    def create_game():
        payload = request.get_json(silent=True) or {}
        player_name = str(payload.get("player_name") or "Player")[:40]
        mode = str(payload.get("mode") or "classic")
        challenge_date = payload.get("challenge_date")

        if mode == "daily":
            # Daily secret is deterministic from UTC date (extension helper).
            from game.daily import daily_secret, today_utc

            challenge_date = challenge_date or today_utc()
            secret = daily_secret(challenge_date)
        else:
            secret = generate_secret()
            mode = "classic"
            challenge_date = None

        game_id = db.create_game(
            player_name=player_name,
            secret=secret,
            mode=mode,
            challenge_date=challenge_date,
        )
        return jsonify(
            {
                "game_id": game_id,
                "max_guesses": MAX_GUESSES,
                "code_length": CODE_LENGTH,
                "mode": mode,
                "challenge_date": challenge_date,
                "player_name": player_name,
            }
        ), 201

    @app.get("/api/games/<int:game_id>")
    def get_game(game_id: int):
        game = db.get_game(game_id)
        if game is None:
            return jsonify({"error": "Game not found"}), 404
        return jsonify(_public_game(game))

    @app.post("/api/games/<int:game_id>/guess")
    def post_guess(game_id: int):
        game = db.get_game(game_id)
        if game is None:
            return jsonify({"error": "Game not found"}), 404
        if game["status"] != "active":
            return jsonify({"error": "Game already finished", "game": _public_game(game)}), 409

        payload = request.get_json(silent=True) or {}
        raw_guess = payload.get("guess")
        try:
            guess = validate_guess(raw_guess or [])
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        exact, partial = evaluate_guess(game["secret"], guess)
        guesses_used = int(game["guesses_used"]) + 1
        status = "active"
        score = None
        if exact == CODE_LENGTH:
            status = "won"
            score = score_for_win(guesses_used)
        elif guesses_used >= MAX_GUESSES:
            status = "lost"

        db.add_guess(
            game_id=game_id,
            guess=guess,
            exact=exact,
            partial=partial,
            status=status,
            score=score,
            guesses_used=guesses_used,
        )
        updated = db.get_game(game_id)
        assert updated is not None
        body: dict[str, Any] = {
            "exact": exact,
            "partial": partial,
            "guesses_used": guesses_used,
            "remaining": MAX_GUESSES - guesses_used,
            "status": status,
            "game": _public_game(updated),
        }
        if status == "won":
            body["score"] = score
        return jsonify(body)

    @app.get("/api/scores")
    def scores():
        mode = request.args.get("mode")
        return jsonify({"scores": db.top_scores(limit=10, mode=mode)})

    return app


def _public_game(game: dict[str, Any]) -> dict[str, Any]:
    """Strip secret while active; reveal after finish for learning."""
    public = {
        "id": game["id"],
        "player_name": game["player_name"],
        "status": game["status"],
        "guesses_used": game["guesses_used"],
        "score": game["score"],
        "max_guesses": MAX_GUESSES,
        "code_length": CODE_LENGTH,
        "mode": game.get("mode") or "classic",
        "challenge_date": game.get("challenge_date"),
        "guesses": game.get("guesses") or [],
        "created_at": game.get("created_at"),
        "finished_at": game.get("finished_at"),
    }
    if game["status"] != "active":
        public["secret"] = game["secret"]
    return public


def main() -> None:
    port = int(os.environ.get("PORT", "5055"))
    app = create_app()
    # threaded=True so UI + API feel snappy during local play
    app.run(host="127.0.0.1", port=port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
