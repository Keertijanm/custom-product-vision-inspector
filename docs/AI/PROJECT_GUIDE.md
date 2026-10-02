# Custom Product Vision Inspector — Project Guide

> **Purpose:** This document is the source of truth for developers and AI agents working on the Custom Product Vision Inspector project.
>
> Before making changes, read and follow this guide.

---

# 1. Project Overview

**Custom Product Vision Inspector** is a configurable AI-powered computer vision platform for product inspection.

The platform allows a business/user to:

1. Upload an image of a physical product.
2. Define or select the product type.
3. Define product-specific inspection requirements.
4. Run an AI/computer-vision inspection.
5. Detect relevant objects, regions, labels, packaging elements, or defects.
6. Validate the detected information against the configured requirements.
7. Display a clear inspection result with visual evidence and explanations.

The core idea is **customizable product inspection**, rather than building a computer-vision system that works for only one fixed product.

The system should be designed so that different products can have different inspection requirements.

---

# 2. Project Goal

Build a functional, polished hackathon MVP demonstrating how AI and computer vision can be used to create configurable product inspection workflows.

The MVP should prioritize:

* A working end-to-end flow
* Clear user experience
* Modular architecture
* Realistic AI/computer-vision integration
* Configurable inspection requirements
* Explainable inspection results
* Easy future expansion

Avoid unnecessary complexity until the core workflow works.

---

# 3. Core User Flow

The primary user journey is:

```text
Open Application
      ↓
Create / Select Product
      ↓
Upload Product Image
      ↓
Define Inspection Requirements
      ↓
Start Inspection
      ↓
AI / Computer Vision Processing
      ↓
Requirement Validation
      ↓
Inspection Results
      ↓
PASS / FAIL + Reasons + Visual Evidence
```

Example:

```text
Product: Beverage Bottle

Requirements:
✓ Product must be detected
✓ Label must be present
✓ Cap must be present
✓ Logo must be visible
✓ Packaging should not have obvious damage

Result:

Overall: PASS

✓ Product detected
✓ Label detected
✓ Cap detected
✓ Logo detected
✓ No configured defect detected
```

Another example:

```text
Overall: FAIL

✓ Product detected
✗ Label not detected
✓ Cap detected
✗ Required logo not detected
```

The result must clearly explain **why** a check passed or failed.

---

# 4. MVP Scope — Phase 1

Phase 1 is focused on establishing a working end-to-end MVP.

## Frontend

Build a modern responsive web application using:

* Next.js
* React
* TypeScript

Required UI areas:

### Dashboard / Home

Should communicate:

* What Custom Product Vision Inspector is
* What problem it solves
* Main CTA to start an inspection
* Recent inspections if useful

### Product Setup

User should be able to:

* Enter product name
* Select product category
* Upload an image
* Define inspection requirements

Requirements should be represented as structured data.

Do not hardcode all requirements directly into UI components.

### Inspection

The inspection page should:

* Display the uploaded image
* Show processing/loading state
* Trigger inspection
* Display inspection status
* Display detected objects/regions when available
* Display individual inspection checks
* Display PASS/FAIL
* Display explanations

### Results

The results page should contain:

* Original image
* Annotated image/result visualization where available
* Overall inspection result
* Individual checks
* Detected issues
* Confidence information where meaningful
* Product information
* Timestamp

---

# 5. AI / Computer Vision Direction

The planned computer-vision stack may include:

* YOLO / YOLOv8
* OpenCV
* NumPy
* Segment Anything Model (SAM)
* Other appropriate computer-vision/AI models

The system should be designed around modular AI components.

Conceptually:

```text
                 Inspection Engine
                        │
          ┌─────────────┼─────────────┐
          ↓             ↓             ↓
      Detection     Segmentation   Image Processing
          │             │             │
          └─────────────┼─────────────┘
                        ↓
              Requirement Validation
                        ↓
                 Result Generation
```

