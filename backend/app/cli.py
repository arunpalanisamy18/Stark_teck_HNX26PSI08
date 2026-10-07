import asyncio
import sys
from pathlib import Path

# Add backend directory to path if running directly
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.api.questions import ask_question
from app.api.upload import DATASET_REGISTRY
from app.config import DEMO_DIR
from app.main import load_demo_data
from app.models.schemas import QuestionRequest
from app.services.data_profiler import data_profiler
from app.services.duckdb_service import duckdb_service

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ADVERSARIAL_DIR = BASE_DIR / "data" / "adversarial"

REQUIRED_DEMO_QUESTIONS = [
    "What is the total revenue?",
    "What was the total revenue in 2025?",
    "What is the average order amount?",
    "What was the revenue from Chennai?",
    "How many orders were placed?",
    "Which product category generated the most revenue?",
    "What is the total revenue by customer segment?",  # Multi-table JOIN
    "What was the profit in 2025?",  # Refusal test
    "What was the weather in Chennai on the date of the highest order?",  # Refusal test
]

async def run_pipeline(question: str, dataset_id: str = "demo"):
    print("\n" + "=" * 65)
    print(f"QUESTION: {question} (Dataset: {dataset_id})")
    print("-" * 65)

    req = QuestionRequest(question=question, dataset_id=dataset_id)
    resp = await ask_question(req)

    print(f"STATUS: {resp.status}")

    if resp.status in ("CANNOT_DETERMINE", "NEEDS_CLARIFICATION"):
        print(f"REASON / CLARIFICATION NEEDED:\n  {resp.reason}")
        if resp.missing_information:
            print(f"MISSING INFORMATION: {resp.missing_information}")
        if resp.proof_certificate:
            print(f"VERIFIER DECISION: {resp.proof_certificate.message}")
    elif resp.status == "VERIFIED":
        print(f"GENERATED SQL:\n  {resp.sql}")
        print(f"EXECUTION STATUS: PASS ({resp.execution.get('execution_time_ms', 0)} ms, {resp.execution.get('row_count', 0)} rows)")
        print(f"FINAL ANSWER: {resp.answer}")
        print("-" * 65)
        print("VERIFICATION CHECKS:")
        if resp.proof_certificate and resp.proof_certificate.checks:
            for chk in resp.proof_certificate.checks:
                print(f"  [{chk.status}] {chk.name}: {chk.details or ''}")
        print(f"REPRODUCTION STATUS: {'PASS' if resp.proof_certificate and resp.proof_certificate.result_reproduced else 'FAIL'}")
    else:
        print(f"REASON: {resp.reason}")
        print(f"WARNINGS: {resp.warnings}")

    if resp.warnings:
        print(f"DATA QUALITY NOTICES: {resp.warnings[:3]}")

    print("=" * 65)
    return resp

def _load_adversarial_dataset(dataset_id: str, table_map: dict):
    tables = []
    for tbl, fpath in table_map.items():
        duckdb_service.load_csv(Path(fpath), tbl)
        tables.append(tbl)
    profile = data_profiler.profile_dataset(dataset_id=dataset_id, table_names=tables)
    DATASET_REGISTRY[dataset_id] = profile
    return profile

