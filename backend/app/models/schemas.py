from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

# Health Check
class HealthResponse(BaseModel):
    status: str
    ollama: str
    model: str
    duckdb: str

# Column & Table Profiling
class ColumnProfile(BaseModel):
    name: str
    type: str
    null_count: int
    null_percentage: float
    unique_count: int
    sample_values: List[Any] = Field(default_factory=list)
    is_numeric: bool = False
    is_date: bool = False
    is_categorical: bool = False
    is_primary_key: bool = False
    unit_or_currency: Optional[str] = None

class TableProfile(BaseModel):
    table: str
    rows: int
    columns: List[ColumnProfile]
    duplicate_rows: int = 0
    primary_keys: List[str] = Field(default_factory=list)
    likely_join_keys: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    has_duplicate_pk: bool = False
    has_mixed_units: bool = False
    has_mixed_currencies: bool = False
    has_ambiguous_dates: bool = False
    distinct_units: List[str] = Field(default_factory=list)
    distinct_currencies: List[str] = Field(default_factory=list)
    ambiguous_date_cols: List[str] = Field(default_factory=list)

class DatasetProfile(BaseModel):
    dataset_id: str
    tables: List[TableProfile]
    total_rows: int
    created_at: str
    cross_table_warnings: List[str] = Field(default_factory=list)
    orphan_keys: Dict[str, Any] = Field(default_factory=dict)
    contradictions: List[str] = Field(default_factory=list)
    join_risks: List[str] = Field(default_factory=list)

# Question & Planning
class QuestionRequest(BaseModel):
    question: str
    dataset_id: str

class FilterCondition(BaseModel):
    column: str
    operator: str
    value: Any

class QuestionPlan(BaseModel):
    intent: str
    operation: Optional[str] = None
    metric: Optional[str] = None
    filters: List[FilterCondition] = Field(default_factory=list)
    required_tables: List[str] = Field(default_factory=list)
    answerable: bool = True
    status: str = "ANSWERABLE"  # ANSWERABLE / CANNOT_DETERMINE / NEEDS_CLARIFICATION
    missing_entity: Optional[str] = None
    ambiguities: List[str] = Field(default_factory=list)
    reason: Optional[str] = None

# SQL Generation & Execution
class SQLGenerationResult(BaseModel):
    sql: str
    explanation: str
    assumptions: List[str] = Field(default_factory=list)

class SQLExecutionResult(BaseModel):
    success: bool
    sql: str
    columns: List[str] = Field(default_factory=list)
    rows: List[List[Any]] = Field(default_factory=list)
    execution_time_ms: float = 0.0
    row_count: int = 0
    error: Optional[str] = None

# Verification
class VerificationCheck(BaseModel):
    name: str
    status: str  # PASS / FAIL / WARN
    details: Optional[str] = None

class ProofCertificate(BaseModel):
    sql_safe: bool = False
    tables_exist: bool = False
    columns_exist: bool = False
    data_quality_checked: bool = False
    ambiguity_checked: bool = False
    join_checked: bool = False
    result_reproduced: bool = False
    answer_from_execution: bool = False
    overall_verified: bool = False
    checks: List[VerificationCheck] = Field(default_factory=list)
    message: Optional[str] = None

class VerificationResult(BaseModel):
    verified: bool
    status: str  # PASS / FAIL
    checks: List[VerificationCheck] = Field(default_factory=list)
    message: Optional[str] = None
    certificate: Optional[ProofCertificate] = None

# Final Result Contract
class FinalAnswerResponse(BaseModel):
    result_id: str
    dataset_id: str
    question: str
    status: str  # VERIFIED / CANNOT_DETERMINE / NEEDS_CLARIFICATION / FAILED
    answer: Optional[Union[int, float, str, List[Any], Dict[str, Any]]] = None
    answer_type: Optional[str] = None  # number, string, table, list, null
    sql: Optional[str] = None
    execution: Optional[Dict[str, Any]] = None
    verification: Optional[Dict[str, Any]] = None
    proof_certificate: Optional[ProofCertificate] = None
    evidence: Optional[Dict[str, Any]] = None
    warnings: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    reason: Optional[str] = None
    missing_information: List[str] = Field(default_factory=list)


