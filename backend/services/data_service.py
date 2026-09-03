"""
Data Service — handles CSV ingestion, sample generation, and summarization.
"""

import numpy as np
import pandas as pd
from io import BytesIO
from typing import Optional, cast

# In-memory data store (singleton per server process)
_dataframe_store: Optional[pd.DataFrame] = None


def generate_sample_data() -> pd.DataFrame:
    """Generate realistic mock business/HR analytics sample data."""
    np.random.seed(42)
    n = 500

    departments = ["Engineering", "Sales", "Marketing", "HR", "Finance", "Operations"]
    education = ["High School", "Bachelor", "Master", "PhD"]
    regions = ["North", "South", "East", "West", "Central"]

    df = pd.DataFrame({
        "employee_id": range(1001, 1001 + n),
        "age": np.random.randint(22, 65, n),
        "salary": np.random.randint(35000, 150000, n),
        "experience_years": np.random.randint(0, 35, n),
        "department": np.random.choice(departments, n),
        "education": np.random.choice(education, n),
        "region": np.random.choice(regions, n),
        "performance_score": np.round(np.random.uniform(1.0, 5.0, n), 1),
        "projects_completed": np.random.randint(0, 50, n),
        "hours_per_week": np.random.randint(30, 60, n),
        "satisfaction_score": np.round(np.random.uniform(1.0, 10.0, n), 1),
        "promoted": np.random.choice([0, 1], n, p=[0.7, 0.3]),
        "attrition": np.random.choice([0, 1], n, p=[0.85, 0.15]),
        "target": np.random.choice([0, 1, 2], n, p=[0.5, 0.3, 0.2])
    })

    return df


def load_dataframe() -> Optional[pd.DataFrame]:
    """Get the current in-memory dataframe."""
    return _dataframe_store


def set_dataframe(df: Optional[pd.DataFrame]) -> None:
    """Store a dataframe in memory."""
    global _dataframe_store
    _dataframe_store = df


def load_from_csv_bytes(content: bytes) -> pd.DataFrame:
    """Parse uploaded CSV bytes into a DataFrame."""
    df = pd.read_csv(BytesIO(content))
    set_dataframe(df)
    return df


def load_from_excel_bytes(content: bytes) -> pd.DataFrame:
    """Parse uploaded Excel bytes into a DataFrame."""
    df = pd.read_excel(BytesIO(content))
    set_dataframe(df)
    return df


def get_or_generate() -> pd.DataFrame:
    """Return existing dataframe or generate sample data."""
    global _dataframe_store
    if _dataframe_store is None:
        _dataframe_store = generate_sample_data()
    return _dataframe_store


def summarize(df: pd.DataFrame) -> dict:
    """Generate a statistical summary of the dataframe."""
    numeric_df = df.select_dtypes(include=np.number)
    stats = {}
    for col in numeric_df.columns:
        series = numeric_df[col]
        stats[col] = {
            "mean": round(float(cast(float, series.mean())), 2),
            "median": round(float(cast(float, series.median())), 2),
            "std": round(float(cast(float, series.std())), 2),
            "min": round(float(cast(float, series.min())), 2),
            "max": round(float(cast(float, series.max())), 2),
        }

    return {
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": df.columns.tolist(),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "missing_values": df.isnull().sum().to_dict(),
        "numeric_stats": stats
    }
