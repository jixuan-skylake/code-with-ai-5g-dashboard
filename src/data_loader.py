"""CSV ingestion for the 5G signal dashboard.

Pure data layer: no Streamlit imports here so the loader can be unit-tested
without booting the web UI.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

REQUIRED_COLUMNS: tuple = (
    "Latitude",
    "Longitude",
    "CellID",
    "Band",
    "RSRP_dBm",
    "SINR_dB",
    "TerminalType",
    "Download_Mbps",
)


class DatasetSchemaError(ValueError):
    """Raised when the loaded CSV is missing one of the required columns."""


def load_signal_samples(csv_path) -> pd.DataFrame:
    """Load and validate the contest signal-samples CSV.

    Parameters
    ----------
    csv_path:
        Path to ``signal_samples.csv``. Resolved relative to the current
        working directory if not absolute.

    Returns
    -------
    pandas.DataFrame
        Cleaned dataframe with rows that have NaN in any required column
        dropped, indexes reset, and dtypes coerced to numeric/object as
        expected by the dashboard.
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"signal samples not found at: {path}")

    df = pd.read_csv(path)
    _ensure_columns(df.columns, REQUIRED_COLUMNS)

    # Drop rows that lack any of the load-bearing columns -- the dashboard
    # cannot render a point without coordinates / RSRP.
    df = df.dropna(subset=list(REQUIRED_COLUMNS)).reset_index(drop=True)

    # Coerce dtypes defensively in case the CSV ever has stringy numbers.
    numeric_cols = ("Latitude", "Longitude", "RSRP_dBm", "SINR_dB", "Download_Mbps")
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["CellID"] = pd.to_numeric(df["CellID"], errors="coerce").astype("Int64")
    df = df.dropna(subset=list(numeric_cols)).reset_index(drop=True)

    return df


def _ensure_columns(actual: Iterable, expected: Iterable) -> None:
    missing = [c for c in expected if c not in set(actual)]
    if missing:
        raise DatasetSchemaError(
            f"signal_samples.csv is missing required columns: {missing}"
        )


def detect_speed_column(df: pd.DataFrame) -> str:
    """Pick the column to drive 3D pillar heights.

    Preference order: an explicit download/throughput/rate column, then
    SINR, then RSRP. Documented here so the heuristic is reviewable.
    """
    preferred_keywords = ("download", "throughput", "rate", "速率", "downlink")
    for col in df.columns:
        lc = col.lower()
        if any(kw in lc for kw in preferred_keywords):
            return col
    if "SINR_dB" in df.columns:
        return "SINR_dB"
    return "RSRP_dBm"
