"""
Data Loader & Preprocessor for Demand Forecasting & Inventory Optimization
"""

from pathlib import Path
import duckdb
import pandas as pd
from src.utils.logger import logger
from src.utils.helpers import get_project_root, ensure_directory


def load_raw_sales(file_path: str | Path | None = None) -> pd.DataFrame:
    """Load raw transactions CSV and enforce data types."""
    root = get_project_root()
    path = Path(file_path) if file_path else root / "data" / "raw" / "historical_sales.csv"

    if not path.exists():
        raise FileNotFoundError(f"Raw data file not found at {path}")

    logger.info("Loading raw sales data from %s...", path)
    df = pd.read_csv(
        path,
        dtype={
            "store_id": "category",
            "store_name": "string",
            "sku_id": "category",
            "sku_name": "string",
            "category": "category",
            "sub_category": "category",
            "quantity": "int32",
            "unit_price": "float32",
            "unit_cost": "float32",
            "revenue": "float32",
            "gross_margin": "float32",
            "promotion_flag": "int8",
        },
        parse_dates=["date"],
    )
    logger.info("Successfully loaded %d records. Date range: %s to %s", len(df), df["date"].min().date(), df["date"].max().date())
    return df


def ensure_complete_temporal_grid(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure every SKU-Store series has a continuous, unbroken daily calendar sequence.
    Explicitly distinguishes between true zero demand (imputed 0) and missing observations.
    """
    min_date = df["date"].min()
    max_date = df["date"].max()
    full_dates = pd.date_range(min_date, max_date, freq="D")

    # Get unique store-sku metadata
    meta_cols = ["store_id", "store_name", "sku_id", "sku_name", "category", "sub_category", "unit_cost"]
    store_skus = df[meta_cols].drop_duplicates()

    # Create full Cartesian index
    idx = pd.MultiIndex.from_product(
        [full_dates, store_skus["store_id"].unique(), store_skus["sku_id"].unique()],
        names=["date", "store_id", "sku_id"],
    )
    full_grid = pd.DataFrame(index=idx).reset_index()

    # Merge metadata
    full_grid = full_grid.merge(store_skus, on=["store_id", "sku_id"], how="left")

    # Merge actual transaction metrics
    merged = full_grid.merge(
        df[["date", "store_id", "sku_id", "quantity", "unit_price", "revenue", "gross_margin", "promotion_flag"]],
        on=["date", "store_id", "sku_id"],
        how="left",
    )

    # Impute explicit true zeroes for unobserved transaction days
    merged["quantity"] = merged["quantity"].fillna(0).astype("int32")
    merged["promotion_flag"] = merged["promotion_flag"].fillna(0).astype("int8")
    merged["revenue"] = merged["revenue"].fillna(0.0).astype("float32")
    merged["gross_margin"] = merged["gross_margin"].fillna(0.0).astype("float32")

    # Forward fill unit price if missing on zero-sales days
    merged["unit_price"] = merged.groupby(["store_id", "sku_id"])["unit_price"].ffill().bfill().astype("float32")

    merged = merged.sort_values(by=["store_id", "sku_id", "date"]).reset_index(drop=True)
    logger.info("Complete temporal grid constructed: %d rows (zero-demand explicitly represented)", len(merged))
    return merged


def process_and_save_dataset(raw_path: str | None = None) -> tuple[pd.DataFrame, Path, Path]:
    """Load, validate temporal continuity, and export processed Parquet and CSV files."""
    root = get_project_root()
    proc_dir = ensure_directory(root / "data" / "processed")

    raw_df = load_raw_sales(raw_path)
    grid_df = ensure_complete_temporal_grid(raw_df)

    parquet_path = proc_dir / "demand_daily.parquet"
    csv_path = proc_dir / "demand_daily.csv"

    grid_df.to_parquet(parquet_path, index=False, engine="pyarrow")
    grid_df.to_csv(csv_path, index=False)
    logger.info("Exported processed dataset: Parquet -> %s, CSV -> %s", parquet_path, csv_path)

    # Initialize DuckDB analytical table
    duckdb_path = proc_dir / "analytics.duckdb"
    con = duckdb.connect(str(duckdb_path))
    con.execute("CREATE OR REPLACE TABLE demand_daily AS SELECT * FROM grid_df")
    count = con.execute("SELECT count(*) FROM demand_daily").fetchone()[0]
    con.close()
    logger.info("DuckDB table 'demand_daily' initialized with %d rows at %s", count, duckdb_path)

    return grid_df, parquet_path, csv_path


if __name__ == "__main__":
    process_and_save_dataset()
