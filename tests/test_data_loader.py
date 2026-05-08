"""Tests for ``src.data_loader``."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.data_loader import (
    DatasetSchemaError,
    REQUIRED_COLUMNS,
    detect_speed_column,
    load_signal_samples,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONTEST_CSV = PROJECT_ROOT / "data" / "signal_samples.csv"


def test_loads_contest_csv_shape_and_columns():
    df = load_signal_samples(CONTEST_CSV)
    assert len(df) > 0
    for col in REQUIRED_COLUMNS:
        assert col in df.columns, f"missing required column: {col}"


def test_load_raises_on_missing_file(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        load_signal_samples(tmp_path / "does-not-exist.csv")


def test_load_raises_on_missing_columns(tmp_path: Path):
    bad = tmp_path / "bad.csv"
    bad.write_text("foo,bar\n1,2\n")
    with pytest.raises(DatasetSchemaError):
        load_signal_samples(bad)


def test_load_drops_rows_with_nan_required_fields(tmp_path: Path):
    """Rows missing critical fields like Latitude/RSRP must be dropped."""
    csv = tmp_path / "mixed.csv"
    csv.write_text(
        "Latitude,Longitude,CellID,Band,RSRP_dBm,SINR_dB,TerminalType,Download_Mbps\n"
        "31.2,121.4,1,n78,-95,12,Smartphone,200\n"
        ",121.4,2,n78,-95,12,Smartphone,200\n"
        "31.2,121.4,3,n78,,12,Smartphone,200\n"
        "31.2,121.4,4,n28,-105,5,IoT,150\n"
    )
    df = load_signal_samples(csv)
    assert len(df) == 2
    assert set(df["CellID"].astype(int).tolist()) == {1, 4}


def test_detect_speed_column_prefers_download():
    df = pd.DataFrame(
        {
            "Latitude": [0.0],
            "Longitude": [0.0],
            "CellID": [1],
            "Band": ["n78"],
            "RSRP_dBm": [-90.0],
            "SINR_dB": [10.0],
            "TerminalType": ["Smartphone"],
            "Download_Mbps": [123.0],
        }
    )
    assert detect_speed_column(df) == "Download_Mbps"


def test_detect_speed_column_falls_back_to_sinr_then_rsrp():
    df_sinr = pd.DataFrame({"RSRP_dBm": [-90.0], "SINR_dB": [10.0]})
    assert detect_speed_column(df_sinr) == "SINR_dB"

    df_rsrp = pd.DataFrame({"RSRP_dBm": [-90.0]})
    assert detect_speed_column(df_rsrp) == "RSRP_dBm"


def test_detect_speed_column_matches_chinese_keyword():
    df = pd.DataFrame({"上行速率": [10.0], "下行速率": [200.0], "RSRP_dBm": [-90.0]})
    assert detect_speed_column(df) in {"上行速率", "下行速率"}