async def run_adversarial_demo():
    print("\n" + "#" * 65)
    print("### VERITAS ADVERSARIAL & MESSY-DATA HARDENING SUITE ###")
    print("#" * 65)

    scenarios = [
        {
            "id": "adv_clean",
            "name": "Case A: Clean Baseline",
            "files": {"sales_clean": ADVERSARIAL_DIR / "case_a_clean" / "sales.csv"},
            "question": "What was the total revenue in 2025?",
        },
        {
            "id": "adv_dups",
            "name": "Case B: Identical Duplicate Rows",
            "files": {"sales_dups": ADVERSARIAL_DIR / "case_b_duplicates" / "sales_dups.csv"},
            "question": "What is the total revenue?",
        },
        {
            "id": "adv_dup_pk",
            "name": "Case C: Duplicate Primary Key with Conflicting Attributes",
            "files": {"customers_dup_pk": ADVERSARIAL_DIR / "case_c_dup_pk" / "customers_dup_pk.csv"},
            "question": "What is the region for customer C001?",
        },
        {
            "id": "adv_units",
            "name": "Case D: Incompatible Mixed Units Without Conversion",
            "files": {"products_units": ADVERSARIAL_DIR / "case_d_units" / "products_units.csv"},
            "question": "What is the total weight of all products?",
        },
        {
            "id": "adv_currency_no_fx",
            "name": "Case E: Mixed Currencies Without Exchange Rate Table",
            "files": {"sales_currencies": ADVERSARIAL_DIR / "case_e_currency" / "sales_currencies.csv"},
            "question": "What is the total revenue?",
        },
        {
            "id": "adv_currency_with_fx",
            "name": "Case E2: Mixed Currencies WITH Exchange Rate Table",
            "files": {
                "sales_curr": ADVERSARIAL_DIR / "case_e_currency" / "sales_currencies.csv",
                "exchange_rates": ADVERSARIAL_DIR / "case_e_currency" / "exchange_rates.csv"
            },
            "question": "What is the total revenue in USD?",
        },
        {
            "id": "adv_ambig_dates",
            "name": "Case F: Ambiguous Dates (DD/MM vs MM/DD)",
            "files": {"sales_ambig": ADVERSARIAL_DIR / "case_f_dates" / "sales_ambiguous_dates.csv"},
            "question": "What was the total revenue in February?",
        },
        {
            "id": "adv_unambig_dates",
            "name": "Case F2: Unambiguous Dates",
            "files": {"sales_unambig": ADVERSARIAL_DIR / "case_f_dates" / "sales_unambiguous_dates.csv"},
            "question": "What was the total amount?",
        },
        {
            "id": "adv_nulls",
            "name": "Case G: NULL Values in Aggregation Column",
            "files": {"sales_nulls": ADVERSARIAL_DIR / "case_g_nulls" / "sales_nulls.csv"},
            "question": "What is the total amount?",
        },
        {
            "id": "adv_contradict",
            "name": "Case H: Contradictory Multi-Table Information",
            "files": {
                "cust_v1": ADVERSARIAL_DIR / "case_h_contradictions" / "customers_v1.csv",
                "cust_v2": ADVERSARIAL_DIR / "case_h_contradictions" / "customers_v2.csv"
            },
            "question": "What is the credit limit for customer C001?",
        },
        {
            "id": "adv_missing_profit",
            "name": "Case K: Missing Metric (Profit)",
            "files": {"sales_no_profit": ADVERSARIAL_DIR / "case_k_missing_field" / "sales_no_profit.csv"},
            "question": "What was the total profit?",
        },
        {
            "id": "adv_nonexistent_entity",
            "name": "Case L1: Nonexistent Entity C999",
            "files": {"sales_clean": ADVERSARIAL_DIR / "case_a_clean" / "sales.csv"},
            "question": "What was the revenue for customer C999?",
        },
        {
            "id": "adv_nonexistent_year",
            "name": "Case L2: Nonexistent Year 2035",
            "files": {"sales_clean": ADVERSARIAL_DIR / "case_a_clean" / "sales.csv"},
            "question": "What was the total revenue in 2035?",
        },
    ]

    for sc in scenarios:
        print(f"\n>>> Running Scenario: {sc['name']}")
        _load_adversarial_dataset(sc["id"], sc["files"])
        await run_pipeline(sc["question"], sc["id"])

async def main():
    load_demo_data()
    print("=== VERITAS Proof-Carrying Data Analyst CLI ===")

    if len(sys.argv) > 1 and ("--adversarial" in sys.argv or "-a" in sys.argv):
        await run_adversarial_demo()
    elif len(sys.argv) > 1 and sys.argv[1] == "--demo":
        print("\nRunning automated verification on all required demo and refusal questions...\n")
        for q in REQUIRED_DEMO_QUESTIONS:
            await run_pipeline(q)
    elif len(sys.argv) > 1:
        custom_q = " ".join(sys.argv[1:])
        await run_pipeline(custom_q)
    else:
        # Interactive loop
        print("\nEnter a question (or 'adversarial' for adversarial suite, 'demo' for batch tests, 'exit' to quit):")
        while True:
            try:
                user_q = input("\nQuery > ").strip()
                if not user_q:
                    continue
                if user_q.lower() in ("exit", "quit"):
                    break
                if user_q.lower() == "adversarial":
                    await run_adversarial_demo()
                elif user_q.lower() == "demo":
                    for q in REQUIRED_DEMO_QUESTIONS:
                        await run_pipeline(q)
                else:
                    await run_pipeline(user_q)
            except (KeyboardInterrupt, EOFError):
                break

if __name__ == "__main__":
    asyncio.run(main())
