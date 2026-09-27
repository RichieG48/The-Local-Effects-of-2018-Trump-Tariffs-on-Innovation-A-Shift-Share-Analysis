"""County panel: patent outcomes + county controls + exposure shares."""

import pandas as pd

from .. import config

COUNTY_COLUMNS = ["fips", "mfg_share16", "college16", "unemployment16", "gop_prez_share_2016", "pop16"]


def load_master_county(path=config.MASTER_COUNTY) -> pd.DataFrame:
    """County controls and tariff exposures from the Fajgelbaum et al. (2020) replication files."""
    county = pd.read_stata(path)
    county["fips"] = county["fips"].astype(str).str.zfill(5)
    return county.drop_duplicates(subset="fips")


def build_county_panel(
    patents_fips: pd.DataFrame, county: pd.DataFrame, shares: pd.DataFrame
) -> pd.DataFrame:
    """Merge outcomes, controls and shares, and scale patent changes per 100k residents."""
    shares = shares.assign(fips=shares["fips"].astype(str).str.zfill(5)).drop_duplicates("fips")

    panel = patents_fips.merge(county[COUNTY_COLUMNS], on="fips", how="inner", validate="1:1")
    panel = panel.merge(shares, on="fips", how="inner", validate="1:1")

    panel = panel[panel["pop16"].notna() & (panel["pop16"] > 0)].copy()
    panel[config.OUTCOME_PRE] = panel["delta_pre_trend"] / panel["pop16"] * 100_000
    panel[config.OUTCOME_POST] = panel["delta_post_shock"] / panel["pop16"] * 100_000
    panel["gop_prez_share_2016_squared"] = panel["gop_prez_share_2016"] ** 2

    required = [config.OUTCOME_POST, "pop16", *config.COUNTY_CONTROLS]
    return panel.dropna(subset=required).reset_index(drop=True)
