import os
import shutil
import uuid
from pathlib import Path
from typing import Dict, Optional
from fastapi import APIRouter, File, HTTPException, UploadFile
import pandas as pd

from app.config import UPLOADS_DIR
from app.models.schemas import DatasetProfile
from app.services.data_profiler import data_profiler
from app.services.duckdb_service import duckdb_service

router = APIRouter(prefix="/api", tags=["Datasets"])

# In-memory storage for dataset metadata and profiles
DATASET_REGISTRY: Dict[str, DatasetProfile] = {}

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}

@router.post("/upload", response_model=DatasetProfile)
async def upload_dataset(
    file: UploadFile = File(...),
    dataset_id: Optional[str] = None
):
    """Upload a CSV or Excel dataset, load into DuckDB, profile, and return profile."""
    filename = file.filename or "uploaded_data"
    ext = Path(filename).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Supported formats: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Use existing dataset_id if provided and exists, else create new
    if not dataset_id or dataset_id not in DATASET_REGISTRY:
        dataset_id = dataset_id or str(uuid.uuid4())[:8]
        existing_tables = []
    else:
        existing_tables = [t.table for t in DATASET_REGISTRY[dataset_id].tables]

    base_name = Path(filename).stem
    safe_table_name = "".join(c if c.isalnum() or c == "_" else "_" for c in base_name).lower()
    if not safe_table_name or safe_table_name[0].isdigit():
        safe_table_name = f"t_{safe_table_name}"

    target_dir = UPLOADS_DIR / dataset_id
    target_dir.mkdir(parents=True, exist_ok=True)
    stored_path = target_dir / filename

    with open(stored_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    new_tables = []
    # Load into DuckDB
    if ext == ".csv":
        duckdb_service.load_csv(stored_path, safe_table_name)
        new_tables.append(safe_table_name)
    else:
        # Excel: could have multiple sheets
        xls = pd.ExcelFile(stored_path)
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name)
            sheet_table = f"{safe_table_name}_{sheet_name}".lower() if len(xls.sheet_names) > 1 else safe_table_name
            sheet_table = "".join(c if c.isalnum() or c == "_" else "_" for c in sheet_table)
            duckdb_service.load_dataframe(df, sheet_table)
            new_tables.append(sheet_table)

    # Combine existing tables + new tables (deduped in order)
    all_tables = []
    for t in existing_tables + new_tables:
        if t not in all_tables:
            all_tables.append(t)

    # Profile all tables in the dataset
    profile = data_profiler.profile_dataset(dataset_id=dataset_id, table_names=all_tables)
    DATASET_REGISTRY[dataset_id] = profile

    return profile

@router.get("/dataset/{dataset_id}", response_model=DatasetProfile)
async def get_dataset_profile(dataset_id: str):
    """Retrieve existing profile for a dataset."""
    if dataset_id not in DATASET_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")
    return DATASET_REGISTRY[dataset_id]

