"""
Locksmith backend evaluator (LoongFlow-inspired).

Engineer reasoning
------------------
A loop without a score is just a retry timer. LoongFlow's Evaluator returns a
normalized score in [0, 1] plus feedback the next Plan can consume. Here we
derive a *composite* metric from independent backend qualities so regressions
are attributable (logic vs API vs modes vs tests vs persistence).

Metric definition
-----------------
    S = 0.30·L + 0.25·A + 0.15·M + 0.20·T + 0.10·P

    L  logic_correctness   fraction of Mastermind property checks passed
    A  api_contract        fraction of HTTP/API contract checks passed
    M  mode_coverage       fraction of classic/daily/hard shape checks passed
    T  test_suite          pytest pass rate (collected tests)
    P  persistence         1 if a won game appears in /api/scores, else 0

S ∈ [0, 1]. Default target_score = 1.0 (all gates green).
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent.parent

# Weights must sum to 1.0 — keep explicit so a TA can audit the formula.
WEIGHTS = {
    "logic_correctness": 0.30,
    "api_contract": 0.25,
    "mode_coverage": 0.15,
    "test_suite": 0.20,
    "persistence": 0.10,
}


@dataclass
class ComponentScore:
    name: str
    score: float  # 0..1
    weight: float
    passed: int
    total: int
    details: list[str] = field(default_factory=list)

    @property
    def weighted(self) -> float:
        return self.score * self.weight


@dataclass
class EvalResult:
    """Normalized evaluation result for one PES cycle (or standalone eval)."""

    score: float
    components: list[ComponentScore]
    feedback: list[str]
    met_target: bool
    target_score: float
    formula: str = (
        "S = 0.30·L + 0.25·A + 0.15·M + 0.20·T + 0.10·P  (each term ∈ [0,1])"
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "target_score": self.target_score,
            "met_target": self.met_target,
            "formula": self.formula,
            "feedback": self.feedback,
            "components": [asdict(c) for c in self.components],
        }

    def render(self) -> str:
        lines = [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "EVAL METRIC — Locksmith backend",
            self.formula,
            f"Composite score S = {self.score:.4f}  "
            f"(target ≥ {self.target_score:.2f})  "
            f"{'✓ PASS' if self.met_target else '✗ BELOW TARGET'}",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        ]
        for c in self.components:
            lines.append(
                f"  {c.name:20s}  raw={c.score:.3f}  "
                f"w={c.weight:.2f}  contrib={c.weighted:.3f}  "
                f"({c.passed}/{c.total})"
            )
            for d in c.details[:5]:
                lines.append(f"      · {d}")
        if self.feedback:
            lines.append("Feedback for next Plan:")
            for f in self.feedback:
                lines.append(f"  - {f}")
        return "\n".join(lines)


def _ratio(passed: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return max(0.0, min(1.0, passed / total))


class LocksmithEvaluator:
    """Evaluate the Locksmith backend as a LoongFlow-style fitness function."""

    def __init__(self, target_score: float = 1.0, run_pytest: bool = True):
        if not 0.0 <= target_score <= 1.0:
            raise ValueError("target_score must be in [0, 1]")
        # Guard against silent weight edits that break the formula.
        weight_sum = round(sum(WEIGHTS.values()), 6)
        if weight_sum != 1.0:
            raise RuntimeError(f"WEIGHTS must sum to 1.0, got {weight_sum}")
        self.target_score = target_score
        self.run_pytest = run_pytest

    def evaluate(self) -> EvalResult:
        components = [
            self._eval_logic(),
            self._eval_api(),
            self._eval_modes(),
            self._eval_tests() if self.run_pytest else self._skip_tests(),
            self._eval_persistence(),
        ]
        score = round(sum(c.weighted for c in components), 6)
        feedback: list[str] = []
        for c in components:
            if c.score < 1.0:
                feedback.append(
                    f"Improve {c.name}: {c.passed}/{c.total} checks "
                    f"(contrib {c.weighted:.3f}/{c.weight:.2f})"
                )
                feedback.extend(f"  detail: {d}" for d in c.details if d.startswith("FAIL"))
        if score >= self.target_score:
            feedback.append(
                "Target met — keep tests green; prefer small safe changes only."
            )
        return EvalResult(
            score=score,
            components=components,
            feedback=feedback,
            met_target=score + 1e-9 >= self.target_score,
            target_score=self.target_score,
        )

    # ----- L: logic -----
    def _eval_logic(self) -> ComponentScore:
        from game.logic import evaluate_guess, score_for_win, validate_guess

        checks: list[tuple[str, Callable[[], bool]]] = [
            ("all exact", lambda: evaluate_guess([1, 2, 3, 4], [1, 2, 3, 4]) == (4, 0)),
            (
                "all partial permute",
                lambda: evaluate_guess([1, 2, 3, 4], [4, 3, 2, 1]) == (0, 4),
            ),
            (
                "duplicate secret not overcounted",
                lambda: evaluate_guess([1, 1, 2, 3], [4, 1, 5, 6]) == (1, 0),
            ),
            (
                "duplicate guess exact-only once",
                lambda: evaluate_guess([1, 2, 3, 4], [1, 1, 1, 1]) == (1, 0),
            ),
            ("mixed pegs", lambda: evaluate_guess([1, 2, 3, 4], [1, 3, 5, 6]) == (1, 1)),
            ("classic score win@1", lambda: score_for_win(1, "classic") == 1000),
            ("hard score win@1", lambda: score_for_win(1, "hard") == 1440),
            (
                "validate rejects digit 7 in classic",
                lambda: _raises(ValueError, validate_guess, [1, 2, 3, 7]),
            ),
            (
                "hard length-5 exact",
                lambda: evaluate_guess(
                    [1, 2, 3, 4, 5], [1, 2, 3, 4, 5], digit_min=1, digit_max=8
                )
                == (5, 0),
            ),
        ]
        return self._run_checks("logic_correctness", checks)

    # ----- A: API contract -----
    def _eval_api(self) -> ComponentScore:
        from game.app import create_app
        from game.daily import daily_secret

        details: list[str] = []
        passed = 0
        total = 0

        def check(name: str, ok: bool) -> None:
            nonlocal passed, total
            total += 1
            if ok:
                passed += 1
                details.append(f"OK   {name}")
            else:
                details.append(f"FAIL {name}")

        with tempfile.TemporaryDirectory() as tmp:
            app = create_app(db_path=str(Path(tmp) / "eval.db"))
            client = app.test_client()

            h = client.get("/api/health")
            check("GET /api/health → 200 ok", h.status_code == 200 and h.get_json().get("ok") is True)

            idx = client.get("/")
            check("GET / → 200 Locksmith", idx.status_code == 200 and b"Locksmith" in idx.data)

            created = client.post(
                "/api/games",
                json={
                    "player_name": "EvalBot",
                    "mode": "daily",
                    "challenge_date": "2026-07-14",
                },
            )
            body = created.get_json() or {}
            check("POST /api/games daily → 201", created.status_code == 201)
            gid = body.get("game_id")
            check("create returns game_id", isinstance(gid, int))

            public = client.get(f"/api/games/{gid}").get_json() or {}
            check("active game hides secret", "secret" not in public)

            bad = client.post(f"/api/games/{gid}/guess", json={"guess": [1, 2]})
            check("short guess → 400", bad.status_code == 400)

            secret = daily_secret("2026-07-14")
            win = client.post(f"/api/games/{gid}/guess", json={"guess": secret})
            wbody = win.get_json() or {}
            check("winning guess → won", win.status_code == 200 and wbody.get("status") == "won")
            check("win includes score", isinstance(wbody.get("score"), int))
            check(
                "finished game reveals secret",
                (wbody.get("game") or {}).get("secret") == secret,
            )

            daily = client.get("/api/daily").get_json() or {}
            check(
                "GET /api/daily has date, no secret",
                "date" in daily and "secret" not in daily,
            )

        return ComponentScore(
            name="api_contract",
            score=_ratio(passed, total),
            weight=WEIGHTS["api_contract"],
            passed=passed,
            total=total,
            details=details,
        )

    # ----- M: modes -----
    def _eval_modes(self) -> ComponentScore:
        from game.app import create_app
        from game.logic import get_mode

        details: list[str] = []
        passed = 0
        total = 0

        def check(name: str, ok: bool) -> None:
            nonlocal passed, total
            total += 1
            if ok:
                passed += 1
                details.append(f"OK   {name}")
            else:
                details.append(f"FAIL {name}")

        classic = get_mode("classic")
        hard = get_mode("hard")
        check("classic length 4", classic.code_length == 4)
        check("hard length 5", hard.code_length == 5)
        check("hard digit_max 8", hard.digit_max == 8)
        check("hard max_guesses 12", hard.max_guesses == 12)

        with tempfile.TemporaryDirectory() as tmp:
            app = create_app(db_path=str(Path(tmp) / "modes.db"))
            client = app.test_client()
            for mode, length, dmax in (
                ("classic", 4, 6),
                ("hard", 5, 8),
                ("daily", 4, 6),
            ):
                res = client.post(
                    "/api/games", json={"player_name": "M", "mode": mode}
                )
                body = res.get_json() or {}
                check(
                    f"{mode} create shape",
                    res.status_code == 201
                    and body.get("code_length") == length
                    and body.get("digit_max") == dmax,
                )

        return ComponentScore(
            name="mode_coverage",
            score=_ratio(passed, total),
            weight=WEIGHTS["mode_coverage"],
            passed=passed,
            total=total,
            details=details,
        )

    # ----- T: pytest -----
    def _eval_tests(self) -> ComponentScore:
        details: list[str] = []
        try:
            proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "tests/",
                    "-q",
                    "--tb=no",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=120,
                env={**dict(**__import__("os").environ), "PYTHONPATH": str(ROOT)},
            )
            out = (proc.stdout or "") + (proc.stderr or "")
            # pytest -q summary like "19 passed" or "2 failed, 17 passed"
            import re

            passed_m = re.search(r"(\d+)\s+passed", out)
            failed_m = re.search(r"(\d+)\s+failed", out)
            passed = int(passed_m.group(1)) if passed_m else 0
            failed = int(failed_m.group(1)) if failed_m else 0
            total = passed + failed
            if total == 0:
                details.append("FAIL could not parse pytest summary")
                details.append(out[-500:])
                return ComponentScore(
                    name="test_suite",
                    score=0.0,
                    weight=WEIGHTS["test_suite"],
                    passed=0,
                    total=1,
                    details=details,
                )
            details.append(f"OK   pytest: {passed} passed, {failed} failed")
            if failed:
                details.append(f"FAIL {failed} test(s) failing")
            return ComponentScore(
                name="test_suite",
                score=_ratio(passed, total),
                weight=WEIGHTS["test_suite"],
                passed=passed,
                total=total,
                details=details,
            )
        except Exception as exc:  # noqa: BLE001
            details.append(f"FAIL pytest invocation: {exc}")
            return ComponentScore(
                name="test_suite",
                score=0.0,
                weight=WEIGHTS["test_suite"],
                passed=0,
                total=1,
                details=details,
            )

    def _skip_tests(self) -> ComponentScore:
        return ComponentScore(
            name="test_suite",
            score=1.0,
            weight=WEIGHTS["test_suite"],
            passed=0,
            total=0,
            details=["SKIP pytest (run_pytest=False)"],
        )

    # ----- P: persistence -----
    def _eval_persistence(self) -> ComponentScore:
        from game.app import create_app
        from game.daily import daily_secret

        details: list[str] = []
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "persist.db"
            app = create_app(db_path=str(db))
            client = app.test_client()
            gid = client.post(
                "/api/games",
                json={
                    "player_name": "Persist",
                    "mode": "daily",
                    "challenge_date": "2026-07-14",
                },
            ).get_json()["game_id"]
            secret = daily_secret("2026-07-14")
            client.post(f"/api/games/{gid}/guess", json={"guess": secret})

            # Recreate app against same DB — scores must survive "restart".
            app2 = create_app(db_path=str(db))
            scores = app2.test_client().get("/api/scores").get_json().get("scores") or []
            ok = any(s.get("player_name") == "Persist" for s in scores)
            details.append(
                "OK   win survives app recreate" if ok else "FAIL score missing after recreate"
            )
            return ComponentScore(
                name="persistence",
                score=1.0 if ok else 0.0,
                weight=WEIGHTS["persistence"],
                passed=1 if ok else 0,
                total=1,
                details=details,
            )

    def _run_checks(
        self, name: str, checks: list[tuple[str, Callable[[], bool]]]
    ) -> ComponentScore:
        details: list[str] = []
        passed = 0
        for label, fn in checks:
            try:
                ok = bool(fn())
            except Exception as exc:  # noqa: BLE001
                ok = False
                details.append(f"FAIL {label}: {exc}")
            else:
                details.append(("OK   " if ok else "FAIL ") + label)
            if ok:
                passed += 1
        total = len(checks)
        return ComponentScore(
            name=name,
            score=_ratio(passed, total),
            weight=WEIGHTS[name],
            passed=passed,
            total=total,
            details=details,
        )


def _raises(exc_type: type[BaseException], fn: Callable[..., Any], *args: Any) -> bool:
    try:
        fn(*args)
    except exc_type:
        return True
    except Exception:
        return False
    return False


def save_eval_report(result: EvalResult, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result.to_dict(), indent=2) + "\n", encoding="utf-8")
    (path.parent / "latest_eval.md").write_text(result.render() + "\n", encoding="utf-8")
    return path
