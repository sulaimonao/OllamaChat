# Multimodal & Browser Quickstart

This repository exposes lightweight health checks for the multimodal and
live-browsing subsystems. They can be queried without starting the full model
stack and are intended as smoke tests for deployments.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

## Run

```bash
cd backend
uvicorn app:app --reload
```

## Smoke Tests

```bash
curl http://localhost:8000/health/mm
curl http://localhost:8000/health/browser
```

## Automated Tests

```bash
cd backend
pytest -q
```

Both commands should return `{"status": "ok"}` and the pytest suite should
report `2 passed`.
