"""County x industry employment shares (the "shares" of the shift-share design)."""

import numpy as np
import pandas as pd

from .. import config

SHARE_PREFIX = "share_naics_"


def load_efsy(path=config.EFSY_CBP) -> pd.DataFrame:
    """2016 County Business Patterns with the Eckert et al. (2020) imputed bounds."""
    return pd.read_csv(path, dtype={"naics": str})


def build_share_matrix(cbp: pd.DataFrame, naics_level: int = config.NAICS_LEVEL) -> pd.DataFrame:
    """Build the wide county x NAICS employment-share matrix.

    Keeps only the finest NAICS level so that industries are mutually exclusive,
    imputes employment as the midpoint of the EFSY lower/upper bounds, and divides
    by county total employment. Rows that sum above one are rescaled to one.

    Returns one row per county (``fips``) and one ``share_naics_<code>`` column per industry.
    """
    if naics_level == 6:
        pattern, padding = r"^\d{6}$", ""
    elif naics_level == 4:
        pattern, padding = r"^\d{4}//$", "//"
    else:
        raise ValueError(f"Unsupported NAICS level: {naics_level}")

    df = cbp[cbp["naics"].astype(str).str.match(pattern)].copy()
    if padding:  # an empty pattern makes pyarrow-backed str.replace loop forever
        df["naics"] = df["naics"].astype(str).str.replace(padding, "", regex=False)
    df["fips"] = df["fipstate"].astype(str).str.zfill(2) + df["fipscty"].astype(str).str.zfill(3)
    df["emp_est"] = (df["lb"] + df["ub"]) / 2.0

    county_totals = df.groupby("fips")["emp_est"].transform("sum")
    df["share"] = np.where(county_totals > 0, df["emp_est"] / county_totals, 0)

    shares = df.pivot_table(index="fips", columns="naics", values="share", aggfunc="sum", fill_value=0)
    shares.columns = [f"{SHARE_PREFIX}{c}" for c in shares.columns]

    row_sums = shares.sum(axis=1)
    shares = shares.div(row_sums.where(row_sums > 1.0, 1.0), axis=0)
    return shares.reset_index()


def share_coverage(shares: pd.DataFrame) -> pd.Series:
    """Sum of industry shares for each county (should be ~1)."""
    cols = [c for c in shares.columns if c.startswith(SHARE_PREFIX)]
    return shares[cols].sum(axis=1)
