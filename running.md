# running.md — how to run this repository

## What exists today

This repository currently ships the **loop engineering system** (Plan–Execute–Summary)
used to satisfy the loop.pdf requirement to use loop code with an AI assistant.

The interactive product (base system + extension) will be built *through* that
loop in later stages. When the product lands, update this file with exact start
commands, ports, and sample clicks a TA should perform.

## Prerequisites

- Python 3.11+ (conda env `loop` is fine)
- Git
- Optional for live agent loops: GitHub Copilot CLI and/or Cursor Agent CLI

## Setup

```bash
cd /path/to/Assign-4
conda activate loop   # if using conda
pip install -r requirements.txt
pip install pytest
chmod +x loop.sh
```

## Run the loop (offline smoke test)

```bash
./loop.sh -m build --backend dry_run -n 1
python -m loop_engine stage status
pytest tests/ -q
```

Expected: dry_run prints a prompt preview, writes experiential memory under
`.loop_workspace/`, appends to `prompts.txt`, and exits after seeing `DONE`.

## Run the loop with a real coding agent

1. Set `agent.backend` in `config.yaml` to `copilot` or `cursor`, **or** pass
   `--backend` on the CLI.
2. Ensure the CLI is installed and authenticated.
3. Example:

```bash
./loop.sh -m plan --backend copilot -n 3
./loop.sh -m build --backend copilot
```

## Assignment stage workflow (rubric)

```bash
python -m loop_engine stage start step1_base specify
# … produce specs …
python -m loop_engine stage complete step1_base specify --notes "base specs v1"

python -m loop_engine stage start step1_base review
# … review …
python -m loop_engine stage complete step1_base review --notes "review pass"

python -m loop_engine stage start step1_base plan
./loop.sh -m plan --backend <your-backend> -n 5
python -m loop_engine stage complete step1_base plan --notes "plan ready"

python -m loop_engine stage start step1_base build
./loop.sh -m build --backend <your-backend>
python -m loop_engine stage complete step1_base build --notes "base system done"

# Repeat pattern for step2_extension
```

## Product app (to be filled in)

<!-- TA: replace this section once Step 1 build completes.
Example:
```bash
./script/server
open http://127.0.0.1:5000
```
-->

_Pending — product not built yet._
