from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.models import ProductConfiguration
from app.services.mock_inspection_service import MockInspectionService

app = FastAPI(title="Custom Product Vision Inspector API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

inspection_service = MockInspectionService()


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "custom-product-vision-inspector"}


@app.post("/api/inspection")
def run_inspection(product: ProductConfiguration):
    return inspection_service.run(product).model_dump()
