import logging
import re
from typing import List, Optional, Set, Tuple

from app.services.duckdb_service import duckdb_service

logger = logging.getLogger("veritas.validator")

# Forbidden SQL keywords / statements
DISALLOWED_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE",
    "COPY", "ATTACH", "DETACH", "INSTALL", "LOAD", "EXPORT",
    "PRAGMA", "CALL", "EXECUTE", "PREPARE", "DEALLOCATE",
    "SYSTEM", "WRITE_CSV", "WRITE_PARQUET", "COPY_TO", "SET "
]

class SQLValidator:
    def __init__(self, db_service=duckdb_service):
        self.db = db_service

    def validate_safety(self, sql: str) -> Tuple[bool, Optional[str]]:
        """Ensure SQL is strictly a read-only query (SELECT or WITH)."""
        clean_sql = sql.strip().rstrip(";")
        if not clean_sql:
            return False, "SQL statement is empty."

        # Check for multiple statements (semicolon injection)
        # Allow semicolons only at the very end
        statements = [s.strip() for s in clean_sql.split(";") if s.strip()]
        if len(statements) > 1:
            return False, "Multiple SQL statements are not permitted."

        upper_sql = f" {clean_sql.upper()} "

        # Must start with SELECT or WITH
        first_token = clean_sql.split()[0].upper()
        if first_token not in ("SELECT", "WITH"):
            return False, f"Only SELECT and WITH statements are allowed. Got '{first_token}'."

        # Check for disallowed mutation / system keywords
        for kw in DISALLOWED_KEYWORDS:
            pattern = rf"\b{kw}\b"
            if re.search(pattern, upper_sql, re.IGNORECASE):
                return False, f"Dangerous or unauthorized keyword '{kw}' detected."

        # Prevent file system reads inside query (read_csv, read_parquet, etc.)
        file_functions = ["read_csv", "read_parquet", "read_json", "scan_csv", "glob("]
        for fn in file_functions:
            if fn.lower() in clean_sql.lower():
                return False, f"Direct filesystem function '{fn}' is not permitted in generated query."

        return True, None

    def validate_schema(self, sql: str, allowed_tables: Optional[List[str]] = None) -> Tuple[bool, Optional[str]]:
        """Validate query against DuckDB catalog using EXPLAIN (verifies table & column existence)."""
        conn = self.db.get_connection()
        try:
            # EXPLAIN checks syntax, table references, and column types
            conn.execute(f"EXPLAIN {sql}")
            return True, None
        except Exception as e:
            err_msg = str(e)
            logger.warning(f"SQL Schema validation failed: {err_msg}")
            return False, f"SQL validation error: {err_msg}"

    def validate_all(self, sql: str, allowed_tables: Optional[List[str]] = None) -> Tuple[bool, Optional[str]]:
        """Run complete safety and schema validation."""
        is_safe, safe_err = self.validate_safety(sql)
        if not is_safe:
            return False, safe_err

        is_valid_schema, schema_err = self.validate_schema(sql, allowed_tables)
        if not is_valid_schema:
            return False, schema_err

        return True, None

# Global singleton
sql_validator = SQLValidator()

