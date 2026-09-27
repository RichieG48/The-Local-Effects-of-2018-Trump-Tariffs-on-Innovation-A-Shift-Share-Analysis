"""County-level patenting outcomes from the annual USPTO/PatentsView files."""

from pathlib import Path

import addfips
import pandas as pd

from .. import config

PATENT_COLUMNS = ["patent_number", "application_year", "country", "state", "county"]


def load_patents(patents_dir: Path = config.PATENTS_DIR) -> pd.DataFrame:
    """Read every ``<year>.csv.zip`` file, keeping only the columns we need."""
    files = sorted(Path(patents_dir).glob("*.zip"))
    if not files:
        raise FileNotFoundError(f"No patent .zip files found in {patents_dir}")
    frames = [
        pd.read_csv(f, usecols=PATENT_COLUMNS, dtype={"patent_number": str, "application_year": "Int64"})
        for f in files
    ]
    return pd.concat(frames, ignore_index=True)


def build_patent_panel(raw: pd.DataFrame) -> pd.DataFrame:
    """Count unique US-inventor patents per county and application year, and compute
    the pre-trend (2017 - 2014) and post-shock (mean 2021-23 - 2017) changes."""
    us = raw[raw["country"] == "US"].dropna(subset=["state", "county", "application_year"])
    counts = (
        us.groupby(["state", "county", "application_year"])["patent_number"]
        .nunique()
        .reset_index()
    )
    counts = counts[counts["application_year"] >= config.FIRST_PATENT_YEAR]

    panel = counts.pivot(
        index=["state", "county"], columns="application_year", values="patent_number"
    ).fillna(0)
    for year in [config.PRE_YEAR, config.BASE_YEAR, *config.POST_YEARS]:
        if year not in panel.columns:
            panel[year] = 0

    panel["delta_pre_trend"] = panel[config.BASE_YEAR] - panel[config.PRE_YEAR]
    panel["delta_post_shock"] = panel[config.POST_YEARS].mean(axis=1) - panel[config.BASE_YEAR]

    panel = panel.reset_index()
    panel.columns = [str(c) for c in panel.columns]
    return panel


def clean_county_names(county: pd.Series) -> pd.Series:
    """Fix the county spellings that addfips does not recognise."""
    return (
        county.str.replace(r"Do̱a", "Dona", regex=True)
        .str.replace(r"\s*\(city\)", " City", case=False, regex=True)
        .str.replace(r"St\.\s*", "St. ", regex=True)
        .str.replace("Carson City City", "Carson City", regex=False)
    )


def map_to_fips(panel: pd.DataFrame) -> pd.DataFrame:
    """Attach 5-digit county FIPS codes and collapse spellings that map to the same county."""
    af = addfips.AddFIPS()
    names = clean_county_names(panel["county"])

    def lookup(county, state):
        try:
            return af.get_county_fips(county, state)
        except Exception:
            return None

    panel = panel.assign(fips=[lookup(c, s) for c, s in zip(names, panel["state"])])
    mapped = panel.dropna(subset=["fips"])

    numeric_cols = mapped.select_dtypes(include="number").columns.tolist()
    return mapped.groupby("fips", as_index=False)[numeric_cols].sum()
