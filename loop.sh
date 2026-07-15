#!/usr/bin/env bash
# loop.sh — thin shell entrypoint for the PES loop engine
#
# Engineer reasoning:
# The class tutorial (ralph-wiggum) teaches muscle memory around `./loop.sh -m plan`.
# Students should get that same UX. The *brains* live in Python (testable,
# typed, memory + stage tracking). This script is deliberately boring: parse
# flags → call `python -m loop_engine run …`.
#
# Usage:
#   ./loop.sh                         # build mode, config defaults
#   ./loop.sh -m plan -n 5            # plan mode, max 5 iterations
#   ./loop.sh -m build --backend copilot
#   ./loop.sh -h

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

MODE="build"
MAX_ITERATIONS=""
BACKEND=""
STAGE=""
CONFIG=""
COMMAND="run"
EXTRA=()

usage() {
  cat <<'EOF'
Usage: ./loop.sh [options]
       ./loop.sh eval [--no-pytest]
       ./loop.sh automate [-n N] [-b backend]

Options:
  -m, --mode <plan|build|execute|specify|review|summary>
  -n, --max <number>          Max iterations (0 = unlimited)
  -b, --backend <name>        dry_run | echo | copilot
  -s, --stage <name>          Assignment stage label (defaults to mode)
  -c, --config <file>         Path to config.yaml
  -h, --help                  Show help

Examples:
  ./loop.sh -m plan -n 3
  ./loop.sh -m build --backend dry_run
  ./loop.sh eval
  ./loop.sh automate -n 3 --backend dry_run
EOF
}

# Subcommands: eval | automate (EvalMetric / backend automation)
if [[ "${1:-}" == "eval" || "${1:-}" == "automate" ]]; then
  COMMAND="$1"
  shift
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    -m|--mode) MODE="$2"; shift 2 ;;
    -n|--max) MAX_ITERATIONS="$2"; shift 2 ;;
    -b|--backend) BACKEND="$2"; shift 2 ;;
    -s|--stage) STAGE="$2"; shift 2 ;;
    -c|--config) CONFIG="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) EXTRA+=("$1"); shift ;;
  esac
done

# Prefer an explicitly set PYTHON, then `python` (conda/venv), then `python3`.
# Engineer note: on macOS, bare `python3` often points at a system install that
# does *not* have our pip packages — activate the env, don't hardcode python3.
if [[ -z "${PYTHON:-}" ]]; then
  if command -v python >/dev/null 2>&1; then
    PYTHON="$(command -v python)"
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON="$(command -v python3)"
  else
    echo "Error: python not found. Activate your env (e.g. conda activate loop)." >&2
    exit 1
  fi
fi
if ! command -v "$PYTHON" >/dev/null 2>&1 && [[ ! -x "$PYTHON" ]]; then
  echo "Error: PYTHON=$PYTHON is not executable." >&2
  exit 1
fi

if [[ "$COMMAND" == "eval" ]]; then
  CMD=("$PYTHON" -m loop_engine eval)
elif [[ "$COMMAND" == "automate" ]]; then
  CMD=("$PYTHON" -m loop_engine automate)
  [[ -n "$MAX_ITERATIONS" ]] && CMD+=(--max "$MAX_ITERATIONS")
  [[ -n "$BACKEND" ]] && CMD+=(--backend "$BACKEND")
else
  CMD=("$PYTHON" -m loop_engine run --mode "$MODE")
  [[ -n "$MAX_ITERATIONS" ]] && CMD+=(--max "$MAX_ITERATIONS")
  [[ -n "$BACKEND" ]] && CMD+=(--backend "$BACKEND")
  [[ -n "$STAGE" ]] && CMD+=(--stage "$STAGE")
fi
[[ -n "$CONFIG" ]] && CMD+=(--config "$CONFIG")
# With `set -u`, empty arrays error on "${EXTRA[@]}" in some bash versions —
# only append when the user actually passed trailing args.
if ((${#EXTRA[@]})); then
  CMD+=("${EXTRA[@]}")
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Loop Engineering (PES + EvalMetric)"
echo "Command: $COMMAND"
[[ "$COMMAND" == "run" ]] && echo "Mode:    $MODE"
echo "Python:  $PYTHON ($("$PYTHON" --version 2>&1))"
echo "Branch:  $(git branch --show-current 2>/dev/null || echo n/a)"
[[ -n "$MAX_ITERATIONS" ]] && echo "Max:     $MAX_ITERATIONS"
[[ -n "$BACKEND" ]] && echo "Backend: $BACKEND"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# PYTHONPATH so `import loop_engine` works without an editable install.
export PYTHONPATH="${ROOT}${PYTHONPATH:+:$PYTHONPATH}"
exec "${CMD[@]}"