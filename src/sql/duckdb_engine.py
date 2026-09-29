"""
DuckDB SQL Analytics Engine for Demand Forecasting & Inventory Optimization
"""

from pathlib import Path
from typing import Any
import duckdb
import pandas as pd
from src.utils.logger import logger
from src.utils.helpers import get_project_root, ensure_directory


class DuckDBAnalyticsEngine:
    """
    Manages DuckDB connection, executes SQL transformations, and materializes
    analytical views and tables.
    """

    def __init__(self, db_path: str | Path | None = None):
        root = get_project_root()
        self.db_path = Path(db_path) if db_path else root / "data" / "processed" / "analytics.duckdb"
        ensure_directory(self.db_path.parent)
        self.con = duckdb.connect(str(self.db_path))
        logger.info("Connected to DuckDB datastore at: %s", self.db_path)

    def execute_script(self, sql_script_path: str | Path) -> None:
        """Read and execute a multi-statement SQL script file."""
        root = get_project_root()
        path = Path(sql_script_path) if Path(sql_script_path).is_absolute() else root / sql_script_path
        if not path.exists():
            raise FileNotFoundError(f"SQL script not found at {path}")

        logger.info("Executing SQL script: %s", path.name)
        with open(path, "r", encoding="utf-8") as f:
            query = f.read()

        # Split statements if needed or execute directly
        self.con.execute(query)

    def query(self, sql_query: str) -> pd.DataFrame:
        """Execute a SQL query and return results as a Pandas DataFrame."""
        return self.con.execute(sql_query).df()

    def load_table_from_df(self, table_name: str, df: pd.DataFrame, overwrite: bool = True) -> None:
        """Register or create a physical table from a Pandas DataFrame."""
        if overwrite:
            self.con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df")
        else:
            self.con.execute(f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM df")
        count = self.con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        logger.info("Table '%s' populated with %d rows in DuckDB.", table_name, count)

    def run_core_analytics_pipeline(self) -> dict[str, Any]:
        """
        Execute core SQL analytics pipeline:
        1. Staging View (01_stg_sales.sql)
        2. Fact Daily Demand (02_daily_demand.sql)
        3. Rolling Demand Metrics (03_rolling_demand_metrics.sql)
        4. ABC-XYZ Segmentation (04_abc_xyz_classification.sql)
        5. SKU Location Profiles (05_sku_demand_profiling.sql)
        """
        logger.info("Starting DuckDB SQL analytical transformations pipeline...")
        root = get_project_root()
        scripts = [
            root / "sql" / "staging" / "01_stg_sales.sql",
            root / "sql" / "analytics" / "02_daily_demand.sql",
            root / "sql" / "analytics" / "03_rolling_demand_metrics.sql",
            root / "sql" / "analytics" / "04_abc_xyz_classification.sql",
            root / "sql" / "analytics" / "05_sku_demand_profiling.sql",
        ]

        for s in scripts:
            self.execute_script(s)

        # Export ABC-XYZ classification table to outputs/inventory/abc_xyz_analysis.csv
        abc_xyz_df = self.query("SELECT * FROM dim_abc_xyz_segmentation")
        out_path = root / "outputs" / "inventory" / "abc_xyz_analysis.csv"
        ensure_directory(out_path.parent)
        abc_xyz_df.to_csv(out_path, index=False)
        logger.info("Exported ABC-XYZ analysis to %s (%d SKUs)", out_path, len(abc_xyz_df))

        # Check counts
        fct_count = self.con.execute("SELECT COUNT(*) FROM fct_daily_demand").fetchone()[0]
        rolling_count = self.con.execute("SELECT COUNT(*) FROM agg_rolling_demand").fetchone()[0]

        return {
            "status": "SUCCESS",
            "daily_demand_rows": fct_count,
            "rolling_demand_rows": rolling_count,
            "segmented_skus": len(abc_xyz_df),
        }

    def close(self) -> None:
        """Close database connection."""
        self.con.close()


def run_sql_analytics() -> dict[str, Any]:
    """Helper runner for standalone SQL execution."""
    engine = DuckDBAnalyticsEngine()
    try:
        res = engine.run_core_analytics_pipeline()
        return res
    finally:
        engine.close()


if __name__ == "__main__":
    run_sql_analytics()
