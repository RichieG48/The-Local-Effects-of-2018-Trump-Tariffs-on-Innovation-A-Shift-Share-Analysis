"""Helpers for handling NAICS codes consistently across data sources."""

import pandas as pd


def normalize_naics(codes: pd.Series) -> pd.Series:
    """Return NAICS codes as clean strings, e.g. 311111.0 -> "311111"."""
    return codes.astype(str).str.strip().str.replace(r"\.0$", "", regex=True)


def truncate(codes: pd.Series, digits: int) -> pd.Series:
    """Return the first ``digits`` characters of each NAICS code (e.g. the 2-digit sector)."""
    return codes.astype(str).str[:digits]
