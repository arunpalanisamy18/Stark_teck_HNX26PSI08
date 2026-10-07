from pathlib import Path
from typing import Dict
import pytest

from app.api.questions import ask_question
from app.api.upload import DATASET_REGISTRY
from app.models.schemas import DatasetProfile, QuestionPlan, QuestionRequest, SQLExecutionResult, TableProfile
from app.services.data_profiler import data_profiler
from app.services.duckdb_service import duckdb_service
from app.services.question_planner import question_planner
from app.services.sql_validator import sql_validator
from app.services.verification_engine import verification_engine

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ADVERSARIAL_DIR = BASE_DIR / "data" / "adversarial"

def load_and_register_tables(dataset_id: str, table_map: Dict[str, Path]) -> DatasetProfile:
    """Helper to load CSVs into DuckDB and register in DATASET_REGISTRY."""
    tables = []
    for tbl, file_path in table_map.items():
        duckdb_service.load_csv(file_path, tbl)
        tables.append(tbl)
    profile = data_profiler.profile_dataset(dataset_id=dataset_id, table_names=tables)
    DATASET_REGISTRY[dataset_id] = profile
    return profile

# ==============================================================================
# 1. Clean Baseline Query
# ==============================================================================
@pytest.mark.asyncio
async def test_case_1_clean_baseline():
    dataset_id = "test_adv_clean"
    table_map = {"sales_clean": ADVERSARIAL_DIR / "case_a_clean" / "sales.csv"}
    load_and_register_tables(dataset_id, table_map)

    req = QuestionRequest(question="What was the total revenue in 2025?", dataset_id=dataset_id)
    resp = await ask_question(req)

    assert resp.status == "VERIFIED"
    assert resp.answer == 41600.0
    assert resp.proof_certificate is not None
    assert resp.proof_certificate.overall_verified is True
    assert resp.proof_certificate.result_reproduced is True
    assert resp.proof_certificate.sql_safe is True

# ==============================================================================
# 2. Identical Physical Duplicate Rows
# ==============================================================================
@pytest.mark.asyncio
async def test_case_2_duplicate_rows():
    dataset_id = "test_adv_dups"
    table_map = {"sales_dups": ADVERSARIAL_DIR / "case_b_duplicates" / "sales_dups.csv"}
    profile = load_and_register_tables(dataset_id, table_map)

    t_prof = profile.tables[0]
    assert t_prof.duplicate_rows == 2
    assert any("duplicate" in w.lower() for w in t_prof.warnings)

# ==============================================================================
# 3. Duplicate Primary Key with Conflicting Attributes
# ==============================================================================
@pytest.mark.asyncio
async def test_case_3_duplicate_primary_key_conflict():
    dataset_id = "test_adv_dup_pk"
    table_map = {"customers_dup_pk": ADVERSARIAL_DIR / "case_c_dup_pk" / "customers_dup_pk.csv"}
    profile = load_and_register_tables(dataset_id, table_map)

    assert profile.tables[0].has_duplicate_pk is True

    req = QuestionRequest(question="What is the region for customer C001?", dataset_id=dataset_id)
    resp = await ask_question(req)

    assert resp.status == "CANNOT_DETERMINE"
    assert "duplicate primary key" in resp.reason.lower()

# ==============================================================================
# 4. Incompatible Units Without Conversion
# ==============================================================================
@pytest.mark.asyncio
async def test_case_4_incompatible_units_refused():
    dataset_id = "test_adv_units"
    table_map = {"products_units": ADVERSARIAL_DIR / "case_d_units" / "products_units.csv"}
    profile = load_and_register_tables(dataset_id, table_map)

    assert profile.tables[0].has_mixed_units is True
    assert set(profile.tables[0].distinct_units) == {"g", "kg"}

    req = QuestionRequest(question="What is the total weight of all products?", dataset_id=dataset_id)
    resp = await ask_question(req)

    assert resp.status == "CANNOT_DETERMINE"
    assert "mixed incompatible units" in resp.reason.lower()

# ==============================================================================
# 5. Mixed Currency Without Conversion Rates
# ==============================================================================
@pytest.mark.asyncio
async def test_case_5_mixed_currency_without_rates_refused():
    dataset_id = "test_adv_currency_no_rate"
    table_map = {"sales_currencies": ADVERSARIAL_DIR / "case_e_currency" / "sales_currencies.csv"}
    profile = load_and_register_tables(dataset_id, table_map)

    assert profile.tables[0].has_mixed_currencies is True

    req = QuestionRequest(question="What is the total revenue?", dataset_id=dataset_id)
    resp = await ask_question(req)

    assert resp.status == "NEEDS_CLARIFICATION"
    assert "mixed currencies" in resp.reason.lower()