Do not tightly couple the application to one model.

The model implementation should be replaceable without requiring major frontend changes.

---

# 6. Mock AI Results

During early development, some AI functionality may not yet be implemented.

When real model inference is unavailable, a mock inspection service may be used to establish and test the complete application flow.

However:

> **Never present mock results as real AI predictions.**

Mock functionality should be clearly separated from actual AI/model inference.

The architecture should allow the mock implementation to later be replaced by real YOLO/SAM/OpenCV/model inference.

---

# 7. Backend

Use Python for the AI/computer-vision/backend layer.

The backend should provide APIs for functionality such as:

```text
Image Upload
Product Configuration
Inspection Request
Inspection Execution
Inspection Results
```

The frontend should communicate with the backend through clearly defined API contracts.

Keep API request and response structures typed/documented where practical.

Avoid putting computer-vision logic directly inside frontend components.

---

# 8. Recommended Repository Structure

The structure may evolve as the project grows.

A starting structure:

```text
custom-product-vision-inspector/
│
├── .github/
│   └── copilot-instructions.md
│
├── docs/
│   └── AI/
│       └── PROJECT_GUIDE.md
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── types/
│   └── ...
│
├── backend/
│   ├── app/
│   ├── api/
│   ├── services/
│   ├── models/
│   ├── vision/
│   └── ...
│
├── README.md
├── .gitignore
└── ...
```

Do not create directories merely because they appear in this example.

Create structure according to actual implementation needs.

---

# 9. Branching Strategy

This project uses two primary branches:

```text
staging
main
```

## `staging`

`staging` is the active development and integration branch.

Use `staging` for:

* Feature development
* Incremental implementation
* Refactoring
* Bug fixes
* UI changes
* AI/CV experimentation
* Integration
* Local testing
* Cloud testing
* QA
* Verification

All active development should happen on `staging`.

---

## `main`

`main` is the **golden/stable branch**.

Treat `main` as:

* Stable
* Fully verified
* Submission-ready
* Production-quality where applicable

Do NOT develop directly on `main`.

Code should move:

```text
staging → main
```

only after complete verification.

---

# 10. Golden Branch Rules

AI agents and developers MUST follow these rules:

1. Do not directly develop on `main`.
2. Do not intentionally commit broken functionality to `main`.
3. Do not force-push `main`.
4. Do not rewrite `main` history.
5. Do not merge incomplete features into `main`.
6. Do not automatically merge `staging` into `main`.
7. `main` promotion requires explicit user approval.
8. Keep `main` stable and submission-ready.

If there is uncertainty about whether a feature is ready for `main`, keep it on `staging`.

---

# 11. Development Workflow

Use:

```text
Feature / Change
      ↓
staging
      ↓
Implement
      ↓
Build / Test
      ↓
Local Verification
      ↓
QA
      ↓
Fix Issues
      ↓
Final Verification
      ↓
User Approval
      ↓
staging → main
```

AI agents must not assume that working code is automatically ready for `main`.

---

# 12. Commit Guidelines

Prefer focused, meaningful commits.

Examples:

```text
feat: add product image upload
feat: add inspection requirements form
feat: add inspection results UI
feat: add backend inspection API
fix: handle invalid image uploads
fix: improve inspection loading state
refactor: separate inspection service
docs: update setup instructions
```

Avoid commits such as:

```text
changes
update
test
fix stuff
final
final2
new changes
```

Keep commits understandable for future developers.

---

# 13. Testing & QA

Before considering a feature complete, verify:

### Frontend

* Application starts successfully
* Production build succeeds
* UI renders correctly
* Responsive layout works
* Loading states work
* Error states work
* Empty states work
* User input is validated

### Backend

* Backend starts successfully
* API endpoints work
* Invalid input is handled
* Image upload is handled safely
* API responses follow the expected structure
* Errors are returned appropriately

### End-to-End

Verify the complete flow:

