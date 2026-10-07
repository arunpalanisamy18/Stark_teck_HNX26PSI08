import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
import duckdb

from app.models.schemas import SQLExecutionResult

logger = logging.getLogger("veritas.duckdb")

class DuckDBService:
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._conn = duckdb.connect(database=db_path, read_only=False)
        logger.info(f"Connected to DuckDB (path: {db_path})")

    def get_connection(self) -> duckdb.DuckDBPyConnection:
        """Return the active connection."""
        return self._conn

    def is_available(self) -> bool:
        """Check if DuckDB connection is healthy and responsive."""
        try:
            res = self._conn.execute("SELECT 1 AS health").fetchone()
            return res is not None and res[0] == 1
        except Exception as e:
            logger.error(f"DuckDB health check failed: {e}")
            return False

    def list_tables(self) -> List[str]:
        """List all tables loaded in DuckDB."""
        try:
            rel = self._conn.execute("SHOW TABLES").fetchall()
            return [row[0] for row in rel]
        except Exception as e:
            logger.error(f"Error listing tables: {e}")
            return []

    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists."""
        tables = [t.lower() for t in self.list_tables()]
        return table_name.lower() in tables

    def get_table_schema(self, table_name: str) -> List[Dict[str, str]]:
        """Return column names and types for a table."""
        try:
            rel = self._conn.execute(f"DESCRIBE \"{table_name}\"").fetchall()
            # DuckDB DESCRIBE columns: column_name, column_type, null, key, default, extra
            return [{"name": row[0], "type": row[1]} for row in rel]
        except Exception as e:
            logger.error(f"Error describing table {table_name}: {e}")
            return []

    def load_csv(self, file_path: Path, table_name: str) -> int:
        """Load CSV into DuckDB using native read_csv_auto."""
        safe_path = str(file_path).replace("\\", "/")
        query = f"CREATE OR REPLACE TABLE \"{table_name}\" AS SELECT * FROM read_csv_auto('{safe_path}')"
        self._conn.execute(query)
        count_res = self._conn.execute(f"SELECT COUNT(*) FROM \"{table_name}\"").fetchone()
        row_count = count_res[0] if count_res else 0
        logger.info(f"Loaded CSV into table '{table_name}' with {row_count} rows")
        return row_count

    def load_dataframe(self, df: Any, table_name: str) -> int:
        """Register / create table from a pandas DataFrame."""
        self._conn.register("temp_df_view", df)
        self._conn.execute(f"CREATE OR REPLACE TABLE \"{table_name}\" AS SELECT * FROM temp_df_view")
        self._conn.unregister("temp_df_view")
        count_res = self._conn.execute(f"SELECT COUNT(*) FROM \"{table_name}\"").fetchone()
        row_count = count_res[0] if count_res else 0
        logger.info(f"Loaded DataFrame into table '{table_name}' with {row_count} rows")
        return row_count

    def execute_query(self, sql: str) -> SQLExecutionResult:
        """Execute a validated SQL query, recording execution time and results."""
        start_time = time.perf_counter()
        try:
            cursor = self._conn.execute(sql)
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            duration_ms = (time.perf_counter() - start_time) * 1000.0

            # Convert rows to JSON-serializable list of lists
            serializable_rows = []
            for row in rows:
                row_items = []
                for val in row:
                    # Convert dates, Decimals, etc. to basic types
                    if hasattr(val, "isoformat"):
                        row_items.append(val.isoformat())
                    else:
                        row_items.append(val)
                serializable_rows.append(row_items)

            return SQLExecutionResult(
                success=True,
                sql=sql,
                columns=columns,
                rows=serializable_rows,
                execution_time_ms=round(duration_ms, 2),
                row_count=len(serializable_rows),
                error=None,
            )
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            logger.warning(f"DuckDB SQL execution failed: {e}")
            return SQLExecutionResult(
                success=False,
                sql=sql,
                columns=[],
                rows=[],
                execution_time_ms=round(duration_ms, 2),
                row_count=0,
                error=str(e),
            )

# Global singleton
duckdb_service = DuckDBService()

