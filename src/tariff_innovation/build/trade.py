"""NAICS-level U.S. import flows: pre-trends and the 2017-2019 first-stage outcome."""

import numpy as np
import pandas as pd

from .. import config


def load_trade_flows(path=config.TRADE_FLOWS) -> pd.DataFrame:
    """Monthly HS10 import flows (value and quantity) with their NAICS code.

    The source file is ~2 GB, so only the needed columns are read.
    """
    trade = pd.read_stata(path, columns=["naics_str", "year", "month", "m_val", "m_q1"])
    trade["naics"] = trade["naics_str"].astype(str).str.strip()
    return trade[trade["naics"] != ""].drop(columns="naics_str")


def monthly_log_changes(trade: pd.DataFrame, years=config.TRADE_PRETREND_YEARS) -> pd.DataFrame:
    """Month-over-month log changes in import value, quantity and unit value by NAICS."""
    first, last = years
    trade = trade[trade["year"].between(first, last)]
    monthly = trade.groupby(["naics", "year", "month"], as_index=False)[["m_val", "m_q1"]].sum()
    monthly["m_p"] = np.where(monthly["m_q1"] > 0, monthly["m_val"] / monthly["m_q1"], np.nan)
    monthly = monthly.sort_values(["naics", "year", "month"])

    for src, dst in [("m_val", "delta_val"), ("m_q1", "delta_qty"), ("m_p", "delta_p")]:
        log_level = np.log(monthly[src].replace(0, np.nan))
        monthly[dst] = log_level.groupby(monthly["naics"]).diff()
    return monthly


def average_trends(monthly: pd.DataFrame, suffix: str) -> pd.DataFrame:
    """Average the monthly log changes into one pre-trend per NAICS code."""
    return (
        monthly.groupby("naics", as_index=False)
        .agg(
            **{
                f"delta_import_val_{suffix}": ("delta_val", "mean"),
                f"delta_qty_{suffix}": ("delta_qty", "mean"),
                f"delta_uv_{suffix}": ("delta_p", "mean"),
            }
        )
        .fillna(0)
    )


def import_change(trade: pd.DataFrame, years=config.FIRST_STAGE_YEARS) -> pd.DataFrame:
    """Log change in annual imports between the two years (industries with positive trade in both)."""
    base, post = years
    annual = (
        trade[trade["year"].isin([base, post])]
        .groupby(["naics", "year"], as_index=False)["m_val"]
        .sum()
        .pivot(index="naics", columns="year", values="m_val")
        .dropna()
    )
    annual = annual[(annual[base] > 0) & (annual[post] > 0)]
    change = np.log(annual[post]) - np.log(annual[base])
    return change.rename("delta_ln_imports").reset_index()
