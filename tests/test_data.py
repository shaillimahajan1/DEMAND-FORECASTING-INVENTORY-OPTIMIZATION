"""
Unit tests for data validation, temporal integrity, and completeness.
"""

import pandas as pd
import pytest
from src.data.generator import generate_retail_sales_data
from src.data.loader import ensure_complete_temporal_grid
from src.validation.quality import DataQualityValidator


@pytest.fixture(scope="module")
def sample_sales_data():
    """Generate small 30-day synthetic retail dataset for unit testing."""
    return generate_retail_sales_data(start_date="2024-01-01", end_date="2024-01-30", seed=42)


def test_data_completeness(sample_sales_data):
    """Verify that there are zero missing or null values in raw generated sales data."""
    validator = DataQualityValidator(sample_sales_data)
    result = validator.validate_completeness()
    assert result["passed"] is True
    assert len(result["columns_with_nulls"]) == 0
    assert result["status"] == "PASSED"


def test_grain_uniqueness(sample_sales_data):
    """Verify that the grain (date, store_id, sku_id) contains no duplicate records."""
    validator = DataQualityValidator(sample_sales_data)
    result = validator.validate_uniqueness()
    assert result["passed"] is True
    assert result["duplicate_grain_records"] == 0


def test_non_negative_demand(sample_sales_data):
    """Verify that no negative quantities, prices, or costs exist."""
    validator = DataQualityValidator(sample_sales_data)
    result = validator.validate_value_validity()
    assert result["passed"] is True
    assert result["negative_demand_count"] == 0
    assert result["non_positive_cost_count"] == 0


def test_temporal_continuity():
    """Verify that ensure_complete_temporal_grid fills unobserved dates with true zeros."""
    raw_records = [
        {"date": "2024-01-01", "store_id": "FC-1", "store_name": "Store 1", "sku_id": "SKU-1", "sku_name": "Item 1", "category": "Cat A", "sub_category": "Sub A", "quantity": 10, "unit_price": 20.0, "unit_cost": 10.0, "revenue": 200.0, "gross_margin": 100.0, "promotion_flag": 0},
        # Notice: 2024-01-02 is missing
        {"date": "2024-01-03", "store_id": "FC-1", "store_name": "Store 1", "sku_id": "SKU-1", "sku_name": "Item 1", "category": "Cat A", "sub_category": "Sub A", "quantity": 15, "unit_price": 20.0, "unit_cost": 10.0, "revenue": 300.0, "gross_margin": 150.0, "promotion_flag": 0},
    ]
    df_sparse = pd.DataFrame(raw_records)
    df_grid = ensure_complete_temporal_grid(df_sparse)

    assert len(df_grid) == 3  # Jan 1, Jan 2, Jan 3
    # Check that Jan 2 is filled with zero quantity
    jan2 = df_grid[df_grid["date"] == "2024-01-02"]
    assert len(jan2) == 1
    assert int(jan2["quantity"].iloc[0]) == 0