```text
Upload
  ↓
Configure Requirements
  ↓
Submit Inspection
  ↓
Backend Processing
  ↓
Result
  ↓
Display Result
```

Do not consider a feature complete merely because the code compiles.

---

# 14. Definition of Done

A feature is considered **Done** only when:

* Implementation is complete
* Relevant tests pass
* Application builds successfully
* Local behavior has been verified
* Error/loading states have been considered
* Integration has been verified where applicable
* No obvious blocking bugs remain
* No secrets are committed
* Documentation is updated where necessary

For promotion to `main`, additionally require:

* Full feature verification
* Regression check
* Stable end-to-end behavior
* Explicit user approval

---

# 15. Security Rules

Never commit:

* API keys
* Passwords
* Tokens
* Cloud credentials
* Private keys
* `.env` files containing secrets
* Personal credentials
* Sensitive datasets

Use environment variables for secrets and configuration.

Example:

```text
.env.local
.env
```

These should remain ignored by Git.

Never place real credentials directly inside source code.

---

# 16. Dependency Guidelines

Before adding a dependency:

1. Check whether the functionality can be implemented with existing dependencies.
2. Prefer established and maintained libraries.
3. Avoid unnecessary packages.
4. Consider package size and security.
5. Verify compatibility with the current project.
6. Update dependency documentation when useful.

Do not introduce a large framework/library merely to solve a small problem.

---

# 17. Frontend Guidelines

Use reusable components.

Prefer:

```text
components/
  ImageUploader
  ProductForm
  RequirementBuilder
  InspectionStatus
  InspectionCheck
  InspectionResults
```

over putting the entire application into one large component.

Use TypeScript types/interfaces for important data structures.

Avoid:

```text
any
```

unless there is a justified reason.

Keep business logic outside presentation components whenever practical.

---

# 18. Inspection Data Model

The inspection system should conceptually work with structured data.

Example:

```json
{
  "product": {
    "name": "Example Bottle",
    "category": "Beverage"
  },
  "requirements": [
    {
      "id": "label-present",
      "type": "object_presence",
      "target": "label",
      "required": true
    },
    {
      "id": "cap-present",
      "type": "object_presence",
      "target": "cap",
      "required": true
    }
  ]
}
```

Inspection output should also be structured.

Example:

```json
{
  "status": "FAIL",
  "checks": [
    {
      "requirementId": "label-present",
      "status": "FAIL",
      "message": "Required label was not detected."
    },
    {
      "requirementId": "cap-present",
      "status": "PASS",
      "message": "Cap detected."
    }
  ]
}
```

The exact schema may evolve as the AI pipeline becomes more sophisticated.

---

# 19. Explainability

Inspection results should be understandable to a non-technical user.

Prefer:

```text
FAIL
Label not detected in the expected product region.
```

instead of:

```text
class_id=3 confidence=0.421
```

Technical confidence/model information can be displayed as supporting information, but the primary result should be human-readable.

Where possible, provide visual evidence such as:

* Bounding boxes
* Segmentation masks
* Highlighted regions
* Detected defect areas

---

# 20. AI Agent Rules

Any AI agent working on this repository should:

1. Read this guide before making changes.
2. Inspect the existing repository before generating new architecture.
3. Check the current Git branch.
4. Work on `staging` for active development.
5. Never modify `main` directly.
6. Never merge to `main` without explicit user approval.
7. Preserve existing working functionality.
8. Avoid destructive changes.
9. Explain significant architectural decisions.
10. Test changes before declaring them complete.
11. Fix errors introduced by the implementation.
12. Avoid pretending that mocked AI results are real predictions.
13. Avoid inventing technologies or capabilities that have not been implemented.
14. Keep the implementation proportional to the current project phase.
15. Ask before making major architectural changes.
16. Do not remove existing functionality unless explicitly requested.
17. Keep documentation synchronized with meaningful architectural changes.

