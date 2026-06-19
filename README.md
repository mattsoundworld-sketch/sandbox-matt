# sandbox-matt
My playground for learning

## Learning Lanes

Use these top-level folders as maturity lanes.

- `fundamentals`: focused concept drills and small exercises.
- `experiments`: rapid tests and throwaway probes.
- `use-cases`: practical workflows with clear problem statements.
- `libraries`: reusable modules promoted from successful experiments.
- `apps`: composed applications that call reusable modules.
- `evals`: datasets and scripts for quality regression checks.
- `data/raw` and `data/processed`: source data and generated artifacts.
- `archive`: retired or superseded material.

## Phase 1 Starter

Reusable baseline package:

- `libraries/ai_stack/contracts.py`
- `libraries/ai_stack/json_contracts.py`
- `libraries/ai_stack/model_client.py`
- `libraries/ai_stack/retrieval.py`

Composable starter app:

- `apps/starter_chat/main.py`

## Python Environment (Cross-Location)

This repo is normalized to Python 3.14 so the same setup works on both PCs.

1. Install Python 3.14 if needed.
2. From repo root, run `./scripts/setup-venv.ps1`.
3. Activate with `./.venv/Scripts/Activate.ps1`.

Notes:
- `.python-version` is set to `3.14`.
- The setup script recreates `.venv` and installs root dependencies from `requirements.txt`.

## Run Starter App

From repo root:

```powershell
python -m apps.starter_chat.main
```

## Run Tests

From repo root:

```powershell
pytest -q
```
