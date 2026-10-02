# Custom Product Vision Inspector

A configurable AI inspection platform where businesses upload product images, define packaging and label requirements, and generate product-specific computer-vision workflows.

## Phase 1 MVP

This repository contains a working Phase 1 end-to-end prototype:

- A responsive Next.js frontend for the dashboard, product setup, inspection workflow, and results review
- A Python FastAPI backend that exposes typed inspection APIs and a mock inspection engine
- Clear separation between mock inspection results and future real model inference

## Project structure

- `frontend/` — Next.js + React + TypeScript UI
- `backend/` — FastAPI service and mock inspection logic
- `docs/AI/PROJECT_GUIDE.md` — project rules and workflow requirements

## Run locally

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Backend:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The frontend expects the backend at http://localhost:8000/api.
