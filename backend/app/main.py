import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.questions import router as questions_router
from app.api.upload import DATASET_REGISTRY, router as upload_router
from app.config import DEMO_DIR, OLLAMA_MODEL
from app.models.schemas import HealthResponse
from app.services.data_profiler import data_profiler
from app.services.duckdb_service import duckdb_service
from app.services.ollama_service import ollama_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("veritas.main")

def load_demo_data():
    """Load demo CSV files on startup if present."""
    sales_file = DEMO_DIR / "sales.csv"
    cust_file = DEMO_DIR / "customers.csv"
    prod_file = DEMO_DIR / "products.csv"

    loaded_tables = []
    if sales_file.exists():
        duckdb_service.load_csv(sales_file, "sales")
        loaded_tables.append("sales")
    if cust_file.exists():
        duckdb_service.load_csv(cust_file, "customers")
        loaded_tables.append("customers")
    if prod_file.exists():
        duckdb_service.load_csv(prod_file, "products")
        loaded_tables.append("products")

    if loaded_tables:
        demo_profile = data_profiler.profile_dataset("demo", loaded_tables)
        DATASET_REGISTRY["demo"] = demo_profile
        logger.info(f"Loaded demo dataset with tables: {loaded_tables}")

    # Also preload adversarial datasets for instant judge evaluation
    adv_dir = DEMO_DIR.parent / "adversarial"
    ambig_file = adv_dir / "case_f_dates" / "sales_ambiguous_dates.csv"
    if ambig_file.exists():
        duckdb_service.load_csv(ambig_file, "sales_ambig")
        ambig_profile = data_profiler.profile_dataset("adv_ambig", ["sales_ambig"])
        DATASET_REGISTRY["adv_ambig"] = ambig_profile
        logger.info("Loaded adv_ambig dataset with table: sales_ambig")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("VERITAS backend initializing...")
    load_demo_data()
    yield
    logger.info("VERITAS backend shutting down...")

app = FastAPI(
    title="HNX26PSI08 — Proof-Carrying Data Analyst API",
    version="0.1.0",
    description="Agentic GenAI Data Analyst with Independent DuckDB Verification Engine",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(upload_router)
app.include_router(questions_router)

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Check health of backend, Ollama service, and DuckDB analytical engine."""
    ollama_ok = await ollama_service.is_available()
    duckdb_ok = duckdb_service.is_available()

    return HealthResponse(
        status="ok",
        ollama="available" if ollama_ok else "unavailable",
        model=OLLAMA_MODEL,
        duckdb="available" if duckdb_ok else "unavailable"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)

