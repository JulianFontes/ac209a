# Data Processing

`src/ac209a/build_dataset.py` merges two raw tract-level datasets into one analysis table.
Run it from the repo root with `python -m ac209a.build_dataset`, or step by step in `notebooks/01_DataProcessing.ipynb`.

## Inputs (`data/unprocessed/`)

| Dataset | File | Years |
|---|---|---|
| CDC PLACES, 2021 release | `PLACES__Local_Data_for_Better_Health__Census_Tract_Data_2021_release.csv` | 2019 survey data (BRFSS) |
| USDA Food Access Research Atlas | `FoodAccessResearchAtlasData2019.xlsx` | 2019 stores; 2010 Census; ACS 2014–18 |

Both use 2010 census tracts, so they join directly on the 11-digit tract ID (`GEOID`).

## Steps

1. **PLACES** (`load_places`)
   - Keep 2 of the 30 measures: `MHLTH` (frequent mental distress) and `DEPRESSION`.
   - Stay in long format: one row per tract and measure, with `MeasureId`, `Year`, `Data_Value`, `Data_Value_Unit` (`%`), `Low_Confidence_Limit` and `High_Confidence_Limit`.
   - Keep `StateAbbr` and `Geolocation` (the tract centroid). Rename `LocationName` to `GEOID`.
2. **Food Access** (`load_food_access`)
   - Keep 20 of the 147 columns: tract info, poverty and income, and the low-access measures.
   - Original column names are kept, except `CensusTract`, which is renamed to `GEOID`.
3. **Merge** (`build`): an inner join on `GEOID`. Each tract's Food Access values repeat on both of its measure rows.
   Columns are ordered as identifiers, health measure, food access, then tract characteristics; rows are sorted by `GEOID` and `MeasureId`.
4. **Clean** (`clean`): drop rows with zero population (`Pop2010`) or a missing `Data_Value` or `PovertyRate`.

No values are changed, imputed or derived.

## Output layout

One row per **tract × measure** (2 rows per tract):

| GEOID | … | MeasureId | Year | Data_Value | Data_Value_Unit | Low_Confidence_Limit | High_Confidence_Limit | food access … | tract … |
|---|---|---|---|---|---|---|---|---|---|
| 01001020100 | … | DEPRESSION | 2019 | 26.6 | % | 25.2 | 28.2 | … | … |
| 01001020100 | … | MHLTH | 2019 | 17.4 | % | 15.7 | 19.1 | … | … |

To analyze one measure: `df[df["MeasureId"] == "MHLTH"]`.

## Before and after

| Stage | Rows | Columns | Notes |
|---|---|---|---|
| PLACES raw | 2,125,561 | 23 | 72,337 tracts × 30 measures, 50 states + DC |
| PLACES loaded | 140,676 | 9 | 70,338 tracts × 2 measures. 1,999 tracts dropped: **New Jersey has no `MHLTH`/`DEPRESSION`** in this release |
| Food Access raw | 72,531 | 147 | 50 states + DC |
| Food Access loaded | 72,531 | 20 | Columns only; no rows dropped |
| Merged | 140,672 | 28 | 70,336 tracts. 2,195 Food Access tracts had no PLACES match (mostly NJ); 2 PLACES tracts had no Food Access match |
| **Cleaned (output)** | **140,666** | **28** | **70,333 tracts × 2 measures.** 3 tracts dropped for missing `PovertyRate`; 0 for zero population |

Output: `data/processed/tract_health_food_access_2019.csv` (49 states + DC).

## Remaining missing values (kept as-is)

Counts below are per tract; in the output each count appears twice, once per measure row.

| Column | Missing | Why |
|---|---|---|
| `lahunv1share`, `lapop1share` | ~19,000 | Blank in the raw file; appears to mean below USDA's low-access cutoff |
| `LAPOP1_10` | 28,954 | Same |
| `lapop10share`, `lahunv10share` | ~62,500 | Same (most tracts have nobody beyond 10 miles) |
| `lapophalfshare`, `lahunvhalfshare` | ~4,300 | Same |
| `MedianFamilyIncome` | 542 | Not reported by ACS |
| `TractSeniors`, `TractHUNV`, `TractSNAP` | 1 | Not reported |