import json
import logging
import re
from typing import Any, Dict, List, Optional

from app.models.schemas import DatasetProfile, FilterCondition, QuestionPlan, TableProfile
from app.services.duckdb_service import duckdb_service
from app.services.ollama_service import ollama_service

logger = logging.getLogger("veritas.planner")

PLANNER_SYSTEM_PROMPT = """You are an expert Data Analyst Query Planner for a Proof-Carrying Data Analyst system.
Your job is to analyze the user question against the EXACT available database schema and determine:
1. Intent (aggregation, filtering, grouping, ranking, comparison, detail)
2. Operation (SUM, AVG, COUNT, MIN, MAX, or None)
3. Target metric / column name
4. Necessary filters (e.g. city = 'Chennai', year = 2025)
5. Required tables
6. Whether the question is ANSWERABLE with the provided schema.

CRITICAL RULES:
- Do NOT hallucinate columns or tables that do NOT exist in the schema.
- If the user asks for a metric or concept (e.g. "profit", "cost", "margin", "weather", "discount", "tax") that has NO matching column or mathematical formula in the schema, you MUST set "answerable": false and explain clearly in "reason".
- Never guess or pretend a column exists.
- Return ONLY valid JSON adhering strictly to the schema.
"""

class QuestionPlanner:
    def __init__(self, llm_service=ollama_service, db_service=duckdb_service):
        self.llm = llm_service
        self.db = db_service

    def _build_schema_summary(self, tables: List[TableProfile]) -> str:
        summary_lines = []
        for t in tables:
            cols = [f"{c.name} ({c.type})" for c in t.columns]
            summary_lines.append(f"Table '{t.table}' ({t.rows} rows):")
            summary_lines.append(f"  Columns: {', '.join(cols)}")
            if t.primary_keys:
                summary_lines.append(f"  Primary Keys: {', '.join(t.primary_keys)}")
            if t.likely_join_keys:
                summary_lines.append(f"  Join Keys: {', '.join(t.likely_join_keys)}")
        return "\n".join(summary_lines)

    async def plan_question(
        self,
        question: str,
        tables: List[TableProfile],
        dataset_profile: Optional[DatasetProfile] = None,
    ) -> QuestionPlan:
        """Analyze user question with deterministic adversarial checks + LLM semantic planning."""
        q_lower = question.lower()
        conn = self.db.get_connection()

        all_cols = set()
        for t in tables:
            for c in t.columns:
                all_cols.add(c.name.lower())

        # ==========================================
        # DETERMINISTIC PRE-CHECKS (PROMPT 3 RULES)
        # ==========================================

        # Check 1: Missing unsupported domain concepts (profit, cost, weather, etc.)
        unsupported_concepts = {
            "profit": ["profit", "cost", "cogs", "margin", "expenses"],
            "weather": ["weather", "temperature", "rain", "climate", "forecast"],
            "discount": ["discount", "coupon"],
            "tax": ["tax", "vat", "gst"],
        }
        for concept, keywords in unsupported_concepts.items():
            if any(kw in q_lower for kw in keywords):
                if not any(any(kw in col for kw in keywords) for col in all_cols):
                    return QuestionPlan(
                        intent="unanswerable",
                        answerable=False,
                        status="CANNOT_DETERMINE",
                        metric=concept,
                        reason=f"The dataset does not contain {concept} or cost information required to answer this question."
                    )

        # Check 2: Contradictory tables
        if dataset_profile and dataset_profile.contradictions:
            # If dataset has known contradictory tables on shared entities
            return QuestionPlan(
                intent="contradiction_detected",
                answerable=False,
                status="CANNOT_DETERMINE",
                reason=f"Conflicting data detected across tables: {dataset_profile.contradictions[0]}. Cannot provide an authoritative answer."
            )

        # Check 3: Duplicate Primary Key with conflicting attributes
        for t in tables:
            if t.has_duplicate_pk:
                return QuestionPlan(
                    intent="duplicate_pk_conflict",
                    answerable=False,
                    status="CANNOT_DETERMINE",
                    reason=f"Table '{t.table}' contains duplicate primary keys with conflicting attribute values. Cannot reliably determine correct entity attributes."
                )

        # Check 4: Mixed Incompatible Units without conversion
        for t in tables:
            if t.has_mixed_units:
                if any(w in q_lower for w in ["weight", "total", "sum", "average", "avg", "amount"]):
                    return QuestionPlan(
                        intent="mixed_units_error",
                        answerable=False,
                        status="CANNOT_DETERMINE",
                        metric="weight",
                        reason=f"Table '{t.table}' contains mixed incompatible units ({t.distinct_units}) without conversion factors. Cannot compute direct aggregation across incompatible units."
                    )

        # Check 5: Mixed Currencies
        for t in tables:
            if t.has_mixed_currencies:
                # Check if another table provides exchange rates
                has_fx_table = any(
                    "exchange" in ot.table.lower() or "rate" in [c.name.lower() for c in ot.columns]
                    for ot in tables
                )
                if not has_fx_table:
                    return QuestionPlan(
                        intent="mixed_currency_ambiguity",
                        answerable=False,
                        status="NEEDS_CLARIFICATION",
                        metric="currency",
                        reason=f"Table '{t.table}' contains mixed currencies ({t.distinct_currencies}) without an exchange rate table. Clarify target currency or provide conversion rates."
                    )

        # Check 6: Ambiguous Dates (DD/MM vs MM/DD)
        month_names = ["january", "february", "march", "april", "may", "june",
                       "july", "august", "september", "october", "november", "december",
                       "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
        asks_month = any(m in q_lower for m in month_names) or "month" in q_lower
        for t in tables:
            if t.has_ambiguous_dates and asks_month:
                return QuestionPlan(
                    intent="ambiguous_date_format",
                    answerable=False,
                    status="NEEDS_CLARIFICATION",
                    metric="date",
                    reason=f"Date column in table '{t.table}' has ambiguous formatting where day and month cannot be distinguished (e.g. '01/02/2025'). Clarify whether format is DD/MM/YYYY or MM/DD/YYYY."
                )

        # Check 7: Nonexistent Entity (e.g. C999, P999, O999)
        entity_matches = re.findall(r"\b([A-Za-z]\d{3,})\b", question)
        for ent in entity_matches:
            ent_upper = ent.upper()
            found_ent = False
            for t in tables:
                for c in t.columns:
                    try:
                        chk = conn.execute(
                            f"SELECT COUNT(*) FROM \"{t.table}\" WHERE UPPER(CAST(\"{c.name}\" AS VARCHAR)) = '{ent_upper}'"
                        ).fetchone()
                        if chk and chk[0] > 0:
                            found_ent = True
                            break
                    except Exception:
                        pass
                if found_ent:
                    break
            if not found_ent:
                return QuestionPlan(
                    intent="nonexistent_entity",
                    answerable=False,
                    status="CANNOT_DETERMINE",
                    missing_entity=ent_upper,
                    reason=f"Entity '{ent_upper}' does not exist in any dataset table."
                )

        # Check 8: Nonexistent Year / Future Date (e.g. 2035)
        year_matches = re.findall(r"\b(19\d\d|20\d\d)\b", question)
        for yr in year_matches:
            found_yr = False
            for t in tables:
                for c in t.columns:
                    if c.is_date or "date" in c.name.lower() or "year" in c.name.lower():
                        try:
                            chk = conn.execute(
                                f"SELECT COUNT(*) FROM \"{t.table}\" WHERE CAST(\"{c.name}\" AS VARCHAR) LIKE '%{yr}%'"
                            ).fetchone()
                            if chk and chk[0] > 0:
                                found_yr = True
                                break
                        except Exception:
                            pass
                if found_yr:
                    break
            if not found_yr and int(yr) > 2025:
                return QuestionPlan(
                    intent="nonexistent_date_range",
                    answerable=False,
                    status="CANNOT_DETERMINE",
                    metric="date",
                    reason=f"No data available for year {yr} in the dataset (time range does not cover {yr})."
                )

        # ==========================================
        # LLM QUERY PLANNING
        # ==========================================
        schema_text = self._build_schema_summary(tables)
        prompt = f"""Database Schema:
{schema_text}

User Question: "{question}"

Analyze the question and provide the plan as JSON with these keys:
{{
  "intent": "aggregation" | "filtering" | "grouping" | "ranking" | "detail",
  "operation": "SUM" | "AVG" | "COUNT" | "MIN" | "MAX" | null,
  "metric": "name of target column or metric",
  "filters": [
    {{"column": "column_name", "operator": "=", "value": "extracted_value"}}
  ],
  "required_tables": ["table_name"],
  "answerable": true | false,
  "ambiguities": ["any ambiguities or assumptions"],
  "reason": "If answerable is false, exact explanation of missing information. Otherwise null."
}}
"""

        try:
            raw_response = await self.llm.generate(
                prompt=prompt,
                system=PLANNER_SYSTEM_PROMPT,
                format_json=True,
                temperature=0.0
            )
            data = self.llm.extract_json(raw_response)

            filters = [
                FilterCondition(
                    column=f.get("column", ""),
                    operator=f.get("operator", "="),
                    value=f.get("value")
                )
                for f in data.get("filters", [])
            ]

            # Identify all tables mentioned or needed
            matched_tables = set(data.get("required_tables", []))
            for t in tables:
                for c in t.columns:
                    c_clean = c.name.lower()
                    if c_clean in q_lower or c_clean.replace("_", " ") in q_lower:
                        matched_tables.add(t.table)

            # Check if currency conversion table is needed
            if any(t.has_mixed_currencies for t in tables):
                for t in tables:
                    if "rate" in t.table.lower() or "exchange" in t.table.lower():
                        matched_tables.add(t.table)

            final_tables = list(matched_tables) if matched_tables else ([tables[0].table] if tables else [])

            ambiguities = data.get("ambiguities", [])
            if dataset_profile and dataset_profile.join_risks:
                ambiguities.extend(dataset_profile.join_risks)

            return QuestionPlan(
                intent=data.get("intent", "aggregation"),
                operation=data.get("operation"),
                metric=data.get("metric"),
                filters=filters,
                required_tables=final_tables,
                answerable=bool(data.get("answerable", True)),
                status="ANSWERABLE" if data.get("answerable", True) else "CANNOT_DETERMINE",
                ambiguities=ambiguities,
                reason=data.get("reason"),
            )

        except Exception as e:
            logger.error(f"Question planning LLM call failed: {e}")
            return QuestionPlan(
                intent="aggregation",
                operation="SUM" if "total" in q_lower else ("AVG" if "average" in q_lower else "COUNT"),
                required_tables=[tables[0].table] if tables else [],
                answerable=True,
                status="ANSWERABLE"
            )

# Global singleton
question_planner = QuestionPlanner()
