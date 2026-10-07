import pytest
from app.config import DEMO_DIR
from app.models.schemas import QuestionPlan
from app.services.data_profiler import data_profiler
from app.services.duckdb_service import duckdb_service
from app.services.sql_generator import sql_generator
from app.services.sql_validator import sql_validator

@pytest.fixture(autouse=True)
def setup_test_db():
    duckdb_service.load_csv(DEMO_DIR / "sales.csv", "sales")

def test_duckdb_query_execution():
    res = duckdb_service.execute_query("SELECT SUM(amount) AS total FROM sales")
    assert res.success is True
    assert res.columns == ["total"]
    assert len(res.rows) == 1
    assert res.rows[0][0] > 0
    assert res.execution_time_ms >= 0

def test_sql_validation_allowed_queries():
    valid_sqls = [
        "SELECT * FROM sales",
        "SELECT city, SUM(amount) FROM sales GROUP BY city",
        "WITH cte AS (SELECT * FROM sales) SELECT COUNT(*) FROM cte",
    ]
    for sql in valid_sqls:
        is_valid, err = sql_validator.validate_all(sql)
        assert is_valid is True, f"Failed for {sql}: {err}"

def test_dangerous_sql_rejection():
    dangerous_sqls = [
        "DROP TABLE sales",
        "DELETE FROM sales WHERE 1=1",
        "INSERT INTO sales VALUES ('1','2','3','2025-01-01','X','Y',1,100)",
        "ALTER TABLE sales ADD COLUMN hack TEXT",
        "SELECT * FROM read_csv('/etc/passwd')",
        "SELECT * FROM sales; DROP TABLE sales",
        "COPY sales TO 'output.csv'",
    ]
    for sql in dangerous_sqls:
        is_valid, err = sql_validator.validate_all(sql)
        assert is_valid is False, f"Expected rejection for: {sql}"

def test_sql_execution_failure_handling():
    res = duckdb_service.execute_query("SELECT non_existent_col FROM sales")
    assert res.success is False
    assert "Referenced column \"non_existent_col\" not found" in res.error or "Binder Error" in res.error

@pytest.mark.asyncio
async def test_sql_repair_flow():
    profile = data_profiler.profile_table("sales")
    failed_sql = "SELECT SUM(non_existent_column) FROM sales"
    error_msg = "Referenced column non_existent_column not found"

    repair_result = await sql_generator.repair_sql(
        question="What is the total revenue?",
        failed_sql=failed_sql,
        error_message=error_msg,
        tables=[profile]
    )
    assert repair_result.sql is not None
    assert "amount" in repair_result.sql.lower()

