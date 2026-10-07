VERITAS — Proof-Carrying Data Analyst
HNX26PSI08 — Proof-Carrying Data Analyst (Agentic GenAI)
AI proposes → Code calculates → Verifier proves → Agent explains.

VERITAS is an agentic data-analysis system that answers natural-language questions over tabular data while carrying executable evidence for its answers.
Instead of allowing an LLM to directly invent a numerical answer, VERITAS separates reasoning from computation:
Question → Answerability Check → SQL Generation → Safety Validation → DuckDB Execution → Independent Re-execution → Verification → Evidence → Answer / Refusal
If the available data is insufficient, ambiguous, contradictory, or unsafe to interpret reliably, VERITAS refuses to produce an unsupported answer.
1. What the Project Does
VERITAS implements the Proof-Carrying Data Analyst concept for problem statement HNX26PSI08.
A user can upload CSV/XLSX datasets and ask questions such as:
What was the total revenue in 2025?
The system does not simply ask an LLM to answer.
Instead:
                     USER QUESTION
                          │
                          ▼
                ┌───────────────────┐
                │ Question Planner  │
                │ + Answerability   │
                │     Analysis      │
                └─────────┬─────────┘
                          │
                          ▼
                ┌───────────────────┐
                │ SQL Generation    │
                │ qwen2.5-coder     │
                └─────────┬─────────┘
                          │
                          ▼
                ┌───────────────────┐
                │ SQL Safety        │
                │ Validation        │
                └─────────┬─────────┘
                          │
                          ▼
                ┌───────────────────┐
                │ DuckDB Execution  │
                │ ACTUAL COMPUTATION│
                └─────────┬─────────┘
                          │
                          ▼
                ┌───────────────────┐
                │ Independent       │
                │ Re-execution      │
                └─────────┬─────────┘
                          │
                          ▼
                ┌───────────────────┐
                │ Verification      │
                │ Engine            │
                └─────────┬─────────┘
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
         VERIFIED   CANNOT_DETERMINE   NEEDS
                                    CLARIFICATION
             │
             ▼
       Evidence + SQL +
       Verification Record
Core Principle
The LLM proposes. DuckDB calculates. The verifier checks.

The final numerical answer comes from the executed database result, not from generated LLM prose.
2. Why VERITAS Is Different
Traditional LLM data-analysis systems can produce plausible-looking answers even when:
- a required column does not exist
- dates are ambiguous
- units are inconsistent
- currencies are incompatible
- duplicate keys multiply a JOIN
- tables contradict each other
- important values are missing
- a question cannot actually be answered from the supplied data
VERITAS explicitly checks these conditions.
The system can return three primary outcomes:
Status	Meaning
VERIFIED	The question was answerable and the computed result passed verification
CANNOT_DETERMINE	The available data cannot support a reliable answer
NEEDS_CLARIFICATION	The question or data contains an ambiguity that must be resolved


