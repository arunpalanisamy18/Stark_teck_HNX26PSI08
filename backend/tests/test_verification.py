import pytest
from app.config import DEMO_DIR
from app.models.schemas import QuestionPlan
from app.services.data_profiler import data_profiler
from app.services.duckdb_service import duckdb_service
from app.services.verification_engine import verification_engine

@pytest.fixture(autouse=True)
def setup_db():
    duckdb_service.load_csv(DEMO_DIR / "sales.csv", "sales")

def test_verification_engine_pass():
    profile = data_profiler.profile_table("sales")
    sql = "SELECT SUM(amount) AS total_revenue FROM sales"
    first_exec = duckdb_service.execute_query(sql)
    assert first_exec.success is True

    plan = QuestionPlan(
        intent="aggregation",
        operation="SUM",
        metric="amount",
        required_tables=["sales"],
        answerable=True
    )

    ver_res, final_val, answer_type = verification_engine.verify_pipeline(
        question="What is the total revenue?",
        plan=plan,
        sql=sql,
        first_execution=first_exec,
        tables=[profile]
    )

    assert ver_res.verified is True
    assert ver_res.status == "PASS"
    assert answer_type == "number"
    assert isinstance(final_val, (int, float))
    assert final_val == first_exec.rows[0][0]

    # Verify check names include reproduction
    check_names = [c.name for c in ver_res.checks]
    assert "Independent result reproduction" in check_names
    reprod_check = next(c for c in ver_res.checks if c.name == "Independent result reproduction")
    assert reprod_check.status == "PASS"

def test_verification_engine_fails_on_empty_or_broken_sql():
    profile = data_profiler.profile_table("sales")
    sql = "SELECT * FROM sales WHERE amount < 0"
    first_exec = duckdb_service.execute_query(sql)

    plan = QuestionPlan(
        intent="filtering",
        required_tables=["sales"],
        answerable=True
    )

    ver_res, final_val, answer_type = verification_engine.verify_pipeline(
        question="Find negative sales",
        plan=plan,
        sql=sql,
        first_execution=first_exec,
        tables=[profile]
    )

    assert ver_res.verified is False
    assert ver_res.status == "FAIL"

