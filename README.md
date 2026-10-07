# VERITAS — Proof-Carrying Data Analyst

**Problem Statement: HNX26PSI08 — Proof-Carrying Data Analyst (Agentic GenAI)**

> _AI proposes → Code calculates → Verifier proves → Agent explains._

VERITAS is a forensic data-analysis and proof-verification console. It answers natural-language questions about tabular data using a **100% local LLM** — no paid API required — and produces a cryptographically traceable proof certificate for every result. If the system cannot establish a reliable, unambiguous answer, it **refuses** rather than hallucinating.

---

## Table of Contents

1. [What the Project Does](#1-what-the-project-does)
2. [Architecture](#2-architecture)
3. [Technologies & Libraries](#3-technologies--libraries)
4. [Prerequisites](#4-prerequisites)
5. [Installation — Backend](#5-installation--backend)
6. [Installation — Frontend](#6-installation--frontend)
7. [Configuration](#7-configuration)
8. [Running the System](#8-running-the-system)
9. [Reproducing the Demonstrated Results](#9-reproducing-the-demonstrated-results)
10. [Running the Test Suite](#10-running-the-test-suite)
11. [Project Structure](#11-project-structure)
12. [Adversarial Test Cases](#12-adversarial-test-cases)
13. [Troubleshooting](#13-troubleshooting)

---

## 1. What the Project Does

VERITAS implements the **Proof-Carrying Data Analyst** pipeline:

```
User Question
    ↓
Question Analysis & Answerability Check (local LLM)
    ↓
SQL Generation (local LLM — qwen2.5-coder:1.5b via Ollama)
    ↓
SQL Safety Validation (regex + AST-level checks)
    ↓
DuckDB Execution (the LLM never decides the numerical answer)
    ↓
Independent Re-Execution / Reproducibility Check
    ↓
10-Point Verification Engine
    ↓
Verified Answer  ──OR──  CANNOT_DETERMINE  ──OR──  NEEDS_CLARIFICATION
    ↓
Proof Certificate (SHA-256 hash, timestamp, full audit trail)
```

**Core guarantees:**
- The LLM _proposes_ SQL. DuckDB _computes_ the answer. The Verifier _certifies_ it.
- Ambiguous dates, missing metrics, duplicate primary keys, orphaned foreign keys, and unit mismatches all trigger **explicit refusals** with explanations, not hallucinated answers.
- Every verified result comes with a reproducible proof certificate.

---

## 2. Architecture

```
React / Vite (localhost:3000)
        ↓  /api/*  (Vite proxy)
FastAPI  (127.0.0.1:8000)
        ↓
Ollama local API  (127.0.0.1:11434)
        ↓  model: qwen2.5-coder:1.5b
Question Planner  →  SQL Generator  →  SQL Validator
        ↓
DuckDB (in-memory analytical engine)
        ↓
10-Point Verification Engine
        ↓
Verified Answer + Proof Certificate
        ↓
React Dashboard  (01 Data Source → 02 Profile → 03 Query → 04 Pipeline → 05 Result → 06 Evidence)
```

---

## 3. Technologies & Libraries

### Local AI / Model
| Component | Details |
|-----------|---------|
| **Ollama** | v0.33.2 — Local LLM runtime |
| **qwen2.5-coder:1.5b** | 1.5B parameter code-optimized model (runs on CPU or GPU) |

### Backend
| Library | Version | Purpose |
|---------|---------|---------|
| **Python** | 3.12.x | Runtime |
| **FastAPI** | 0.142.2 | REST API framework |
| **Uvicorn** | 0.54.0 | ASGI server |
| **DuckDB** | 1.5.6 | In-process analytical SQL engine |
| **Pandas** | 3.0.6 | CSV/Excel parsing and data manipulation |
| **Pydantic** | 2.13.5 | Request/response schema validation |
| **openpyxl** | 3.1.5 | Excel (.xlsx) file reading |
| **httpx** | 0.28.1 | Async HTTP client for Ollama API |
| **python-multipart** | 0.0.32 | Multipart file upload parsing |
| **pytest** | 9.1.1 | Test framework |
| **pyarrow** | 25.0.1 | Arrow columnar format support for DuckDB |

### Frontend
| Library | Version | Purpose |
|---------|---------|---------|
| **React** | 18.3.1 | UI framework |
| **Vite** | 5.4.x | Build tool and dev server |
| **@vitejs/plugin-react** | 4.3.1 | React fast-refresh support |

---

## 4. Prerequisites

Install these **before** cloning the repository. All are free and run locally.

### 4.1 Python 3.12+
Download from [python.org](https://www.python.org/downloads/).  
Verify: `python --version`

### 4.2 Node.js 18+ and npm 9+
Download from [nodejs.org](https://nodejs.org/).  
Verify: `node --version` and `npm --version`

### 4.3 Git
Download from [git-scm.com](https://git-scm.com/).  
Verify: `git --version`

### 4.4 Ollama
Download from [ollama.com](https://ollama.com/download).  
Verify: `ollama --version`

> **GPU Acceleration (Recommended):** On NVIDIA GPUs, Ollama will automatically use CUDA. Tested on RTX 3050 4 GB VRAM. The model also runs on CPU-only machines, but will be slower.

---

## 5. Installation — Backend

### Step 1 — Clone the repository

```bash
git clone <your-repository-url>
cd VERITAS
```

### Step 2 — Pull the local LLM model

Start the Ollama daemon (leave this terminal open, or run it as a background service):

```bash
ollama serve
```

In a second terminal, pull the model:

```bash
ollama pull qwen2.5-coder:1.5b
```

This downloads ~1 GB. Verify it loaded:

```bash
ollama list
# Should show: qwen2.5-coder:1.5b
```

Test it works:

```bash
ollama run qwen2.5-coder:1.5b "SELECT 1+1"
```

### Step 3 — Create a Python virtual environment

```bash
cd backend
python -m venv .venv
```

Activate it:

- **Windows (PowerShell):**  `.\.venv\Scripts\Activate.ps1`
- **Windows (CMD):**         `.\.venv\Scripts\activate.bat`
- **macOS / Linux:**         `source .venv/bin/activate`

### Step 4 — Install Python dependencies

```bash
pip install -r requirements.txt
```

This installs FastAPI, DuckDB, Pandas, Uvicorn, and all other backend dependencies.

### Step 5 — Verify the backend install

```bash
python -c "import duckdb, fastapi, pandas; print('Backend deps OK')"
```

---

## 6. Installation — Frontend

Open a new terminal (keep the backend terminal ready):

```bash
cd frontend
npm install
```

This installs React, Vite, and the React Vite plugin.

---

## 7. Configuration

The backend reads configuration from environment variables with sensible defaults. **No `.env` file is required** to run locally.

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Ollama API endpoint |
| `OLLAMA_MODEL` | `qwen2.5-coder:1.5b` | Model name to use |
| `OLLAMA_TIMEOUT_SECONDS` | `120.0` | Max seconds to wait for LLM response |
| `DUCKDB_PATH` | `:memory:` | DuckDB storage (in-memory by default) |

To use a different model (e.g., `codellama:7b`), set the environment variable before starting:

```bash
# Windows PowerShell
$env:OLLAMA_MODEL = "codellama:7b"
```

```bash
# macOS / Linux
export OLLAMA_MODEL="codellama:7b"
```

> The Vite dev server proxy is already configured in `frontend/vite.config.js` to forward all `/api/*` requests to `http://127.0.0.1:8000`.

---

## 8. Running the System

You need **3 terminal windows** running simultaneously.

### Terminal 1 — Ollama (LLM daemon)

```bash
ollama serve
```

Keep this running. Ollama will listen on `http://127.0.0.1:11434`.

### Terminal 2 — FastAPI Backend

```bash
cd VERITAS/backend
.\.venv\Scripts\Activate.ps1        # Windows PowerShell
# OR
source .venv/bin/activate           # macOS / Linux

python run.py
```

Expected output:
```
Starting VERITAS Proof-Carrying Data Analyst API on http://127.0.0.1:8000 ...
INFO: VERITAS backend initializing...
INFO: Loaded demo dataset with tables: ['sales', 'customers', 'products']
INFO: Loaded adv_ambig dataset with table: sales_ambig
INFO: Uvicorn running on http://127.0.0.1:8000
```

Verify the backend is healthy:
```bash
curl http://127.0.0.1:8000/api/health
# {"status":"ok","ollama":"available","model":"qwen2.5-coder:1.5b","duckdb":"available"}
```

### Terminal 3 — React Frontend (Development Mode)

```bash
cd VERITAS/frontend
npm run dev
```

Expected output:
```
  VITE v5.4.x  ready in 300ms
  ➜  Local:   http://localhost:3000/
```

Open **http://localhost:3000** in your browser.

---

## 9. Reproducing the Demonstrated Results

The demo dataset (`data/demo/`) is automatically loaded on backend startup. It contains three relational tables:

| Table | File | Rows | Description |
|-------|------|------|-------------|
| `sales` | `data/demo/sales.csv` | 18 | Orders with `order_id`, `customer_id`, `product_id`, `date`, `amount` |
| `customers` | `data/demo/customers.csv` | 5 | Customer profiles with `segment` |
| `products` | `data/demo/products.csv` | 6 | Product catalog with `category`, `price` |

### Result 1 — VERIFIED answer (Total Revenue 2025)

**Question:** `What was the total revenue in 2025?`  
**Dataset:** `demo`  
**Expected status:** `VERIFIED`  
**Expected answer:** `148700.0`

Via the UI:
1. Open `http://localhost:3000`
2. The demo dataset is loaded by default (see `01 DATA SOURCE`)
3. In `03 ASK YOUR DATA`, type: `What was the total revenue in 2025?`
4. Click **Run Proof Pipeline →**
5. The `05 RESULT` card should show **VERIFIED** with value `148,700`

Via API (command line):
```bash
curl -X POST http://127.0.0.1:8000/api/question \
  -H "Content-Type: application/json" \
  -d '{"question": "What was the total revenue in 2025?", "dataset_id": "demo"}'
```

Expected JSON excerpt:
```json
{
  "status": "VERIFIED",
  "answer": 148700.0,
  "answer_type": "number",
  "verification": { "verified": true, "status": "PASS" },
  "proof_certificate": { "overall_verified": true, "result_reproduced": true }
}
```

---

### Result 2 — CANNOT_DETERMINE (Missing Metric)

**Question:** `What was the profit in 2025?`  
**Dataset:** `demo`  
**Expected status:** `CANNOT_DETERMINE`  
**Reason:** The `sales` table has no `cost` or `profit` column — VERITAS refuses rather than guessing.

Via API:
```bash
curl -X POST http://127.0.0.1:8000/api/question \
  -H "Content-Type: application/json" \
  -d '{"question": "What was the profit in 2025?", "dataset_id": "demo"}'
```

---

### Result 3 — NEEDS_CLARIFICATION (Ambiguous Dates)

**Question:** `What was the total revenue in February?`  
**Dataset:** `adv_ambig` (adversarial dataset with ambiguous date formats)  
**Expected status:** `NEEDS_CLARIFICATION`  
**Reason:** The date column contains mixed formats (`DD/MM/YYYY` and `MM/DD/YYYY`) — February is ambiguous.

Via API:
```bash
curl -X POST http://127.0.0.1:8000/api/question \
  -H "Content-Type: application/json" \
  -d '{"question": "What was the total revenue in February?", "dataset_id": "adv_ambig"}'
```

---

### Result 4 — Multi-Table JOIN query

**Question:** `What is the total revenue by customer segment?`  
**Dataset:** `demo`  
**Expected status:** `VERIFIED`  
**Proof:** SQL will contain a JOIN across `sales` and `customers`.

---

### Result 5 — Upload your own CSV

1. In the UI, click `01 DATA SOURCE`
2. Drag and drop any `.csv` or `.xlsx` file
3. The `02 DATA PROFILE` panel will render column types, null counts, and quality notices
4. Ask any factual question against your uploaded dataset

---

## 10. Running the Test Suite

The backend ships with **35 tests** covering all pipeline stages.

```bash
cd VERITAS/backend
.\.venv\Scripts\Activate.ps1      # Activate virtualenv

# All 35 tests
pytest tests/ -v

# Core pipeline tests only
pytest tests/test_questions.py -v

# SQL generation and validation tests
pytest tests/test_sql.py -v

# 10-point verification engine tests
pytest tests/test_verification.py -v

# Adversarial and messy-data hardening tests
pytest tests/test_adversarial.py -v

# Data profiler tests
pytest tests/test_profiler.py -v
```

> **Note:** Tests that invoke the LLM (`test_questions.py`, `test_adversarial.py`) require Ollama to be running (`ollama serve`) with `qwen2.5-coder:1.5b` pulled.

Expected result: **35 passed**.

---

## 11. Project Structure

```
VERITAS/
├── README.md                          ← This file
│
├── backend/
│   ├── run.py                         ← Entry point: starts uvicorn server
│   ├── requirements.txt               ← All Python dependencies (pinned)
│   ├── app/
│   │   ├── config.py                  ← Environment config (Ollama URL, model, paths)
│   │   ├── main.py                    ← FastAPI app, lifespan, CORS, demo data loader
│   │   ├── api/
│   │   │   ├── questions.py           ← POST /api/question  (full pipeline endpoint)
│   │   │   └── upload.py             ← POST /api/upload, GET /api/dataset/{id}
│   │   ├── models/
│   │   │   └── schemas.py            ← Pydantic schemas (request/response models)
│   │   └── services/
│   │       ├── data_profiler.py      ← Schema analysis, null/dup/unit detection
│   │       ├── duckdb_service.py     ← DuckDB connection, CSV ingestion, SQL execution
│   │       ├── ollama_service.py     ← Async Ollama HTTP client
│   │       ├── question_planner.py   ← LLM-based answerability analysis
│   │       ├── sql_generator.py      ← LLM-based SQL generation with retry logic
│   │       ├── sql_validator.py      ← Safety validation (no DROP/DELETE/UPDATE etc.)
│   │       └── verification_engine.py ← 10-point independent verification
│   └── tests/
│       ├── test_health.py
│       ├── test_profiler.py
│       ├── test_sql.py
│       ├── test_questions.py
│       ├── test_verification.py
│       └── test_adversarial.py       ← 11 adversarial data scenarios
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js                 ← Vite dev server with /api proxy to :8000
│   ├── index.html
│   └── src/
│       ├── App.jsx                    ← Main layout and state management
│       ├── index.css                  ← Design tokens (forensic dark theme)
│       ├── main.jsx
│       ├── services/
│       │   └── api.js                ← Centralized API client with failover
│       └── components/
│           ├── Header.jsx            ← Engine status indicator
│           ├── DataUpload.jsx        ← 01 DATA SOURCE — drag-drop ingestion
│           ├── DataProfilePanel.jsx  ← 02 DATA PROFILE — schema & quality panel
│           ├── ProofPipeline.jsx     ← 04 PROOF PIPELINE — 6-stage stepper
│           ├── ResultDisplay.jsx     ← 05 RESULT — verified / refusal / clarify
│           ├── SqlViewer.jsx         ← Executed SQL display
│           ├── EvidencePanel.jsx     ← DuckDB tuple evidence table
│           └── ProofCertificate.jsx  ← 06 EVIDENCE — certificate & audit record
│
└── data/
    ├── demo/
    │   ├── sales.csv                  ← 18-row sales fact table (2025)
    │   ├── customers.csv              ← 5 customers with segments
    │   └── products.csv              ← 6 products with categories & prices
    └── adversarial/
        ├── case_a_clean/             ← Baseline clean query
        ├── case_b_duplicates/        ← Physical duplicate rows
        ├── case_c_dup_pk/            ← Duplicate primary key
        ├── case_d_units/             ← Mixed units (kg, g, lbs)
        ├── case_e_currency/          ← Mixed currencies (INR, USD, EUR)
        ├── case_f_dates/             ← Ambiguous date formats (MM/DD vs DD/MM)
        ├── case_g_nulls/             ← Critical null values in metric columns
        ├── case_h_contradictions/    ← Two tables with contradicting values
        ├── case_i_orphans/           ← Orphaned foreign keys
        ├── case_j_cardinality/       ← M:N join cardinality explosion risk
        └── case_k_missing_field/     ← Question requires a non-existent column
```

---

## 12. Adversarial Test Cases

VERITAS is hardened against 11 classes of data problems. Each has a dedicated dataset under `data/adversarial/` and a corresponding automated test in `backend/tests/test_adversarial.py`.

| Case | Data Problem | Expected Pipeline Behaviour |
|------|--------------|-----------------------------|
| A | Clean baseline | `VERIFIED` with correct numerical answer |
| B | Duplicate rows | `VERIFIED` with `WARNING` about duplicates in proof |
| C | Duplicate primary key | `CANNOT_DETERMINE` — PK integrity violated |
| D | Mixed units (kg/g/lbs) | `CANNOT_DETERMINE` — unit inconsistency detected |
| E | Mixed currencies (INR/USD/EUR) | `CANNOT_DETERMINE` — currency mixing flagged |
| F | Ambiguous dates (MM/DD vs DD/MM) | `NEEDS_CLARIFICATION` — date format undecidable |
| G | Nulls in metric column | `VERIFIED` with null `WARNING` in certificate |
| H | Contradicting tables | `CANNOT_DETERMINE` — contradiction detected |
| I | Orphaned foreign keys | `VERIFIED` with orphan `WARNING`, or refusal |
| J | M:N join cardinality explosion | `CANNOT_DETERMINE` — multiply-counting risk detected |
| K | Missing required field | `CANNOT_DETERMINE` — required column absent |

---

## 13. Troubleshooting

### `TypeError: Failed to fetch` in the browser
- Ensure the backend is running: `curl http://127.0.0.1:8000/api/health`
- Ensure Ollama is running: `ollama list`
- Ensure you are accessing `http://localhost:3000` (not the `dist/` folder directly)
- The frontend API client will automatically retry with direct `http://127.0.0.1:8000` if the Vite proxy fails

### `ollama: unavailable` in the health badge
- Run `ollama serve` in a separate terminal
- Check that the model is present: `ollama list`
- If missing: `ollama pull qwen2.5-coder:1.5b`

### LLM returns bad SQL (rare with small model)
- The backend has automatic SQL repair and retry logic (up to 3 attempts)
- If the question is genuinely unanswerable from the data, it will return `CANNOT_DETERMINE`
- Try rephrasing the question more specifically

### `ModuleNotFoundError` when running backend
- Ensure the virtual environment is **activated** before running `python run.py`
- Re-run `pip install -r requirements.txt`

### Port conflicts
| Service | Default Port | Override |
|---------|-------------|---------|
| Vite dev server | `3000` | Edit `frontend/vite.config.js` → `server.port` |
| FastAPI backend | `8000` | Edit `backend/run.py` → `uvicorn.run(..., port=...)` |
| Ollama | `11434` | Set `OLLAMA_BASE_URL` environment variable |

### Windows PowerShell execution policy error
If `.\.venv\Scripts\Activate.ps1` is blocked:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## License

This project was developed for the **HackNXTrix 2026 Hackathon** (Problem Statement HNX26PSI08). All demo datasets are synthetic. No real personal or financial data is used.
