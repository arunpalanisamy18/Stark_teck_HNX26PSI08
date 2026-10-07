import pytest
from app.api.questions import ask_question
from app.api.upload import DATASET_REGISTRY
from app.config import DEMO_DIR
from app.main import load_demo_data
from app.models.schemas import QuestionRequest
from app.services.data_profiler import data_profiler
from app.services.duckdb_service import duckdb_service
from app.services.question_planner import question_planner

@pytest.fixture(autouse=True)
def setup_environment():
    load_demo_data()

@pytest.mark.asyncio
async def test_question_planning_and_answerability():
    tables = [data_profiler.profile_table("sales")]

    # Answerable
    plan = await question_planner.plan_question("What is the total revenue?", tables)
    assert plan.answerable is True

    # Unanswerable (profit not in dataset)
    plan_unanswerable = await question_planner.plan_question("What was the profit in 2025?", tables)
    assert plan_unanswerable.answerable is False
    assert "profit" in (plan_unanswerable.reason or "").lower() or "cost" in (plan_unanswerable.reason or "").lower()

@pytest.mark.asyncio
async def test_refusal_unanswerable_profit():
    req = QuestionRequest(question="What was the profit in 2025?", dataset_id="demo")
    resp = await ask_question(req)

    assert resp.status == "CANNOT_DETERMINE"
    assert resp.answer is None
    assert resp.reason is not None

@pytest.mark.asyncio
async def test_refusal_unanswerable_weather():
    req = QuestionRequest(
        question="What was the weather in Chennai on the date of the highest order?",
        dataset_id="demo"
    )
    resp = await ask_question(req)

    assert resp.status == "CANNOT_DETERMINE"
    assert resp.answer is None
    assert "weather" in (resp.reason or "").lower()

@pytest.mark.asyncio
async def test_e2e_total_revenue_in_2025():
    req = QuestionRequest(question="What was the total revenue in 2025?", dataset_id="demo")
    resp = await ask_question(req)

    assert resp.status == "VERIFIED"
    assert resp.answer is not None
    assert resp.answer_type == "number"
    assert resp.sql is not None
    assert resp.verification["verified"] is True
    assert resp.verification["status"] == "PASS"

    # Verify DuckDB actually executed it and calculated the answer
    duck_calc = duckdb_service.execute_query(resp.sql)
    assert duck_calc.success is True
    assert duck_calc.rows[0][0] == resp.answer

@pytest.mark.asyncio
async def test_multi_table_join_query():
    # Customer segment query requires joining sales and customers
    req = QuestionRequest(
        question="What is the total revenue by customer segment?",
        dataset_id="demo"
    )
    resp = await ask_question(req)

    assert resp.status == "VERIFIED"
    assert resp.sql is not None
    assert "join" in resp.sql.lower() or "from sales, customers" in resp.sql.lower()
    assert resp.verification["verified"] is True

