"""Merge CDC PLACES (2021 release, 2019 data) and the USDA Food Access Research Atlas (2019)
into one tract-level dataset. Both use 2010 census tracts.

Run from the repo root:
    python -m ac209a.build_dataset

Output: data/processed/tract_health_food_access_2019.csv
"""

from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
PLACES_FILE = ROOT / "data/unprocessed/PLACES__Local_Data_for_Better_Health__Census_Tract_Data_2021_release.csv"
FOOD_ACCESS_FILE = ROOT / "data/unprocessed/FoodAccessResearchAtlasData2019.xlsx"
OUTPUT_FILE = ROOT / "data/processed/tract_health_food_access_2019.csv"

# Measures and columns to keep (see config/dataset_columns.yaml)
CONFIG = yaml.safe_load((ROOT / "config/dataset_columns.yaml").read_text())
PLACES = CONFIG["places"]
FOOD = CONFIG["food_access"]


def load_places() -> pd.DataFrame:
    """CDC PLACES: one row per tract and measure (MeasureId), with its year, value and 95% confidence limits."""
    places = pd.read_csv(PLACES_FILE, usecols=PLACES["columns"], dtype={"LocationName": str})
    places = places[places["MeasureId"].isin(PLACES["measures"])]
    return places.rename(columns={"LocationName": "GEOID"})


def load_food_access() -> pd.DataFrame:
    """USDA Food Access Research Atlas 2019: tract info + straight-line access measures."""
    food = pd.read_excel(FOOD_ACCESS_FILE, sheet_name="Food Access Research Atlas",
                         usecols=FOOD["columns"], dtype={"CensusTract": str})
    return food.rename(columns={"CensusTract": "GEOID"})


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Drop empty tracts and rows missing the health value or poverty rate."""
    df = df[df["Pop2010"] > 0]
    return df.dropna(subset=["Data_Value", "PovertyRate"])


def build(places: pd.DataFrame, food: pd.DataFrame) -> pd.DataFrame:
    """Merge PLACES and Food Access on the tract ID, clean, and save (one row per tract and measure)."""
    df = places.merge(food, on="GEOID")
    print("Merged rows:", len(df), "| tracts:", df["GEOID"].nunique())

    # Column order: identifiers first, then PLACES columns, then Food Access columns (as in config/dataset_columns.yaml)
    ids = ["GEOID", "State", "StateAbbr", "County", "Geolocation", "Urban"]
    rest = [c for c in PLACES["columns"] + FOOD["columns"]
            if c not in ids + ["LocationName", "CensusTract"]]
    df = df[ids + rest].sort_values(["GEOID", "MeasureId"])

    df = clean(df)
    print("After cleaning:", len(df), "| tracts:", df["GEOID"].nunique())

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)
    print("Saved", OUTPUT_FILE)
    return df


if __name__ == "__main__":
    build(load_places(), load_food_access())