---

# 21. New AI Session Procedure

When starting a new AI session:

### Step 1 — Understand the repository

Inspect:

```text
README.md
docs/AI/PROJECT_GUIDE.md
.github/copilot-instructions.md
```

and the relevant source files.

### Step 2 — Check Git state

Determine:

```text
Current branch
Uncommitted changes
Recent commits
```

Do not discard existing work.

### Step 3 — Understand the current implementation

Before coding, identify:

* What already works
* What is incomplete
* Current architecture
* Current API contracts
* Current AI/model integration
* Existing tests

### Step 4 — Plan

For non-trivial work:

1. Explain the proposed change.
2. Identify affected files.
3. Identify potential risks.
4. Implement incrementally.

### Step 5 — Verify

After implementation:

* Run appropriate tests
* Run build checks
* Verify functionality
* Fix errors
* Summarize changes

---

# 22. Phase Management

The project should be developed incrementally.

## Phase 1 — Working MVP

Focus on:

```text
Product
  ↓
Image Upload
  ↓
Requirements
  ↓
Inspection API
  ↓
Inspection Engine
  ↓
Results
```

Mock AI functionality may be used where necessary.

## Phase 2 — Real Computer Vision

Integrate real models and image processing.

Potential components:

* YOLO/YOLOv8
* OpenCV
* SAM
* Image preprocessing
* Object detection
* Segmentation
* Requirement validation

## Phase 3 — Advanced Customization

Potential capabilities:

* Product-specific inspection workflows
* Custom detection requirements
* Configurable thresholds
* Better defect detection
* Custom model support
* Multiple product types

## Phase 4 — Hackathon Polish

Focus on:

* UI refinement
* Performance
* Explainability
* Demo reliability
* Screenshots
* Documentation
* Demo video
* Deployment

Do not implement future-phase functionality prematurely if it compromises the working MVP.

---

# 23. Current Priority

The immediate priority is:

> **Build a reliable Phase 1 end-to-end MVP before expanding the AI capabilities.**

The first working version should prove that:

```text
A user can configure an inspection
        ↓
submit an image
        ↓
run an inspection
        ↓
receive structured results
        ↓
understand why the product passed or failed
```

Once this workflow is stable, improve the intelligence of the inspection engine.

---

# 24. Architecture Principle

The most important architectural principle is:

> **Separate product configuration, inspection requirements, AI inference, validation logic, and presentation.**

Conceptually:

```text
User
 │
 ↓
Next.js UI
 │
 ↓
Backend API
 │
 ↓
Inspection Service
 │
 ├── AI Detection
 │
 ├── Segmentation
 │
 ├── Image Processing
 │
 └── Requirement Validation
 │
 ↓
Structured Inspection Result
 │
 ↓
Next.js Results UI
```

This separation should make it possible to improve or replace the AI models without rebuilding the entire application.

---

# 25. Project Philosophy

Build the project as if it could become a real product, while keeping the hackathon MVP achievable.

Prioritize:

**Working > Complex**

**Clear > Clever**

**Modular > Tightly Coupled**

**Explainable > Black Box**

**Verified > Assumed**

**Incremental > Over-engineered**

---

# 26. Golden Rule

> **Never sacrifice the stability of `main` for speed of development.**

Develop on:

```text
staging
```

Test and verify thoroughly.

Only after the feature is fully working and the user explicitly approves:

```text
staging → main
```

`main` is the golden branch.
`staging` is the development, testing, integration, and QA branch.

---

# 27. Document Maintenance

This document should evolve with the project.

Update it when there are meaningful changes to:

* Architecture
* Technology stack
* Branching strategy
* AI/model strategy
* Development workflow
* Testing strategy
* Major product capabilities

Do not update the document for every tiny implementation detail.

When this guide conflicts with a newer explicit project decision from the user, the explicit current project decision takes precedence and this guide should subsequently be updated to reflect it.
