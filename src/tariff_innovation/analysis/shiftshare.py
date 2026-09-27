"""Shift-share diagnostics and inference (Borusyak, Hull and Jaravel, 2022)."""

import numpy as np
import pandas as pd

from .. import config
from .regressions import wls


def inverse_hhi(df: pd.DataFrame, weight: str = config.WEIGHT) -> float:
    """Effective number of shocks: 1 / sum of squared normalised importance weights."""
    shares = df[weight] / df[weight].sum()
    return float(1.0 / (shares**2).sum())


def shock_diagnostics(df: pd.DataFrame, shock: str, weight: str = config.WEIGHT) -> dict:
    """Weighted mean/SD of a shock, the largest weight and the effective number of shocks."""
    w = df[weight]
    mean = np.average(df[shock], weights=w)
    sd = np.sqrt(np.average((df[shock] - mean) ** 2, weights=w))
    return {
        "n_industries": len(df),
        "inverse_hhi": inverse_hhi(df, weight),
        "weighted_mean": mean,
        "weighted_sd": sd,
        "max_weight": float((w / w.sum()).max()),
    }


def null_imposed_ci(
    df: pd.DataFrame,
    y: str,
    shock: str,
    controls: list[str],
    level: float = 0.05,
    grid_width: float = 10.0,
    grid_points: int = 1000,
) -> dict:
    """Asymptotic and grid-inverted 95% confidence intervals for the shock coefficient.

    For each candidate beta_0 on a grid of +/- ``grid_width`` standard errors around the
    point estimate, the outcome is adjusted to y - beta_0 * shock and re-regressed on the
    shock and controls; beta_0 is kept when the shock coefficient is not rejected at ``level``.

    Note: this is the procedure used in the thesis. It re-uses the unrestricted
    clustered variance at each grid point, so it closely tracks the Wald interval; see
    docs/replication_notes.md.
    """
    x = [shock, *controls]
    fit = wls(df, y, x)
    beta, se = fit.params[shock], fit.bse[shock]
    asymptotic = tuple(fit.conf_int(alpha=level).loc[shock])

    accepted = []
    for beta_0 in np.linspace(beta - grid_width * se, beta + grid_width * se, grid_points):
        adjusted = df.assign(_y_adj=df[y] - beta_0 * df[shock])
        if wls(adjusted, "_y_adj", x).pvalues[shock] >= level:
            accepted.append(beta_0)
    null_imposed = (min(accepted), max(accepted)) if accepted else (np.nan, np.nan)

    return {
        "estimate": beta,
        "std_error": se,
        "asymptotic_ci": asymptotic,
        "null_imposed_ci": null_imposed,
        "inverse_hhi": inverse_hhi(df),
    }
