from pathlib import Path
import pytest
import pandas as pd

from app.config import DEMO_DIR
from app.services.data_profiler import data_profiler
from app.services.duckdb_service import duckdb_service

def test_csv_loading_and_profiling():
    sales_csv = DEMO_DIR / "sales.csv"
    assert sales_csv.exists()

    row_count = duckdb_service.load_csv(sales_csv, "test_sales")
    assert row_count > 0

    profile = data_profiler.profile_table("test_sales")
    assert profile.table == "test_sales"
    assert profile.rows == row_count
    assert len(profile.columns) == 8

    col_names = [c.name for c in profile.columns]
    assert "order_id" in col_names
    assert "amount" in col_names
    assert "date" in col_names

    amount_col = next(c for c in profile.columns if c.name == "amount")
    assert amount_col.is_numeric is True
    assert amount_col.null_count == 0

def test_xlsx_loading_and_profiling():
    fixture_path = Path("tests/fixtures/test_data.xlsx")
    assert fixture_path.exists()

    df = pd.read_excel(fixture_path)
    row_count = duckdb_service.load_dataframe(df, "test_excel_table")
    assert row_count == 3

    profile = data_profiler.profile_table("test_excel_table")
    assert profile.table == "test_excel_table"
    assert profile.rows == 3
    assert len(profile.columns) == 3