Messy-data conditions are assessed rather than blindly rejected. A warning such as legitimate duplicate transaction rows or non-critical NULLs may still allow a result to be verified, while conditions that compromise correctness can cause refusal.
3. Key Features
Natural-Language Data Analysis
Ask questions directly in natural language instead of writing SQL manually.
Local LLM
The default model is:
qwen2.5-coder:1.5b
running locally through Ollama.
No paid LLM API is required.
Executable Computation
Generated SQL is actually executed against DuckDB.
The LLM does not provide the final numerical result.
SQL Safety Validation
Generated SQL is checked before execution to prevent unsafe or destructive operations.
Independent Reproduction
The generated computation is executed and then independently re-executed to verify that the result is reproducible.
Data-Quality Analysis
The system profiles uploaded datasets for information such as:
- row counts
- column types
- NULL values
- distinct values
- duplicates
- potential key issues
- suspicious data-quality conditions
- unit/currency/date problems where detectable
Multi-Table Analysis
VERITAS can reason over relational datasets and generate JOIN queries.
Refusal Capability
When an answer cannot be reliably established, the system refuses rather than hallucinating.
Proof / Evidence Record
The interface exposes:
- question
- interpretation/plan
- generated SQL
- SQL safety result
- execution status
- verification checks
- reproducibility result
- evidence/result tuple
- final status
4. Architecture
┌──────────────────────────────────────────────────────┐
│                  React / Vite UI                     │
│              http://localhost:3000                  │
└───────────────────────┬──────────────────────────────┘
                        │ /api/*
                        ▼
┌──────────────────────────────────────────────────────┐
│                    FastAPI                           │
│              http://127.0.0.1:8000                 │
└───────────────┬───────────────────────┬──────────────┘
                │                       │
                ▼                       ▼
        ┌───────────────┐       ┌────────────────┐
        │    Ollama     │       │     DuckDB     │
        │ :11434        │       │ Analytical SQL │
        └───────┬───────┘       └───────┬────────┘
                │                       │
                ▼                       │
       qwen2.5-coder:1.5b               │
                │                       │
                ▼                       │
       Question Planner                 │
                │                       │
                ▼                       │
         SQL Generator                 │
                │                       │
                ▼                       │
         SQL Validator ────────────────┘
                                        │
                                        ▼
                              Verification Engine
                                        │
                         ┌──────────────┼──────────────┐
                         ▼              ▼              ▼
                      VERIFIED   CANNOT_DETERMINE   NEEDS_CLARIFICATION
                         │
                         ▼
                  Evidence / Audit
                         │
                         ▼
                    React UI
5. Technologies, Libraries and Models
AI / Local Model
Component	Version / Details	Purpose
Ollama	0.33.2	Local LLM runtime
qwen2.5-coder:1.5b	1.5B parameters	Question planning and SQL generation


Backend
Technology	Version	Purpose
Python	3.12.x	Backend runtime
FastAPI	0.142.2	REST API
Uvicorn	0.54.0	ASGI server
DuckDB	1.5.6	Analytical SQL execution
Pandas	3.0.6	Data loading/profiling
Pydantic	2.13.5	API schemas
openpyxl	3.1.5	XLSX support
httpx	0.28.1	Ollama API communication
python-multipart	0.0.32	File upload handling
PyArrow	25.0.1	Columnar data support
pytest	9.1.1	Automated testing


Frontend
Technology	Version	Purpose
React	18.3.1	User interface
Vite	5.4.x	Frontend build/dev server
@vitejs/plugin-react	4.3.1	React integration


6. Prerequisites
Install the following before running the project:
- Python 3.12+
- Node.js 18+
- npm 9+
- Git
- Ollama
Optional but recommended:
- NVIDIA GPU with CUDA support
The project was developed and tested with an NVIDIA RTX 3050 4 GB GPU. Ollama can also run the model on CPU-only systems, although inference will generally be slower.
Verify the installations:
python --version
node --version
npm --version
git --version
ollama --version
7. Installation
7.1 Clone the Repository
git clone <YOUR_PUBLIC_GITHUB_REPOSITORY_URL>
cd VERITAS
7.2 Install and Configure Ollama
Start Ollama:
ollama serve
Keep this terminal running.
In another terminal, download the model:
ollama pull qwen2.5-coder:1.5b
Verify:
ollama list
You should see:
qwen2.5-coder:1.5b
Test the model:
ollama run qwen2.5-coder:1.5b "SELECT 1+1"
8. Backend Installation
Move into the backend:
cd backend
Create a Python virtual environment:
python -m venv .venv
Windows PowerShell
.\.venv\Scripts\Activate.ps1
Windows CMD
.\.venv\Scripts\activate.bat
macOS / Linux
source .venv/bin/activate
Install dependencies:
pip install -r requirements.txt
Verify the backend dependencies:
python -c "import duckdb, fastapi, pandas; print('Backend dependencies OK')"
9. Frontend Installation
Open another terminal:
cd frontend
Install Node dependencies:
npm install
10. Configuration
VERITAS works without a .env file using the following defaults:
Environment Variable	Default	Purpose
OLLAMA_BASE_URL	http://127.0.0.1:11434	Ollama server
OLLAMA_MODEL	qwen2.5-coder:1.5b	Local model
OLLAMA_TIMEOUT_SECONDS	120	LLM request timeout
DUCKDB_PATH	:memory:	DuckDB storage


Windows PowerShell
Example:
$env:OLLAMA_MODEL="qwen2.5-coder:1.5b"
macOS / Linux
export OLLAMA_MODEL="qwen2.5-coder:1.5b"
The frontend Vite configuration proxies /api/* requests to:
http://127.0.0.1:8000
No API key is required for the default local setup.
11. Running the System
VERITAS uses three processes.
Terminal 1 — Ollama
ollama serve
Ollama runs at:
http://127.0.0.1:11434
Terminal 2 — FastAPI Backend
cd VERITAS/backend
Activate the virtual environment.
Then run:
python run.py
The backend runs at:
http://127.0.0.1:8000
Check the backend health:
curl http://127.0.0.1:8000/api/health
Expected response:
{
  "status": "ok",
  "ollama": "available",
  "model": "qwen2.5-coder:1.5b",
  "duckdb": "available"
}
Terminal 3 — React Frontend
cd VERITAS/frontend
npm run dev
Open:
http://localhost:3000
12. Using the Application
The dashboard follows this workflow:
01 DATA SOURCE
       ↓
02 DATA PROFILE
       ↓
03 ASK YOUR DATA
       ↓
04 PROOF PIPELINE
       ↓
05 RESULT
       ↓
06 EVIDENCE
Uploading Data
VERITAS supports:
.csv
.xlsx
Upload a dataset through the DATA SOURCE panel.
The DATA PROFILE panel displays information such as:
- number of rows
- number of columns
- column types
- NULL counts
- distinct values
- duplicate information
- sample values
- detected data-quality warnings
The uploaded dataset becomes the source of truth for subsequent analysis.
13. Reproducing the Demonstrated Results
The repository contains synthetic demonstration data under:
data/demo/
The demonstration dataset contains:
Table	File	Rows	Description
sales	data/demo/sales.csv	18	Sales transactions
customers	data/demo/customers.csv	5	Customer profiles and segments
products	data/demo/products.csv	6	Product information


14. Demonstration 1 — VERIFIED Numerical Answer
Question
What was the total revenue in 2025?
Expected Result
Status: VERIFIED
Answer: 148700.0
Reproduce Through the UI
1. Start Ollama.
2. Start the backend.
3. Start the frontend.
4. Open:
http://localhost:3000
5. Use the demo dataset.
6. Go to ASK YOUR DATA.
7. Enter:
What was the total revenue in 2025?
8. Click:
Run Proof Pipeline
The result should show:
VERIFIED

148,700
Reproduce Through the API
curl -X POST http://127.0.0.1:8000/api/question \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"What was the total revenue in 2025?\",\"dataset_id\":\"demo\"}"
Expected response contains:
{
  "status": "VERIFIED",
  "answer": 148700.0,
  "answer_type": "number",
  "verification": {
    "verified": true,
    "status": "PASS"
  }
}
The important property is that 148700.0 is obtained from the actual DuckDB execution result and then verified. It is not supplied as a hardcoded LLM answer.
15. Demonstration 2 — CANNOT_DETERMINE
Question
What was the profit in 2025?
Expected Result
Status: CANNOT_DETERMINE
Reason
The demonstration sales data does not contain the required cost/profit information.
VERITAS therefore does not invent a profit value.
API Reproduction
curl -X POST http://127.0.0.1:8000/api/question \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"What was the profit in 2025?\",\"dataset_id\":\"demo\"}"
Expected:
CANNOT_DETERMINE
This demonstrates the system's refusal capability when the requested metric cannot be reliably derived from the available data.
16. Demonstration 3 — NEEDS_CLARIFICATION
The repository contains an adversarial dataset with ambiguous date formats.
Question
What was the total revenue in February?
Dataset
adv_ambig
Expected Result
Status: NEEDS_CLARIFICATION
Reason
The dataset contains mixed date formats such as:
DD/MM/YYYY
MM/DD/YYYY
Therefore, the meaning of "February" cannot be established reliably without clarification.
API Reproduction
curl -X POST http://127.0.0.1:8000/api/question \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"What was the total revenue in February?\",\"dataset_id\":\"adv_ambig\"}"
Expected:
NEEDS_CLARIFICATION
17. Demonstration 4 — Multi-Table JOIN
Question
What is the total revenue by customer segment?
VERITAS must combine information from:
sales
   │
   │ customer_id
   ▼
customers
The generated SQL therefore performs a JOIN across the relevant tables.
Expected result:
VERIFIED
The important point is that the JOIN is actually executed by DuckDB and the result is subjected to verification rather than being calculated by the LLM.
18. Demonstration 5 — Upload Your Own Dataset
1. Open the application.
2. Go to DATA SOURCE.
3. Drag and drop a .csv or .xlsx file.
4. Inspect the DATA PROFILE.
5. Ask a factual question about the uploaded dataset.
6. VERITAS analyzes the actual uploaded schema.
7. Generated SQL is validated before execution.
8. DuckDB performs the calculation.
9. The result is independently checked.
10. The system returns VERIFIED, CANNOT_DETERMINE, or NEEDS_CLARIFICATION.
19. Proof-Carrying Verification
For a VERIFIED result, VERITAS records the computational evidence used to establish the answer.
The verification pipeline checks aspects including:
1. Question / operation alignment
2. SQL safety
3. SQL execution
4. Schema / column validity
5. Result availability
6. Data-quality conditions
7. Ambiguity conditions
8. Join / cardinality risks
9. Independent re-execution
10. Answer provenance
The final numerical value is taken from the executed DuckDB result rather than from generated LLM text.
The fundamental distinction is:
LLM-generated answer
        ✗
versus:
LLM-generated computation
        ↓
Actual execution
        ↓
Independent verification
        ↓
Verified result
20. Messy and Adversarial Data
The project contains adversarial datasets covering conditions such as:
Case	Scenario	Expected Handling
A	Clean baseline	VERIFIED
B	Duplicate physical rows	May verify with warning
C	Duplicate primary keys	Refuse when correctness is compromised
D	Mixed units	Refuse when no reliable normalization exists
E	Mixed currencies	Refuse without a valid conversion basis
F	Ambiguous date formats	NEEDS_CLARIFICATION
G	NULL metric values	Verify with warning or refuse depending on impact
H	Contradictory tables	CANNOT_DETERMINE
I	Orphaned foreign keys	Warning or refusal depending on impact
J	Many-to-many JOIN/cardinality risk	Refuse when result cannot be trusted
K	Missing required field	CANNOT_DETERMINE


The goal is not to reject every imperfect dataset.
Instead, VERITAS distinguishes between:
Data issue that does not invalidate the requested calculation
                         ↓
                    WARNING
                         ↓
                  MAY VERIFY
and:
Data issue that prevents reliable computation
                         ↓
                      REFUSE
This distinction is important for real-world messy data.
21. Currency and Unit Handling
VERITAS does not silently assume that values expressed in different units or currencies are directly comparable.
For example:
100 USD
100 EUR
100 INR
must not automatically be treated as equivalent.
A reliable conversion basis must be available before combining incompatible currencies.
Likewise, values such as:
10 kg
1000 g
2 lb
cannot safely be combined unless the required unit conversion is established.
If the system cannot establish a reliable conversion:
CANNOT_DETERMINE
is preferred over inventing a conversion.
22. Running the Test Suite
The backend contains automated tests covering the major components of the system.
Run the complete test suite:
cd backend
pytest tests/ -v
Core Pipeline Tests
pytest tests/test_questions.py -v
SQL Generation and Validation
pytest tests/test_sql.py -v
Verification Engine
pytest tests/test_verification.py -v
Adversarial Tests
pytest tests/test_adversarial.py -v
Data Profiler
pytest tests/test_profiler.py -v
LLM-dependent tests require Ollama to be running:
ollama serve
and the model to be installed:
ollama pull qwen2.5-coder:1.5b
The current documented implementation contains 35 tests covering the core and adversarial pipeline.
Before final submission, run:
pytest tests/ -v
and verify the final test count after all repository changes.
23. Project Structure
VERITAS/
│
├── README.md
│
├── backend/
│   ├── run.py
│   ├── requirements.txt
│   │
│   ├── app/
│   │   ├── config.py
│   │   ├── main.py
│   │   │
│   │   ├── api/
│   │   │   ├── questions.py
│   │   │   └── upload.py
│   │   │
│   │   ├── models/
│   │   │   └── schemas.py
│   │   │
│   │   └── services/
│   │       ├── data_profiler.py
│   │       ├── duckdb_service.py
│   │       ├── ollama_service.py
│   │       ├── question_planner.py
│   │       ├── sql_generator.py
│   │       ├── sql_validator.py
│   │       └── verification_engine.py
│   │
│   └── tests/
│       ├── test_health.py
│       ├── test_profiler.py
│       ├── test_sql.py
│       ├── test_questions.py
│       ├── test_verification.py
│       └── test_adversarial.py
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   │
│   └── src/
│       ├── App.jsx
│       ├── main.jsx
│       ├── index.css
│       │
│       ├── services/
│       │   └── api.js
│       │
│       └── components/
│           ├── Header.jsx
│           ├── DataUpload.jsx
│           ├── DataProfilePanel.jsx
│           ├── ProofPipeline.jsx
│           ├── ResultDisplay.jsx
│           ├── SqlViewer.jsx
│           ├── EvidencePanel.jsx
│           └── ProofCertificate.jsx
│
└── data/
    ├── demo/
    │   ├── sales.csv
    │   ├── customers.csv
    │   └── products.csv
    │
    └── adversarial/
        ├── case_a_clean/
        ├── case_b_duplicates/
        ├── case_c_dup_pk/
        ├── case_d_units/
        ├── case_e_currency/
        ├── case_f_dates/
        ├── case_g_nulls/
        ├── case_h_contradictions/
        ├── case_i_orphans/
        ├── case_j_cardinality/
        └── case_k_missing_field/
24. API Endpoints
Method	Endpoint	Purpose
GET	/api/health	Backend, Ollama and DuckDB health
POST	/api/upload	Upload CSV/XLSX
GET	/api/dataset/{dataset_id}	Retrieve dataset profile
POST	/api/question	Run the proof-carrying analysis pipeline
GET	/api/result/{result_id}	Retrieve a previous result


25. Troubleshooting
TypeError: Failed to fetch
Check that the backend is running:
http://127.0.0.1:8000
Then:
curl http://127.0.0.1:8000/api/health
Also make sure the frontend is running:
npm run dev
Ollama Unavailable
Run:
ollama serve
Then:
ollama list
Make sure:
qwen2.5-coder:1.5b
is installed.
Model Not Found
Run:
ollama pull qwen2.5-coder:1.5b
Python Module Not Found
Activate the backend virtual environment.
Windows:
.\.venv\Scripts\Activate.ps1
Then:
pip install -r requirements.txt
Port Already in Use
Check whether another instance of:
Ollama
FastAPI
Vite
is already running.
Stop the conflicting process and restart the appropriate service.
26. Important Design Principle
VERITAS deliberately separates reasoning from computation.
The LLM is responsible for:
- understanding the user's question
- identifying whether the question appears answerable
- proposing a computational plan
- generating SQL
The execution engine is responsible for:
- accessing the actual dataset
- performing arithmetic
- filtering rows
- aggregating values
- performing JOINs
- producing the numerical result
The verifier is responsible for:
- checking safety
- checking execution
- checking schema alignment
- checking data quality
- checking ambiguity
- checking JOIN/cardinality risks
- reproducing the result
- determining whether the result can be trusted
Therefore:
The language model is not the source of truth for the numerical answer.

27. Reproducibility
A demonstrated result can be reproduced from a clean checkout by following these steps:
1. Clone the repository
2. Install Python dependencies
3. Install Node dependencies
4. Install Ollama
5. Pull qwen2.5-coder:1.5b
6. Start Ollama
7. Start FastAPI with python run.py
8. Start Vite with npm run dev
9. Open localhost:3000
10. Load the demo dataset
11. Enter the demonstrated question
12. Run the proof pipeline
13. Inspect the generated SQL
14. Inspect the execution result
15. Inspect verification
16. Inspect evidence
The demonstrated result is therefore not merely a screenshot or manually entered value. The computation can be regenerated from the repository.
28. Evaluation Checklist
This README directly covers the required repository documentation.
What the project does
See:
- Section 1 — What the Project Does
- Section 2 — Why VERITAS Is Different
- Section 3 — Key Features
Technologies, libraries and models used
See:
- Section 5 — Technologies, Libraries and Models
How to install dependencies
See:
- Section 6 — Prerequisites
- Section 7 — Installation
- Section 8 — Backend Installation
- Section 9 — Frontend Installation
How to configure and run the system
See:
- Section 10 — Configuration
- Section 11 — Running the System
How to reproduce demonstrated results
See:
- Section 13 — Reproducing the Demonstrated Results
- Section 14 — Demonstration 1
- Section 15 — Demonstration 2
- Section 16 — Demonstration 3
- Section 17 — Demonstration 4
- Section 18 — Demonstration 5
Reliability and testing
See:
- Section 19 — Proof-Carrying Verification
- Section 20 — Messy and Adversarial Data
- Section 22 — Running the Test Suite
29. Final Submission Checklist
Before submitting the repository, verify:
- [ ] GitHub repository is Public
- [ ] README.md exists at the repository root
- [ ] Repository can be cloned without private credentials
- [ ] backend/requirements.txt exists
- [ ] frontend/package.json exists
- [ ] Demo datasets are included
- [ ] Adversarial datasets/tests are included
- [ ] Ollama installation instructions are included
- [ ] Model installation instructions are included
- [ ] Backend installation instructions are included
- [ ] Frontend installation instructions are included
- [ ] Configuration instructions are included
- [ ] Running instructions are included
- [ ] Demonstrated results are reproducible
- [ ] /api/health works
- [ ] 148700.0 revenue result can be reproduced
- [ ] Missing-profit question returns CANNOT_DETERMINE
- [ ] Ambiguous-date question returns NEEDS_CLARIFICATION
- [ ] Multi-table JOIN query works
- [ ] Tests pass after the latest code changes
- [ ] Frontend production build passes
- [ ] No API keys or private credentials are committed
- [ ] No .env secrets are committed
- [ ] Repository link is accessible publicly
30. Submission
Public Git Repository:
<YOUR_PUBLIC_GITHUB_REPOSITORY_URL>
Submit the public repository URL before the evaluation deadline.
31. Hackathon Information
HackNXTrix 2026
Problem Statement: HNX26PSI08
Project: VERITAS — Proof-Carrying Data Analyst
Category: Agentic GenAI / Data Analysis
The demonstration datasets are synthetic and are intended for project demonstration and evaluation.
No real personal, financial, or confidential data is required to run the demonstration.
VERITAS
AI proposes → Code calculates → Verifier proves → Agent explains.
