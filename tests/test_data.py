from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "historical_automobile_sales.csv"

def test_dataset_exists_and_has_expected_size():
    df = pd.read_csv(DATA)
    assert len(df) == 528
    assert {"Date", "Year", "Month", "Recession", "Automobile_Sales",
            "Vehicle_Type", "City"}.issubset(df.columns)

def test_recession_is_binary_and_sales_nonnegative():
    df = pd.read_csv(DATA)
    assert set(df["Recession"].dropna().unique()).issubset({0, 1})
    assert (df["Automobile_Sales"].dropna() >= 0).all()

def test_city_field_is_state_level_source_category():
    df = pd.read_csv(DATA)
    assert set(df["City"].dropna().unique()) == {
        "California", "Georgia", "Illinois", "New York"
    }
