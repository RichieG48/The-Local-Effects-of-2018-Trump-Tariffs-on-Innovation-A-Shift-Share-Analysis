"""Industry (shock-level) panel: aggregated outcomes, tariff shocks and industry controls."""

import numpy as np
import pandas as pd
import ssaggregate as ssa

from .. import config
from ..naics import normalize_naics, truncate
from .shares import SHARE_PREFIX


def aggregate_to_industries(county_panel: pd.DataFrame) -> pd.DataFrame:
    """Residualise county outcomes on the county controls and aggregate them to
    exposure-weighted industry averages (Borusyak, Hull and Jaravel, 2022)."""
    industry = ssa.ssaggregate(
        data=county_panel,
        vars_list=[config.OUTCOME_POST, config.OUTCOME_PRE],
        n="naics",
        s=SHARE_PREFIX,
        weights="pop16",
        controls=" + ".join(config.COUNTY_CONTROLS),
        addmissing=True,
    )
    industry["naics"] = normalize_naics(industry["naics"])
    return industry


def load_shocks(path=config.TARIFFS_NAICS, naics_level: int = config.NAICS_LEVEL) -> pd.DataFrame:
    """U.S. tariff (T0) and foreign retaliation (R0) shocks from Fajgelbaum et al. (2020)."""
    tariffs = pd.read_stata(path)
    shocks = pd.DataFrame(
        {
            "naics": normalize_naics(tariffs["naics"]),
            "tariff_shock": tariffs["T0"],
            "retaliation_shock": tariffs["R0"],
        }
    )
    shocks = shocks.groupby("naics", as_index=False).mean()
    return shocks[shocks["naics"].str.len() == naics_level].reset_index(drop=True)


def load_nber_controls(path=config.NBER_CES, year: int = 2016) -> pd.DataFrame:
    """Production-structure controls from the NBER-CES Manufacturing Database."""
    nber = pd.read_csv(path)
    for col in ["emp", "pay", "prode", "vadd", "cap", "equip", "piship"]:
        nber[col] = nber[col].astype(float)

    nber["prode_share"] = nber["prode"] / nber["emp"]
    real_vadd = nber["vadd"] / nber["piship"]
    nber["cap_vadd_ratio"] = nber["cap"] / real_vadd
    wage_per_worker = (nber["pay"] * 1e6) / (nber["emp"] * 1e3)
    nber["log_real_wage"] = np.log(wage_per_worker / nber["piship"])
    nber["equip_share"] = nber["equip"] / nber["cap"]
    nber = nber.replace([np.inf, -np.inf], np.nan)

    nber = nber[nber["year"] == year]
    nber["naics"] = normalize_naics(nber["naics"])
    return nber[["naics", *config.NBER_CONTROLS]]


def load_markups(path=config.MARKUPS) -> pd.DataFrame:
    """Pre-2018 markups by 2-digit NAICS sector."""
    return pd.read_stata(path)[["naics2_str", "markups"]]


def load_pac(path=config.PAC) -> pd.DataFrame:
    """2016 PAC contributions summed by 2-digit NAICS sector (negative codes are missing)."""
    pac = pd.read_stata(path)
    pac = pac[~pac["naics"].astype(str).isin(["-100", "-99"])]
    pac = pac.assign(naics2_str=truncate(pac["naics"], 2))
    return pac.groupby("naics2_str", as_index=False)["pac"].sum()


def _finalize(df: pd.DataFrame) -> pd.DataFrame:
    """Drop incomplete industries and add the cluster and winsorised-outcome columns."""
    df = df.dropna().reset_index(drop=True)
    lo, hi = df[config.OUTCOME_POST].quantile(list(config.WINSOR_QUANTILES))
    df["patents_scaled_winsorized"] = df[config.OUTCOME_POST].clip(lower=lo, upper=hi)
    df[config.CLUSTER] = truncate(df["naics"], 3)
    return df


def build_industry_samples(
    industry: pd.DataFrame, shocks: pd.DataFrame, markups: pd.DataFrame, nber: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return the two estimation samples used in the thesis.

    * main (N=333): tradable industries with shocks, markups and all NBER-CES controls.
      Used for every table except the trade pre-trends.
    * pre_nber (N=361): tradable industries with shocks and markups, before the NBER-CES
      merge. Used for the 2013-2017 trade pre-trend table.
    """
    industry = industry.assign(naics2_str=truncate(industry["naics"], 2))
    with_markups = industry.merge(markups, on="naics2_str", how="left")

    pre_nber = _finalize(with_markups.merge(shocks, on="naics", how="left"))

    main = with_markups.merge(nber, on="naics", how="left").dropna(subset=config.NBER_CONTROLS)
    main = _finalize(main.merge(shocks, on="naics", how="left"))
    return main, pre_nber
