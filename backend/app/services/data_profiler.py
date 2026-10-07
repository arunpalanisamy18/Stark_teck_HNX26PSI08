import datetime
import logging
import re
from typing import Any, Dict, List, Optional
import duckdb

from app.models.schemas import ColumnProfile, DatasetProfile, TableProfile
from app.services.duckdb_service import duckdb_service

logger = logging.getLogger("veritas.profiler")

class DataProfiler:
    def __init__(self, db_service=duckdb_service):
        self.db = db_service

    def profile_table(self, table_name: str) -> TableProfile:
        """Perform comprehensive profiling on a DuckDB table."""
        conn = self.db.get_connection()

        # 1. Row count
        row_res = conn.execute(f"SELECT COUNT(*) FROM \"{table_name}\"").fetchone()
        row_count = int(row_res[0]) if row_res else 0

        # 2. Columns & types
        schema_cols = self.db.get_table_schema(table_name)
        col_count = len(schema_cols)

        # 3. Duplicate rows count
        dup_rows = 0
        if row_count > 0 and col_count > 0:
            try:
                dup_res = conn.execute(
                    f"SELECT (SELECT COUNT(*) FROM \"{table_name}\") - (SELECT COUNT(*) FROM (SELECT DISTINCT * FROM \"{table_name}\"))"
                ).fetchone()
                dup_rows = max(0, int(dup_res[0])) if dup_res else 0
            except Exception as e:
                logger.warning(f"Could not compute duplicate rows for {table_name}: {e}")

        columns_profile: List[ColumnProfile] = []
        primary_keys: List[str] = []
        likely_join_keys: List[str] = []
        warnings: List[str] = []

        has_duplicate_pk = False
        has_mixed_units = False
        has_mixed_currencies = False
        has_ambiguous_dates = False
        distinct_units: List[str] = []
        distinct_currencies: List[str] = []
        ambiguous_date_cols: List[str] = []

        if dup_rows > 0:
            warnings.append(f"Table contains {dup_rows} duplicate rows.")

        for col_info in schema_cols:
            col_name = col_info["name"]
            duck_type = str(col_info["type"]).upper()

            # Null count & distinct count
            try:
                stats_res = conn.execute(
                    f"SELECT COUNT(*) - COUNT(\"{col_name}\"), COUNT(DISTINCT \"{col_name}\") FROM \"{table_name}\""
                ).fetchone()
                null_count = int(stats_res[0]) if stats_res else 0
                unique_count = int(stats_res[1]) if stats_res else 0
            except Exception as e:
                logger.warning(f"Error computing null/distinct for {col_name}: {e}")
                null_count = 0
                unique_count = 0

            null_pct = round((null_count / row_count * 100.0), 2) if row_count > 0 else 0.0

            if null_pct > 20.0:
                warnings.append(f"Column '{col_name}' has high null rate ({null_pct}%).")
            elif null_count > 0 and any(k in col_name.lower() for k in ["amount", "revenue", "price", "cost", "total", "weight", "qty", "quantity"]):
                warnings.append(f"Column '{col_name}' contains {null_count} NULL value(s) ({null_pct}%).")

            # Sample values (up to 5 distinct non-null)
            try:
                sample_rows = conn.execute(
                    f"SELECT DISTINCT \"{col_name}\" FROM \"{table_name}\" WHERE \"{col_name}\" IS NOT NULL LIMIT 5"
                ).fetchall()
                sample_vals = [
                    v[0].isoformat() if hasattr(v[0], "isoformat") else v[0]
                    for v in sample_rows
                ]
            except Exception:
                sample_vals = []

            # Inferred semantic categories
            is_num = any(
                t in duck_type for t in ["INT", "DOUBLE", "FLOAT", "DECIMAL", "NUMERIC", "BIGINT", "HUGEINT"]
            )
            is_date = any(
                t in duck_type for t in ["DATE", "TIMESTAMP", "TIME"]
            ) or ("date" in col_name.lower() or "time" in col_name.lower())

            is_cat = not is_num and not is_date and (unique_count <= 50 or unique_count < (row_count * 0.2))

            # Primary key heuristic: zero nulls and 100% unique
            is_pk = False
            if row_count > 0 and null_count == 0 and unique_count == row_count:
                if "id" in col_name.lower() or "key" in col_name.lower() or "code" in col_name.lower():
                    is_pk = True
                    primary_keys.append(col_name)

            # Primary key candidate check for table entity
            table_clean = table_name.lower().replace("_", "")
            col_clean = col_name.lower().replace("_", "")
            is_entity_id_col = (
                col_clean in ["id", f"{table_clean}id", f"{table_clean.rstrip('s')}id"]
                or (col_clean == "customerid" and "customer" in table_clean)
                or (col_clean == "productid" and "product" in table_clean)
                or (col_clean == "orderid" and ("order" in table_clean or "sale" in table_clean))
            )
            if is_entity_id_col and not is_pk and row_count > 0:
                if unique_count < (row_count - dup_rows):
                    has_duplicate_pk = True
                    warnings.append(
                        f"Duplicate primary key candidate detected in column '{col_name}' with conflicting attribute rows."
                    )

            # Join key heuristic
            if "id" in col_name.lower() or "key" in col_name.lower():
                likely_join_keys.append(col_name)

            # Units detection (e.g. column named unit, units, uom)
            if any(k in col_name.lower() for k in ["unit", "uom", "weight_unit", "currency"]):
                try:
                    unit_vals = [
                        str(v[0]).strip() for v in conn.execute(
                            f"SELECT DISTINCT \"{col_name}\" FROM \"{table_name}\" WHERE \"{col_name}\" IS NOT NULL"
                        ).fetchall()
                    ]
                    if "currency" in col_name.lower() or any(u in ["USD", "INR", "EUR", "GBP", "JPY"] for u in unit_vals):
                        if len(unit_vals) > 1:
                            has_mixed_currencies = True
                            distinct_currencies = unit_vals
                            warnings.append(
                                f"Mixed currencies detected in column '{col_name}': {unit_vals}. Calculation requires exchange rate conversion."
                            )
                    elif len(unit_vals) > 1 and any(u.lower() in ["kg", "g", "lb", "oz", "cm", "m", "l", "ml"] for u in unit_vals):
                        has_mixed_units = True
                        distinct_units = unit_vals
                        warnings.append(
                            f"Mixed units detected in column '{col_name}': {unit_vals}. Direct aggregation without normalization is invalid."
                        )
                except Exception as e:
                    logger.warning(f"Error checking unit/currency column {col_name}: {e}")

            # Ambiguous date detection: DD/MM vs MM/DD
            if is_date or "date" in col_name.lower():
                try:
                    gt12_res = conn.execute(
                        f"SELECT COUNT(*) FROM \"{table_name}\" WHERE EXTRACT(day FROM CAST(\"{col_name}\" AS DATE)) > 12"
                    ).fetchone()
                    gt12_count = int(gt12_res[0]) if gt12_res else 0
                    if gt12_count == 0 and row_count >= 2:
                        has_ambiguous_dates = True
                        ambiguous_date_cols.append(col_name)
                        warnings.append(
                            f"Ambiguous date format detected in column '{col_name}'. All day values are <= 12; cannot disambiguate DD/MM/YYYY vs MM/DD/YYYY without metadata."
                        )
                except Exception as e:
                    logger.warning(f"Error checking ambiguous dates in {col_name}: {e}")

            # Units or currency semantic tagging
            unit_currency = None
            col_lower = col_name.lower()
            if any(term in col_lower for term in ["revenue", "amount", "price", "cost", "salary", "balance"]):
                unit_currency = "currency"
            elif any(term in col_lower for term in ["qty", "quantity", "count", "items"]):
                unit_currency = "count/units"
            elif any(term in col_lower for term in ["weight", "kg", "grams"]):
                unit_currency = "weight"

            columns_profile.append(
                ColumnProfile(
                    name=col_name,
                    type=duck_type,
                    null_count=null_count,
                    null_percentage=null_pct,
                    unique_count=unique_count,
                    sample_values=sample_vals,
                    is_numeric=is_num,
                    is_date=is_date,
                    is_categorical=is_cat,
                    is_primary_key=is_pk,
                    unit_or_currency=unit_currency,
                )
            )

        return TableProfile(
            table=table_name,
            rows=row_count,
            columns=columns_profile,
            duplicate_rows=dup_rows,
            primary_keys=primary_keys,
            likely_join_keys=likely_join_keys,
            warnings=warnings,
            has_duplicate_pk=has_duplicate_pk,
            has_mixed_units=has_mixed_units,
            has_mixed_currencies=has_mixed_currencies,
            has_ambiguous_dates=has_ambiguous_dates,
            distinct_units=distinct_units,
            distinct_currencies=distinct_currencies,
            ambiguous_date_cols=ambiguous_date_cols,
        )

    def profile_dataset(self, dataset_id: str, table_names: List[str]) -> DatasetProfile:
        """Profile all tables in a dataset, including cross-table consistency, orphan keys, and join cardinality."""
        profiles = [self.profile_table(t) for t in table_names]
        total_rows = sum(p.rows for p in profiles)
        conn = self.db.get_connection()

        cross_table_warnings: List[str] = []
        orphan_keys: Dict[str, Any] = {}
        contradictions: List[str] = []
        join_risks: List[str] = []

        # Cross-table inspections
        if len(profiles) > 1:
            for i in range(len(profiles)):
                for j in range(i + 1, len(profiles)):
                    t1 = profiles[i]
                    t2 = profiles[j]
                    cols1 = {c.name.lower(): c.name for c in t1.columns}
                    cols2 = {c.name.lower(): c.name for c in t2.columns}
                    shared_cols = set(cols1.keys()).intersection(set(cols2.keys()))

                    # Find common ID / key column
                    key_cols = [c for c in shared_cols if "id" in c or "key" in c or "code" in c]

                    for kc in key_cols:
                        orig_k1 = cols1[kc]
                        orig_k2 = cols2[kc]

                        # Check for orphan foreign keys
                        try:
                            orphan_res = conn.execute(
                                f"SELECT COUNT(DISTINCT \"{orig_k1}\") FROM \"{t1.table}\" "
                                f"WHERE \"{orig_k1}\" IS NOT NULL AND \"{orig_k1}\" NOT IN "
                                f"(SELECT \"{orig_k2}\" FROM \"{t2.table}\" WHERE \"{orig_k2}\" IS NOT NULL)"
                            ).fetchone()
                            orphan_count = int(orphan_res[0]) if orphan_res else 0
                            if orphan_count > 0:
                                orphan_keys[f"{t1.table}.{orig_k1} -> {t2.table}.{orig_k2}"] = orphan_count
                                cross_table_warnings.append(
                                    f"Orphan foreign keys detected: '{t1.table}.{orig_k1}' has {orphan_count} value(s) not present in '{t2.table}.{orig_k2}'."
                                )
                        except Exception as e:
                            logger.debug(f"Orphan check error {t1.table}->{t2.table}: {e}")

                        # Check for join cardinality explosion (duplicate keys on both sides)
                        try:
                            t1_dups = conn.execute(
                                f"SELECT COUNT(*) - COUNT(DISTINCT \"{orig_k1}\") FROM \"{t1.table}\" WHERE \"{orig_k1}\" IS NOT NULL"
                            ).fetchone()[0]
                            t2_dups = conn.execute(
                                f"SELECT COUNT(*) - COUNT(DISTINCT \"{orig_k2}\") FROM \"{t2.table}\" WHERE \"{orig_k2}\" IS NOT NULL"
                            ).fetchone()[0]
                            if t1_dups > 0 and t2_dups > 0:
                                risk_msg = (
                                    f"Join cardinality risk on '{orig_k1}': both '{t1.table}' and '{t2.table}' have "
                                    f"duplicate join keys, which will cause Cartesian multiplication of rows in joins."
                                )
                                join_risks.append(risk_msg)
                                cross_table_warnings.append(risk_msg)
                        except Exception as e:
                            logger.debug(f"Cardinality check error: {e}")

                        # Check for contradictory data on shared non-key attributes
                        non_key_shared = [c for c in shared_cols if c != kc]
                        for attr in non_key_shared:
                            a1 = cols1[attr]
                            a2 = cols2[attr]
                            try:
                                contra_res = conn.execute(
                                    f"SELECT COUNT(*) FROM \"{t1.table}\" t1 JOIN \"{t2.table}\" t2 "
                                    f"ON t1.\"{orig_k1}\" = t2.\"{orig_k2}\" "
                                    f"WHERE t1.\"{a1}\" IS NOT NULL AND t2.\"{a2}\" IS NOT NULL "
                                    f"AND CAST(t1.\"{a1}\" AS VARCHAR) != CAST(t2.\"{a2}\" AS VARCHAR)"
                                ).fetchone()
                                contra_count = int(contra_res[0]) if contra_res else 0
                                if contra_count > 0:
                                    contra_msg = (
                                        f"Contradictory values detected between '{t1.table}' and '{t2.table}' "
                                        f"for key '{orig_k1}' on attribute '{attr}' ({contra_count} conflicting rows)."
                                    )
                                    contradictions.append(contra_msg)
                                    cross_table_warnings.append(contra_msg)
                            except Exception as e:
                                logger.debug(f"Contradiction check error: {e}")

        return DatasetProfile(
            dataset_id=dataset_id,
            tables=profiles,
            total_rows=total_rows,
            created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            cross_table_warnings=cross_table_warnings,
            orphan_keys=orphan_keys,
            contradictions=contradictions,
            join_risks=join_risks,
        )

# Global singleton
data_profiler = DataProfiler()