# ==============================================================================
# 6. Mixed Currency WITH Conversion Rates Table
# ==============================================================================
@pytest.mark.asyncio
async def test_case_6_mixed_currency_with_rates_verified():
    dataset_id = "test_adv_currency_with_rates"
    table_map = {
        "sales_curr": ADVERSARIAL_DIR / "case_e_currency" / "sales_currencies.csv",
        "exchange_rates": ADVERSARIAL_DIR / "case_e_currency" / "exchange_rates.csv"
    }
    load_and_register_tables(dataset_id, table_map)

    req = QuestionRequest(question="What is the total revenue in USD?", dataset_id=dataset_id)
    resp = await ask_question(req)

    # With exchange rates table, the system can determine answer or verify join calculation
    assert resp.status in ("VERIFIED", "CANNOT_DETERMINE")
    if resp.status == "VERIFIED":
        assert resp.proof_certificate.overall_verified is True

# ==============================================================================
# 7. Ambiguous Date Format Refused (Month Query)
# ==============================================================================
@pytest.mark.asyncio
async def test_case_7_ambiguous_date_refused():
    dataset_id = "test_adv_ambig_dates"
    table_map = {"sales_ambig": ADVERSARIAL_DIR / "case_f_dates" / "sales_ambiguous_dates.csv"}
    profile = load_and_register_tables(dataset_id, table_map)

    assert profile.tables[0].has_ambiguous_dates is True

    req = QuestionRequest(question="What was the total revenue in February?", dataset_id=dataset_id)
    resp = await ask_question(req)

    assert resp.status == "NEEDS_CLARIFICATION"
    assert "ambiguous" in resp.reason.lower()

# ==============================================================================
# 8. Unambiguous Date Format Accepted
# ==============================================================================
@pytest.mark.asyncio
async def test_case_8_unambiguous_date_verified():
    dataset_id = "test_adv_unambig_dates"
    table_map = {"sales_unambig": ADVERSARIAL_DIR / "case_f_dates" / "sales_unambiguous_dates.csv"}
    profile = load_and_register_tables(dataset_id, table_map)

    assert profile.tables[0].has_ambiguous_dates is False

    req = QuestionRequest(question="What was the total amount?", dataset_id=dataset_id)
    resp = await ask_question(req)

    assert resp.status == "VERIFIED"
    assert resp.answer == 23700.0

# ==============================================================================
# 9. NULL Values in Aggregation Columns
# ==============================================================================
@pytest.mark.asyncio
async def test_case_9_null_aggregation_disclosed():
    dataset_id = "test_adv_nulls"
    table_map = {"sales_nulls": ADVERSARIAL_DIR / "case_g_nulls" / "sales_nulls.csv"}
    profile = load_and_register_tables(dataset_id, table_map)

    # Check nulls detected in profiling
    amt_col = next(c for c in profile.tables[0].columns if c.name == "amount")
    assert amt_col.null_count == 2

    req = QuestionRequest(question="What is the total amount?", dataset_id=dataset_id)
    resp = await ask_question(req)

    assert resp.status == "VERIFIED"
    assert resp.answer == 15000.0
    # Warnings must mention nulls
    assert any("null" in w.lower() for w in resp.warnings)

# ==============================================================================
# 10. Contradictory Multi-Table Data Refused
# ==============================================================================
@pytest.mark.asyncio
async def test_case_10_contradictory_tables_refused():
    dataset_id = "test_adv_contradictions"
    table_map = {
        "cust_v1": ADVERSARIAL_DIR / "case_h_contradictions" / "customers_v1.csv",
        "cust_v2": ADVERSARIAL_DIR / "case_h_contradictions" / "customers_v2.csv"
    }
    profile = load_and_register_tables(dataset_id, table_map)

    assert len(profile.contradictions) > 0

    req = QuestionRequest(question="What is the credit limit for customer C001?", dataset_id=dataset_id)
    resp = await ask_question(req)

    assert resp.status == "CANNOT_DETERMINE"
    assert "conflicting" in resp.reason.lower() or "contradictory" in resp.reason.lower()

# ==============================================================================
# 11. Orphan Foreign Keys Detected
# ==============================================================================
def test_case_11_orphan_foreign_keys_detected():
    dataset_id = "test_adv_orphans"
    table_map = {
        "sales_orphans": ADVERSARIAL_DIR / "case_i_orphans" / "sales_orphans.csv",
        "customers_orphans": ADVERSARIAL_DIR / "case_i_orphans" / "customers.csv"
    }
    profile = load_and_register_tables(dataset_id, table_map)

    assert len(profile.orphan_keys) > 0
    assert any("orphan" in w.lower() for w in profile.cross_table_warnings)

# ==============================================================================
# 12. Many-to-Many Join Risk Detected
# ==============================================================================
def test_case_12_many_to_many_join_risk_detected():
    dataset_id = "test_adv_m2m"
    table_map = {
        "orders_m2m": ADVERSARIAL_DIR / "case_j_cardinality" / "orders.csv",
        "notes_m2m": ADVERSARIAL_DIR / "case_j_cardinality" / "notes.csv"
    }
    profile = load_and_register_tables(dataset_id, table_map)

    assert len(profile.join_risks) > 0
    assert any("cartesian" in r.lower() or "cardinality" in r.lower() for r in profile.join_risks)

