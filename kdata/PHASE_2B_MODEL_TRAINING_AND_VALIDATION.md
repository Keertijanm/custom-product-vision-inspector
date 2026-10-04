# Phase 2B — Train, Evaluate, and Verify the Label Detector

This runbook takes the project from the supplied YOLO dataset to an experimentally
evaluated model and a verified backend inference path. It is written for a
developer or an AI coding session working in this repository.

> **Current state (2026-10-04):** a grouped one-class YOLOv8n label-region
> model completed 10 CPU epochs at 320px. Independent grouped validation and a
> one-time grouped test scored mAP50 0.995 and mAP50-95 0.941/0.944. This is a
> promising localization prototype on this dataset, not production readiness:
> the source is one camera/session and has no label-absent examples. The backend
> remains in mock mode pending external-data validation.

## 1. What this model can and cannot do

The archive [`labels.v6i.yolov8.zip`](./labels.v6i.yolov8.zip) is attributed in
its metadata to [VialsLabel / labels-ud0wc, version 6](https://universe.roboflow.com/vialslabel-hkq5w/labels-ud0wc/dataset/6)
under **CC BY 4.0**. The checked archive has 735 paired images and YOLO text
annotations, split into:

| Split | Images / label files |
| --- | ---: |
| Train | 512 |
| Validation | 149 |
| Test (held out) | 74 |

It declares 51 classes with numeric names. Classes are imbalanced, with some
represented by very few examples. The annotations are suitable for experiments
in vial-label region detection and numeric label-class recognition. They do not
annotate product bodies, caps, logos, or damage. The current YOLO service
therefore cannot verify those checks and must not be described as a complete
product inspection system.

The numbers above are a dataset inventory, not evidence of model quality. A
human should confirm what the numeric classes mean for the intended product
before treating class predictions as useful product identification.

### Capture-sequence leakage

The image filenames contain capture timestamps. Grouping consecutive frames
with gaps of at most two seconds found 45 capture bursts; 44 bursts cross the
provided split boundaries, containing 728 of the 735 images. In other words,
near-consecutive frames from the same capture sequence appear in train,
validation, and often test. Scores measured on these original partitions are
not independent generalization estimates. This also invalidates the earlier
held-out-test readiness interpretation.

The training script's `--group-captures` option now rebuilds temporary splits
by capture burst (70% train, 15% validation, 15% test) before training. It
requires timestamped filenames in the supplied naming format. This is a better
experiment split, but all images still come from one dated source/camera; a
final claim requires a new holdout collected in independent sessions and
conditions. Also, every supplied image contains a labeled object. Collect
label-absent, obscured, and out-of-scope examples to measure false detections
before using the model to reject or pass real products.

### Local class-support audit

The extracted local dataset was counted by annotated image and class. Each of
the 735 label files contains exactly one object, so image support and object
support are equal for this dataset.

| Split | Images / objects | Classes with 0 support | 1-4 | 5-9 | 10+ | Highest support |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Train | 512 | 1 | 11 | 6 | 33 | 22 |
| Validation | 149 | 5 | 31 | 15 | 0 | 8 |
| Test | 74 | 11 | 40 | 0 | 0 | 4 |

In training, class `30` has no examples. The other classes below five training
images are `34`, `35`, `36`, `37`, `38`, `41`, `42`, `43`, `44`, `46`, and
`47`. Validation has no class with more than eight examples, and every class
represented in test has at most four. Per-class validation and test metrics
will therefore be very noisy; absence from a split must not be interpreted as
good performance. The numeric names also need domain-owner confirmation.

### Recommended retraining decision

First confirm the intended task:

- If the goal is only to locate vial labels, make a one-class dataset by
  mapping each existing label class to `label` while preserving its box. This
  uses the available annotations for the task they support and avoids asking
  a 51-class model to learn identities from very sparse examples. The training
  script supports this as an explicit opt-in mode:

  ```bash
  python scripts/train_label_detector.py --single-class --group-captures --epochs 10 --imgsz 320 --device cpu
  ```

  This saves to `backend/models/label-detector/yolov8-label-regions-grouped/`,
  separate from the earlier runs. The four-epoch ungrouped checkpoint scored
  precision 0.956, recall 0.966, mAP50 0.988, and mAP50-95 0.811 on the original
  validation split, but those values are contaminated by capture overlap. The
  grouped 10-epoch run scored precision 0.999, recall 1.000, mAP50 0.995, and
  mAP50-95 0.940 during training. Independent evaluation reproduced precision
  0.999, recall 1.000, mAP50 0.995, and mAP50-95 0.941 on 110 grouped validation
  images. A one-time evaluation on 113 grouped test images scored precision
  1.000, recall 1.000, mAP50 0.995, and mAP50-95 0.944. Review these plots, but
  do not treat this same-source dataset as an external readiness test.

  Validate a saved grouped checkpoint on validation data with:

  ```bash
  python scripts/validate_label_detector.py --weights models/label-detector/yolov8-label-regions-grouped/weights/best.pt --split valid --imgsz 320 --single-class --group-captures --device cpu
  ```

  The grouped checkpoint's one-time test evaluation is retained under
  `runs/label-detector-evaluation/yolov8-label-regions-grouped-test/`. Do not
  use it to tune another model; obtain new independent-session data for a final
  generalization check.
- If the goal is to identify a product/SKU, confirm the class-to-product map
  first, then collect more independent images per class. A reasonable planning
  floor for the next experiment is 20-30 varied training images and at least 5
  validation images per class; this is a data-collection target, not a model
  acceptance threshold. Include different capture conditions and product
  instances, and split by source/capture group to avoid near-duplicate leakage.

After label localization is validated, treat product/SKU reading as a separate
stage: crop the detected label region, run OCR, and normalize the recognized
text against a human-confirmed product/SKU catalog. Measure exact SKU match and
abstention/error rates on a separate labeled set; a correct label box does not
prove that the product text was read correctly. A visual classifier is an
alternative only if the use case has a confirmed finite SKU set and enough
representative labeled examples per SKU.

Do not try to solve the rare-class problem by duplicating images across splits
or by aggressive oversampling before the class map and labels are audited.
Choose the experiment using grouped training and validation only, save each run
under a distinct output directory, and keep the configuration fixed before
final testing. The provided test split is contaminated by the same capture
overlap and has already been inspected, so it is not a blind final set. Collect
a fresh, representative holdout for a future final claim.

## 2. Responsibilities and completion gates

| Work | Can be automated by a developer/AI session | Human responsibility / decision |
| --- | --- | --- |
| Environment and dependency setup | Create/use the backend virtual environment, install the optional requirements, run tests and report errors. | Choose CPU vs. GPU based on available hardware and decide whether the time and disk cost of model dependencies are acceptable. |
| Dataset preparation | Check archive integrity and split/label pairing; use the training script to prepare a temporary YOLO dataset. | Confirm dataset provenance, CC BY 4.0 attribution requirements, class meaning, and appropriateness for the target inspection images. |
| Training | Run the training script, retain logs/weights, and report the run directory and validation metrics. | Decide whether the resource/time budget and results justify further experiments. |
| Held-out evaluation | Run the final weights on `test` and preserve the metrics/plots. | Review per-class performance, representative false positives/negatives, and pre-agreed acceptance thresholds. Do not let aggregate metrics alone approve a model. |
| Backend configuration | Set process environment variables, start the service, submit an image, and check the response schema and detection boxes. | Supply a representative image that may be processed locally and confirm whether the returned class is semantically correct. |
| Promotion/use | Keep the model explicitly experimental unless a release process is requested. | Approve any production/demo claim and decide what checks the model is allowed to influence. |

Do not upload private or customer product images to external services for
debugging. Keep the dataset, model weights, and evaluation artifacts local
unless their owner has explicitly approved sharing.

## 3. Prerequisites and environment

Run these commands from the repository root unless a command says otherwise.

1. Use Python 3.10+ (the existing backend environment in this workspace uses
   Python 3.12). Make sure there is adequate free disk space for PyTorch,
   downloaded model weights, training outputs, and the extracted temporary
   dataset.
2. For GPU training, check that an NVIDIA GPU and driver are available with
   `nvidia-smi`. Install the PyTorch build appropriate to the host by following
   the official [PyTorch install selector](https://pytorch.org/get-started/locally/).
   CPU training is supported but may be considerably slower.
3. Create and activate the backend virtual environment, then install the
   project's optional vision dependencies:

   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install --upgrade pip
   python -m pip install -r requirements-vision.txt
   ```

   On Windows PowerShell, activate with
   `.\.venv\Scripts\Activate.ps1`. If the PyTorch wheel selected for the
   machine is not the one resolved by the optional requirements, install the
   correct PyTorch build using the official selector before installing
   `requirements-vision.txt`.
4. Verify the runtime and script are available:

   ```bash
   python -c "import torch, ultralytics; print('torch', torch.__version__, 'cuda', torch.cuda.is_available(), 'ultralytics', ultralytics.__version__)"
   python scripts/train_label_detector.py --help
   ```

   A false CUDA result is not a blocker for CPU training. Resolve package,
   platform, or driver errors before starting a long run.

The optional packages are declared in
[`backend/requirements-vision.txt`](../backend/requirements-vision.txt). They
are deliberately separate from the default lightweight backend requirements.

## 4. Check and train

The training script defaults to the supplied archive, starts from the
Ultralytics `yolov8n.pt` checkpoint, and saves runs below
`backend/models/label-detector/`. The initial run can download the pretrained
checkpoint and needs internet access unless that checkpoint is already
available locally. Training extracts the dataset to a temporary directory and
removes that temporary copy when the run ends.

From `backend/`, start with a short smoke run before a longer run:

```bash
python scripts/train_label_detector.py --epochs 2 --device cpu
```

If the smoke run starts and saves artifacts successfully, run a full baseline.
The script defaults to 100 epochs and image size 640; specify a device only
when appropriate (`cpu` or `0` are examples):

```bash
python scripts/train_label_detector.py --epochs 100 --imgsz 640 --device 0
```

Omit `--device 0` to let Ultralytics select the available device. For CPU-only
training, use `--device cpu`. A custom archive, output root, or pretrained
checkpoint can be supplied with `--archive`, `--output`, or `--base-model`.
Prefer a supported pretrained checkpoint; document any change so experiments
remain comparable.

At completion, record the printed absolute `best.pt` path. It will normally
look like:

```text
backend/models/label-detector/yolov8-labels/weights/best.pt
```

The actual run directory may differ if there are multiple or resumed runs.
Use the path printed by the script, not an assumed path. Training outputs,
weights, and run logs are ignored by Git and should not be committed by
default.

### Training gate

Before evaluating, verify that:

- Training completed without an exception and produced `weights/best.pt`.
- The run contains validation results (normally `results.csv` and plots).
- The saved model has the expected 51 classes.
- Validation results and class-wise performance are inspected; a completed run
  alone does not prove usefulness.

If the run fails, keep the error and relevant environment/package versions in
the handoff notes. Do not silently switch model architectures or discard failed
runs.

## 5. Evaluate once on the held-out test split

Use the `test` split only after the training configuration and checkpoint have
been selected using training and validation data. Do not tune epochs,
confidence, augmentations, or model choice repeatedly against the test metrics.
If test results are used to change the model, the test set is no longer an
unbiased final evaluation; obtain a new held-out set for the final claim.

The following command prepares the dataset in a temporary directory and
evaluates the chosen weights directly on its declared test split. Run it from
`backend/`, replace the checkpoint path with the absolute path printed by the
training script, and choose `cpu` or `0` as appropriate:

```bash
WEIGHTS="/absolute/path/to/backend/models/label-detector/yolov8-labels/weights/best.pt" \
DEVICE="cpu" \
python - <<'PY'
import os
import tempfile
from pathlib import Path

from ultralytics import YOLO
from scripts.train_label_detector import DEFAULT_ARCHIVE, extract_dataset

weights = Path(os.environ["WEIGHTS"])
if not weights.is_file():
    raise FileNotFoundError(f"Model weights not found: {weights}")

with tempfile.TemporaryDirectory(prefix="product-vision-test-") as temporary_directory:
    data_yaml = extract_dataset(DEFAULT_ARCHIVE, Path(temporary_directory))
    model = YOLO(str(weights))
    metrics = model.val(
        data=str(data_yaml),
        split="test",
        imgsz=640,
        device=os.environ.get("DEVICE", "cpu"),
        plots=True,
        project="runs/phase2b-evaluation",
        name="labels-held-out-test",
        exist_ok=True,
    )
    print("Held-out test metrics:", metrics.results_dict)
    print("Per-class mAP:", metrics.box.maps)
    print("Evaluation artifacts:", metrics.save_dir)
PY
```

Evaluation plots and files are saved under
`backend/runs/phase2b-evaluation/labels-held-out-test/`. Preserve the run
directory locally and record its path. It is ignored by Git; share artifacts
only if dataset/model permissions allow.

### How to interpret the evaluation

Review, at minimum:

- **mAP50-95 and mAP50:** localization/classification quality at stricter and
  looser IoU thresholds. Neither number alone establishes suitability.
- **Precision and recall:** false alarms versus missed labels; which matters
  more depends on the inspection workflow.
- **Per-class AP and support:** aggregate scores can hide classes with no
  examples or very poor performance. Compare against the archive's class
  counts.
- **Confusion matrix and test plots:** look for class confusions, duplicate or
  misplaced boxes, and misses on small/blurred/rotated labels.
- **Representative errors:** inspect true positives, false positives, and false
  negatives by opening the plots/images, not only the printed summary.

The test split contains only 74 images and the classes are imbalanced, so
per-class estimates may be noisy. Establish acceptance criteria before
reviewing the test results. If metrics are weak or classes have inadequate
support, report that clearly and collect/label more representative data rather
than presenting the detector as reliable.

The earlier 51-class report captured precision 0.0406, recall 0.1958, mAP50
0.0545, and mAP50-95 0.0541 on the supplied test partition. Its PR curve rounds
mAP50 to 0.055. Because the supplied partitions share capture bursts, these
numbers are retained only as historical run output, not as an independent test
of generalization.

The numeric class names are opaque. Have a human or the dataset owner confirm
the class-to-product mapping before claiming that a detected class identifies a
specific SKU, drug, or brand. Dataset attribution must be retained in derived
model/demo documentation under the dataset's CC BY 4.0 terms.

Official references:

- [Ultralytics detection training](https://docs.ultralytics.com/modes/train/)
- [Ultralytics validation](https://docs.ultralytics.com/modes/val/)
- [Ultralytics prediction](https://docs.ultralytics.com/modes/predict/)
- [PyTorch local installation selector](https://pytorch.org/get-started/locally/)
- [Source dataset and attribution](https://universe.roboflow.com/vialslabel-hkq5w/labels-ud0wc/dataset/6)

## 6. Configure and verify backend inference

Do this only after selecting a checkpoint and reviewing its held-out test
results. `INSPECTION_ENGINE=yolo` loads the weights at backend startup; invalid
configuration or missing optional packages should fail startup rather than
silently falling back to mock mode.

From `backend/`, activate the environment and export the actual absolute
checkpoint path:

```bash
source .venv/bin/activate
export INSPECTION_ENGINE=yolo
export YOLO_MODEL_PATH="/absolute/path/to/backend/models/label-detector/yolov8-labels/weights/best.pt"
export YOLO_CONFIDENCE_THRESHOLD=0.25
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Use PowerShell equivalents (`$env:INSPECTION_ENGINE = "yolo"` etc.) on Windows.
The confidence threshold is configurable between 0 and 1. Start at 0.25 for
the existing default, then choose a threshold using validation data and the
desired precision/recall tradeoff. Do not select it by repeatedly optimizing
against the held-out test set.

In a second terminal, verify health:

```bash
curl --fail http://localhost:8000/api/health
```

Then verify inference using the frontend: start it with `cd frontend && npm
run dev`, set `NEXT_PUBLIC_API_URL` to the backend API URL if needed, upload a
representative image in Product Setup, run the inspection, and open Results.
YOLO mode requires a base64 image data URL from an uploaded image; a remote
image URL is not accepted. The backend rejects uploads larger than 15 MB.

Check the response/UI for all of the following:

- `inspection_mode` is `yolo`, not `mock`.
- Detections are labeled with the model's numeric class names and have
  confidence values in the 0–1 range.
- Each YOLO detection includes a normalized `bounding_box` in
  `[x1, y1, x2, y2]` order, with coordinates from 0 to 1.
- A label-present requirement passes only when at least one label detection is
  returned. A requirement name containing a numeric class such as `1001`
  checks for that predicted class.
- Unsupported checks (for example cap, logo, or damage) explicitly say the
  label-only detector cannot verify them; a required unsupported check should
  fail the overall result, not pass.
- Missing, invalid, or oversized image data returns an explicit client error.

Also repeat a known input with the same checkpoint and threshold. Exact
confidence values can vary with environment/model library versions, but
detections should be plausible and boxes should align with the label. A
successful API response is not enough: have a human inspect the overlay/input
and confirm that the model's class interpretation is sensible.

Return to mock mode by unsetting `INSPECTION_ENGINE` (or setting it to `mock`)
and restarting the backend. Do not leave the app configured to YOLO on a
machine without the selected weights and optional dependencies.

## 7. Phase 2B completion checklist

Mark Phase 2B complete only when each applicable item is evidenced:

- [ ] Optional dependencies installed in the backend virtual environment.
- [ ] Training smoke run and baseline training completed; `best.pt` path
      recorded.
- [ ] Validation metrics and plots reviewed.
- [ ] Held-out `test` evaluation run once on the selected checkpoint, with
      metrics and artifact path recorded.
- [ ] Numeric class meanings/provenance and CC BY 4.0 attribution reviewed.
- [ ] Human-reviewed examples show plausible detections for the intended
      product images; limitations and weak classes are documented.
- [ ] Backend starts explicitly in YOLO mode with the selected weights.
- [ ] Inference response and UI show the correct mode, label detections,
      confidence, normalized boxes, and unsupported-check behavior.
- [ ] Mock mode still starts and works when YOLO mode is not configured.
- [ ] No dataset copies, model weights, credentials, or customer images were
      accidentally added to Git.

## 8. Suggested handoff for another developer or AI session

When handing off or asking an AI session to continue, provide:

1. This runbook and the repository branch/working-tree state.
2. OS, Python version, `torch`/Ultralytics versions, and CPU/GPU details.
3. Exact training command, start/end status, logs, and absolute `best.pt` path.
4. Validation metrics plus held-out test metrics, plots directory, and any
   class-level failures.
5. Whether the model's numeric class mapping has been confirmed by a human.
6. Backend startup configuration (never include secrets) and one
   representative inference result, including the input image's permission/
   provenance.
7. Any unresolved error verbatim and the command that produced it.

An AI session can run reproducible commands, inspect code/logs and evaluation
artifacts, and fix implementation issues. A human must decide whether the
dataset/model is appropriate, interpret opaque class meanings, approve sharing
or licensing decisions, assess real-world false accept/reject risk, and approve
any claim that the detector is ready for operational use.
