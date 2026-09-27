"""Shock-level WLS regressions reported in the thesis.

Every regression is weighted by the industry importance weights ``s_n``. Standard
errors are clustered at the 3-digit NAICS level unless stated otherwise.
"""

import pandas as pd
import statsmodels.api as sm

from .. import config

BALANCE_VARIABLES = {
    "Markups": "markups",
    "Labor": "prode_share",
    "Capital": "cap_vadd_ratio",
    "Wages": "log_real_wage",
    "High-Tech": "equip_share",
}


def wls(df: pd.DataFrame, y: str, x: list[str], se: str = "cluster"):
    """Weighted least squares of ``y`` on ``x`` (plus a constant).

    ``se`` is ``"cluster"`` (NAICS-3 clusters) or ``"HC1"`` (heteroskedasticity-robust).
    """
    model = sm.WLS(df[y], sm.add_constant(df[x]), weights=df[config.WEIGHT])
    if se == "cluster":
        return model.fit(cov_type="cluster", cov_kwds={"groups": df[config.CLUSTER]})
    return model.fit(cov_type=se)


def main_regression(df: pd.DataFrame):
    """Patent change on the U.S. tariff shock with markups and NBER-CES controls."""
    return wls(df, config.OUTCOME_POST, ["tariff_shock", *config.INDUSTRY_CONTROLS])


def retaliation_regression(df: pd.DataFrame):
    """Patent change on the foreign retaliation shock with the same controls."""
    return wls(df, config.OUTCOME_POST, ["retaliation_shock", *config.INDUSTRY_CONTROLS])


def innovation_pretrend(df: pd.DataFrame):
    """Pre-period (2014-2017) patent change on the 2018 tariff shock.

    Uses HC1 standard errors, as in the thesis table.
    """
    return wls(df, config.OUTCOME_PRE, ["tariff_shock", *config.INDUSTRY_CONTROLS], se="HC1")


def robustness_one_control(df: pd.DataFrame) -> dict:
    """Tariff + markups + one NBER-CES control at a time."""
    return {c: wls(df, config.OUTCOME_POST, ["tariff_shock", "markups", c]) for c in config.NBER_CONTROLS}


def balance_tests(df: pd.DataFrame) -> dict:
    """Each baseline industry characteristic regressed on the tariff shock."""
    return {name: wls(df, var, ["tariff_shock"]) for name, var in BALANCE_VARIABLES.items()}


def trade_pretrends(df: pd.DataFrame, trends: pd.DataFrame, suffix: str) -> list:
    """Pre-2018 changes in import value, quantity and unit value on the 2018 tariff shock."""
    data = df.merge(trends, on="naics", how="inner")
    outcomes = [f"delta_import_val_{suffix}", f"delta_qty_{suffix}", f"delta_uv_{suffix}"]
    return [wls(data, y, ["tariff_shock"]) for y in outcomes]


def first_stage_data(df: pd.DataFrame, imports: pd.DataFrame) -> pd.DataFrame:
    return df.merge(imports, on="naics", how="inner")


def first_stage(df: pd.DataFrame, imports: pd.DataFrame):
    """2017-2019 log change in imports on the tariff shock with industry controls."""
    return wls(first_stage_data(df, imports), "delta_ln_imports", ["tariff_shock", *config.INDUSTRY_CONTROLS])


def pac_falsification(df: pd.DataFrame, pac: pd.DataFrame):
    """2016 PAC contributions (2-digit sector totals) on the tariff shock. Supplementary."""
    data = df.merge(pac, on="naics2_str", how="inner")
    return wls(data, "pac", ["tariff_shock"])
