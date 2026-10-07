import logging
import uuid
from typing import Dict, List
from fastapi import APIRouter, HTTPException

from app.api.upload import DATASET_REGISTRY
from app.models.schemas import (
    FinalAnswerResponse,
    ProofCertificate,
    QuestionPlan,
    QuestionRequest,
    SQLGenerationResult,
)
from app.services.duckdb_service import duckdb_service
from app.services.question_planner import question_planner
from app.services.sql_generator import sql_generator
from app.services.sql_validator import sql_validator
from app.services.verification_engine import verification_engine

logger = logging.getLogger("veritas.questions")

router = APIRouter(prefix="/api", tags=["Questions"])

RESULTS_REGISTRY: Dict[str, FinalAnswerResponse] = {}

@router.post("/question", response_model=FinalAnswerResponse)
async def ask_question(request: QuestionRequest):
    """
    Execute the full end-to-end Proof-Carrying Data Analyst pipeline:
    Question -> Plan -> Answerability -> SQL Generation -> Validation ->
    DuckDB Execution -> SQL Repair (if needed) -> 10-Point Verification ->
    Reproduction -> Verified Result / Refusal.
    """
    dataset_id = request.dataset_id
    question = request.question.strip()
    result_id = str(uuid.uuid4())[:8]

    if dataset_id not in DATASET_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")

    dataset_profile = DATASET_REGISTRY[dataset_id]
    tables = dataset_profile.tables

    # 1. QUESTION ANALYSIS & ANSWERABILITY CHECK
    plan: QuestionPlan = await question_planner.plan_question(
        question=question,
        tables=tables,
        dataset_profile=dataset_profile,
    )

    # 2. STRICT REFUSAL FOR UNANSWERABLE OR AMBIGUOUS QUESTIONS
    if not plan.answerable:
        refusal_res = FinalAnswerResponse(
            result_id=result_id,
            dataset_id=dataset_id,
            question=question,
            status=plan.status if plan.status in ("CANNOT_DETERMINE", "NEEDS_CLARIFICATION") else "CANNOT_DETERMINE",
            answer=None,
            answer_type="null",
            sql=None,
            execution=None,
            verification={
                "verified": False,
                "status": "FAIL",
                "checks": [],
                "message": plan.reason or "Question cannot be answered from the provided dataset."
            },
            proof_certificate=ProofCertificate(
                sql_safe=False,
                tables_exist=True,
                columns_exist=False,
                data_quality_checked=True,
                ambiguity_checked=True,
                join_checked=True,
                result_reproduced=False,
                answer_from_execution=False,
                overall_verified=False,
                checks=[],
                message=plan.reason or "Refusal: computation could not proceed due to ambiguity or missing information."
            ),
            warnings=dataset_profile.cross_table_warnings,
            assumptions=plan.ambiguities,
            reason=plan.reason or "The dataset does not contain sufficient columns or information to answer this question.",
            missing_information=[plan.metric or plan.missing_entity or "required attribute/metrics"]
        )
        RESULTS_REGISTRY[result_id] = refusal_res
        return refusal_res

    # 3. SQL GENERATION
    gen_result: SQLGenerationResult = await sql_generator.generate_sql(question, tables, plan)
    current_sql = gen_result.sql

    # 4. VALIDATION & EXECUTION WITH AT MOST 2 REPAIR ATTEMPTS
    max_attempts = 3  # 1 initial + 2 repairs
    execution_result = None
    all_warnings: List[str] = []

    for attempt in range(max_attempts):
        is_valid, val_err = sql_validator.validate_all(current_sql)
        if is_valid:
            execution_result = duckdb_service.execute_query(current_sql)
            if execution_result.success:
                break
            else:
                err_msg = execution_result.error or "Execution error"
        else:
            err_msg = val_err or "Validation error"

        logger.warning(f"SQL attempt {attempt + 1} failed: {err_msg}. Triggering repair...")
        all_warnings.append(f"Attempt {attempt + 1} failed: {err_msg}")

        if attempt < max_attempts - 1:
            repair_res = await sql_generator.repair_sql(
                question=question,
                failed_sql=current_sql,
                error_message=err_msg,
                tables=tables
            )
            current_sql = repair_res.sql

    if execution_result is None or not execution_result.success:
        failed_res = FinalAnswerResponse(
            result_id=result_id,
            dataset_id=dataset_id,
            question=question,
            status="FAILED",
            answer=None,
            answer_type="null",
            sql=current_sql,
            execution={
                "success": False,
                "error": execution_result.error if execution_result else "Validation rejected SQL"
            },
            verification={"verified": False, "status": "FAIL"},
            proof_certificate=ProofCertificate(
                sql_safe=False,
                overall_verified=False,
                message="Execution failure"
            ),
            warnings=all_warnings,
            assumptions=gen_result.assumptions,
            reason="Generated computation could not be executed reliably after repair attempts."
        )
        RESULTS_REGISTRY[result_id] = failed_res
        return failed_res

    # 5. INDEPENDENT VERIFICATION & REPRODUCTION CHECK
    verification_res, final_val, answer_type = verification_engine.verify_pipeline(
        question=question,
        plan=plan,
        sql=current_sql,
        first_execution=execution_result,
        tables=tables
    )

    # 6. ASSEMBLE VERIFIED FINAL ANSWER CONTRACT
    final_status = "VERIFIED" if verification_res.verified else "FAILED"

    # Collect dataset-level warnings relevant to query
    dataset_warnings = list(dataset_profile.cross_table_warnings)
    for t in tables:
        dataset_warnings.extend(t.warnings)

    evidence = {
        "sql": current_sql,
        "execution_time_ms": execution_result.execution_time_ms,
        "row_count": execution_result.row_count,
        "columns": execution_result.columns,
        "sample_rows": execution_result.rows[:5] if execution_result.rows else [],
    }

    response = FinalAnswerResponse(
        result_id=result_id,
        dataset_id=dataset_id,
        question=question,
        status=final_status,
        answer=final_val,
        answer_type=answer_type,
        sql=current_sql,
        execution={
            "success": execution_result.success,
            "columns": execution_result.columns,
            "rows": execution_result.rows,
            "row_count": execution_result.row_count,
            "execution_time_ms": execution_result.execution_time_ms,
        },
        verification=verification_res.model_dump(),
        proof_certificate=verification_res.certificate,
        evidence=evidence,
        warnings=dataset_warnings,
        assumptions=gen_result.assumptions,
        reason=None if verification_res.verified else "Independent verification failed reproduction or checks."
    )

    RESULTS_REGISTRY[result_id] = response
    return response

@router.get("/result/{result_id}", response_model=FinalAnswerResponse)
async def get_result(result_id: str):
    """Retrieve an existing computation result and verification certificate."""
    if result_id not in RESULTS_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Result '{result_id}' not found.")
    return RESULTS_REGISTRY[result_id]