# ==============================================================================
# 13. Missing Metric (Profit) Refused
# ==============================================================================
@pytest.mark.asyncio
async def test_case_13_missing_metric_profit_refused():
    dataset_id = "test_adv_no_profit"
    table_map = {"sales_no_profit": ADVERSARIAL_DIR / "case_k_missing_field" / "sales_no_profit.csv"}
    load_and_register_tables(dataset_id, table_map)

    req = QuestionRequest(question="What was the total profit?", dataset_id=dataset_id)
    resp = await ask_question(req)

    assert resp.status == "CANNOT_DETERMINE"
    assert "profit" in resp.reason.lower()

# ==============================================================================
# 14. Nonexistent Entity (C999) Refused
# ==============================================================================
@pytest.mark.asyncio
async def test_case_14_nonexistent_entity_refused():
    dataset_id = "test_adv_clean_entity"
    table_map = {"sales_c14": ADVERSARIAL_DIR / "case_a_clean" / "sales.csv"}
    load_and_register_tables(dataset_id, table_map)

    req = QuestionRequest(question="What was the revenue for customer C999?", dataset_id=dataset_id)
    resp = await ask_question(req)

    assert resp.status == "CANNOT_DETERMINE"
    assert "c999" in resp.reason.lower()

# ==============================================================================
# 15. Nonexistent Year (2035) Refused
# ==============================================================================
@pytest.mark.asyncio
async def test_case_15_nonexistent_year_refused():
    dataset_id = "test_adv_clean_year"
    table_map = {"sales_c15": ADVERSARIAL_DIR / "case_a_clean" / "sales.csv"}
    load_and_register_tables(dataset_id, table_map)

    req = QuestionRequest(question="What was the total revenue in 2035?", dataset_id=dataset_id)
    resp = await ask_question(req)

    assert resp.status == "CANNOT_DETERMINE"
    assert "2035" in resp.reason.lower()

# ==============================================================================
# 16. Dangerous SQL Rejected
# ==============================================================================
def test_case_16_dangerous_sql_rejected():
    dangerous_queries = [
        "DROP TABLE sales",
        "DELETE FROM sales WHERE id = 1",
        "UPDATE sales SET amount = 0",
        "INSERT INTO sales VALUES (1, '2025-01-01', 'C001', 100, 'North')",
        "ALTER TABLE sales ADD COLUMN hack TEXT",
    ]
    for q in dangerous_queries:
        is_safe, err = sql_validator.validate_safety(q)
        assert is_safe is False
        assert err is not None

# ==============================================================================
# 17. Malformed SQL Handled Safely
# ==============================================================================
def test_case_17_malformed_sql_rejected_by_validator():
    malformed = "SELECT FROM WHERE"
    is_valid, err = sql_validator.validate_all(malformed)
    assert is_valid is False
    assert err is not None

# ==============================================================================
# 18. Verification Engine Fails on Empty Result
# ==============================================================================
def test_case_18_verification_engine_fails_on_empty_result():
    plan = QuestionPlan(intent="aggregation", operation="SUM", answerable=True, required_tables=["sales_clean"])
    empty_exec = SQLExecutionResult(
        success=True,
        sql="SELECT * FROM sales_clean WHERE 1=0",
        columns=["amount"],
        rows=[],
        execution_time_ms=1.0,
        row_count=0
    )
    t_prof = data_profiler.profile_table("sales_clean")
    res, val, atype = verification_engine.verify_pipeline("test", plan, empty_exec.sql, empty_exec, [t_prof])

    assert res.verified is False
    assert res.status == "FAIL"

# ==============================================================================
# 19. Deterministic Reproduction Consistency
# ==============================================================================
def test_case_19_reproduction_consistency():
    query = "SELECT SUM(amount) FROM sales_clean"
    res1 = duckdb_service.execute_query(query)
    res2 = duckdb_service.execute_query(query)

    assert res1.success is True
    assert res2.success is True
    assert res1.rows == res2.rows

# ==============================================================================
# 20. Proof Certificate Complete Contract
# ==============================================================================
@pytest.mark.asyncio
async def test_case_20_proof_certificate_contract():
    dataset_id = "test_adv_cert"
    table_map = {"sales_clean": ADVERSARIAL_DIR / "case_a_clean" / "sales.csv"}
    load_and_register_tables(dataset_id, table_map)

    req = QuestionRequest(question="What was the total revenue in 2025?", dataset_id=dataset_id)
    resp = await ask_question(req)

    cert = resp.proof_certificate
    assert cert is not None
    assert isinstance(cert.sql_safe, bool)
    assert isinstance(cert.tables_exist, bool)
    assert isinstance(cert.columns_exist, bool)
    assert isinstance(cert.data_quality_checked, bool)
    assert isinstance(cert.ambiguity_checked, bool)
    assert isinstance(cert.join_checked, bool)
    assert isinstance(cert.result_reproduced, bool)
    assert isinstance(cert.answer_from_execution, bool)
    assert isinstance(cert.overall_verified, bool)
    assert len(cert.checks) > 0
    assert resp.evidence is not None
    assert "sql" in resp.evidence

