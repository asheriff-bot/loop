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

from game.daily import daily_secret, today_utc
from game.db import Database
from game.logic import evaluate_guess, generate_secret, get_mode, score_for_win, validate_guess

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

    @app.get("/api/daily")
    def daily_info():
        return jsonify({"date": today_utc(), "mode": "daily"})

    @app.post("/api/games")
    def create_game():
        payload = request.get_json(silent=True) or {}
        player_name = str(payload.get("player_name") or "Player")[:40]
        mode_raw = str(payload.get("mode") or "classic").lower()
        challenge_date = payload.get("challenge_date")

        try:
            cfg = get_mode(mode_raw)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        if cfg.name == "daily":
            challenge_date = challenge_date or today_utc()
            secret = daily_secret(challenge_date)
            mode = "daily"
        else:
            secret = generate_secret(cfg.name)
            mode = cfg.name
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
                "max_guesses": cfg.max_guesses,
                "code_length": cfg.code_length,
                "digit_min": cfg.digit_min,
                "digit_max": cfg.digit_max,
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

        cfg = get_mode(game.get("mode") or "classic")
        payload = request.get_json(silent=True) or {}
        raw_guess = payload.get("guess")
        try:
            guess = validate_guess(
                raw_guess or [],
                code_length=cfg.code_length,
                digit_min=cfg.digit_min,
                digit_max=cfg.digit_max,
            )
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        exact, partial = evaluate_guess(
            game["secret"],
            guess,
            digit_min=cfg.digit_min,
            digit_max=cfg.digit_max,
        )
        guesses_used = int(game["guesses_used"]) + 1
        status = "active"
        score = None
        if exact == cfg.code_length:
            status = "won"
            score = score_for_win(guesses_used, cfg.name)
        elif guesses_used >= cfg.max_guesses:
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
            "remaining": cfg.max_guesses - guesses_used,
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
    cfg = get_mode(game.get("mode") or "classic")
    public = {
        "id": game["id"],
        "player_name": game["player_name"],
        "status": game["status"],
        "guesses_used": game["guesses_used"],
        "score": game["score"],
        "max_guesses": cfg.max_guesses,
        "code_length": cfg.code_length,
        "digit_min": cfg.digit_min,
        "digit_max": cfg.digit_max,
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
    app.run(host="127.0.0.1", port=port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
