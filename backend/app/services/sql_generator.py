import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from app.models.schemas import QuestionPlan, SQLGenerationResult, TableProfile
from app.services.duckdb_service import duckdb_service
from app.services.ollama_service import ollama_service
from app.services.sql_validator import sql_validator

logger = logging.getLogger("veritas.sql_generator")

SQL_GENERATOR_SYSTEM_PROMPT = """You are a senior SQL database expert generating DuckDB SQL queries for a verified analytics engine.
Your sole job is to generate a precise, valid, read-only DuckDB SQL query that directly answers the user's question using ONLY the provided tables and columns.

CRITICAL RULES:
1. ONLY return a JSON object with this exact format:
{
  "sql": "SELECT ...",
  "explanation": "Brief explanation of the logic",
  "assumptions": ["Any specific assumptions made"]
}
2. Use DuckDB SQL syntax:
   - For year filtering on date strings or dates: Use (EXTRACT(year FROM CAST(date AS DATE)) = 2025) OR (date LIKE '2025%') OR (strftime(CAST(date AS DATE), '%Y') = '2025').
   - For string comparisons, be case-sensitive or use UPPER(col) = 'VAL' if appropriate.
   - For calculating total revenue: use SUM(amount) or SUM(quantity * unit_price) depending on available columns.
   - For counts: use COUNT(*) or COUNT(DISTINCT col).
   - For category ranking: use GROUP BY category ORDER BY SUM(...) DESC LIMIT 1.
   - MULTI-TABLE JOINS: If a column (e.g. customer_segment, customer_name, product_name) is in a different table than sales, you MUST write an explicit JOIN on the common key (e.g., FROM sales JOIN customers ON sales.customer_id = customers.customer_id). NEVER reference a column without including its table in FROM/JOIN!
   - CURRENCY CONVERSION: When converting currencies using an exchange rates table, JOIN on currency and compute SUM(sales_table.amount * exchange_rates.rate_to_usd).
3. NEVER hallucinate table or column names.
4. Only generate SELECT queries. NO INSERT, UPDATE, DELETE, DROP, CREATE, ALTER.
5. Do NOT include markdown text outside the JSON object.
"""

class SQLGenerator:
    def __init__(self, llm_service=ollama_service, validator=sql_validator, db=duckdb_service):
        self.llm = llm_service
        self.validator = validator
        self.db = db

    def _format_schema(self, tables: List[TableProfile]) -> str:
        lines = []
        for t in tables:
            lines.append(f"Table: {t.table}")
            lines.append("Columns:")
            for c in t.columns:
                sample_str = f" (samples: {c.sample_values[:3]})" if c.sample_values else ""
                lines.append(f"  - {c.name}: {c.type}{sample_str}")
            if t.primary_keys:
                lines.append(f"Primary Keys: {', '.join(t.primary_keys)}")
            if t.likely_join_keys:
                lines.append(f"Join Keys: {', '.join(t.likely_join_keys)}")
            if t.warnings:
                lines.append(f"Quality Warnings: {', '.join(t.warnings)}")
            lines.append("")
        return "\n".join(lines)

    async def generate_sql(
        self,
        question: str,
        tables: List[TableProfile],
        plan: QuestionPlan,
    ) -> SQLGenerationResult:
        """Generate structured SQL JSON from question and schema."""
        schema_text = self._format_schema(tables)

        prompt = f"""Available Database Schema:
{schema_text}

User Question: "{question}"
Query Plan Intent: {plan.intent}
Target Metric: {plan.metric}
Operation: {plan.operation}
Required Tables: {plan.required_tables}

Generate the exact DuckDB SQL query to answer the question.
Output JSON:
{{
  "sql": "SELECT ...",
  "explanation": "...",
  "assumptions": []
}}
"""

        raw_response = await self.llm.generate(
            prompt=prompt,
            system=SQL_GENERATOR_SYSTEM_PROMPT,
            format_json=True,
            temperature=0.0
        )

        data = self.llm.extract_json(raw_response)
        sql = data.get("sql", "").strip()
        explanation = data.get("explanation", "Query generated to answer the question.")
        assumptions = data.get("assumptions", [])

        # Clean sql if wrapped in code block
        if sql.startswith("```"):
            sql = re.sub(r"^```(?:sql)?\s*", "", sql)
            sql = re.sub(r"\s*```$", "", sql)

        return SQLGenerationResult(
            sql=sql.strip(),
            explanation=explanation,
            assumptions=assumptions
        )

    async def repair_sql(
        self,
        question: str,
        failed_sql: str,
        error_message: str,
        tables: List[TableProfile],
    ) -> SQLGenerationResult:
        """Repair a failed SQL query using LLM feedback."""
        schema_text = self._format_schema(tables)

        prompt = f"""The previous DuckDB SQL query failed execution with an error.

Schema:
{schema_text}

User Question: "{question}"
Failed SQL: {failed_sql}
Error: {error_message}

Fix the SQL query so that it executes successfully in DuckDB.
IMPORTANT: If the error says a column was not found in FROM clause, check which table in the schema contains that column and add a JOIN clause on the shared join key (e.g. sales.customer_id = customers.customer_id or sales.product_id = products.product_id).
Return ONLY JSON:
{{
  "sql": "SELECT ...",
  "explanation": "Fixed error by ...",
  "assumptions": []
}}
"""

        raw_response = await self.llm.generate(
            prompt=prompt,
            system=SQL_GENERATOR_SYSTEM_PROMPT,
            format_json=True,
            temperature=0.0
        )

        data = self.llm.extract_json(raw_response)
        sql = data.get("sql", "").strip()
        if sql.startswith("```"):
            sql = re.sub(r"^```(?:sql)?\s*", "", sql)
            sql = re.sub(r"\s*```$", "", sql)

        return SQLGenerationResult(
            sql=sql.strip(),
            explanation=data.get("explanation", "Repaired query."),
            assumptions=data.get("assumptions", [])
        )

# Global singleton
sql_generator = SQLGenerator()
