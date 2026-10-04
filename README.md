# Custom Product Vision Inspector

A configurable AI inspection platform where businesses upload product images, define packaging and label requirements, and generate product-specific computer-vision workflows.

## Phase 1 MVP

This repository contains the working Phase 1 end-to-end flow plus optional Phase 2 computer-vision support:

- A responsive Next.js frontend for the dashboard, product setup, inspection workflow, and results review
- A Python FastAPI backend that exposes typed inspection APIs and a mock inspection engine
- Clear separation between mock and real-model inspection results

## Phase 2 — Experimental label detection

The backend can run either the clearly identified mock engine (default) or a configured YOLO detector. The supplied
[`kdata/labels.v6i.yolov8.zip`](./kdata/labels.v6i.yolov8.zip) contains 735 paired images and YOLO annotations for
51 numeric vial-label classes. It is suitable for experimenting with label-region detection and label-class
recognition, but is too small and imbalanced to assume production accuracy. Dataset metadata attributes it to
[VialsLabel / labels-ud0wc](https://universe.roboflow.com/vialslabel-hkq5w/labels-ud0wc/dataset/6) under CC BY 4.0.
It does not annotate product bodies, caps, logos, or damage; the YOLO engine reports those checks as unverifiable
rather than inferring success.

Install the optional computer-vision dependencies from `backend/`:

```bash
pip install -r requirements-vision.txt
python scripts/train_label_detector.py --epochs 100
```

Training starts from the Ultralytics `yolov8n.pt` checkpoint and downloads it when needed. The dataset is extracted
to a temporary directory; the trained weights are written under `backend/models/label-detector/`. Review the
validation metrics before using a model. To use the trained model, set these backend environment variables:

```bash
INSPECTION_ENGINE=yolo
YOLO_MODEL_PATH=/absolute/path/to/backend/models/label-detector/yolov8-labels/weights/best.pt
YOLO_CONFIDENCE_THRESHOLD=0.25
```

YOLO mode requires a product image uploaded by the setup screen and currently accepts image data URLs only. Results
identify the active engine and include normalized label bounding boxes. Leave `INSPECTION_ENGINE` unset to continue
using mock mode.

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
