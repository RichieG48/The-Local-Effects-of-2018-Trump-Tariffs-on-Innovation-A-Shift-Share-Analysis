"""LaTeX table export."""

from pathlib import Path

import numpy as np
import pandas as pd
from stargazer.stargazer import Stargazer

from .. import config

COVARIATE_LABELS = {
    "const": "Constant",
    "tariff_shock": "U.S. Tariff Shock ($T_0$)",
    "retaliation_shock": "Retaliation Shock ($R_0$)",
    "markups": "Markups",
    "prode_share": "Production Worker Share",
    "cap_vadd_ratio": "Capital / Value Added",
    "log_real_wage": "Log Real Wage",
    "equip_share": "Equipment Share",
}


def write_regression_table(
    models: list,
    path: Path,
    title: str,
    label: str,
    column_labels: list[str] | None = None,
    dependent_variable: str | None = None,
) -> None:
    """Render statsmodels results to a LaTeX table with Stargazer."""
    table = Stargazer(models)
    table.title(title)
    table.table_label = label
    table.rename_covariates(COVARIATE_LABELS)
    if column_labels:
        table.custom_columns(column_labels, [1] * len(column_labels))
        table.show_model_numbers(False)
    if dependent_variable:
        table.dependent_variable_name(dependent_variable)
    Path(path).write_text(table.render_latex())


def summary_stats(df: pd.DataFrame, columns: list[str], weight: str | None = None) -> pd.DataFrame:
    """Mean, SD, min and max of each column (weighted mean/SD if ``weight`` is given)."""
    if weight is not None and weight not in df.columns:
        raise KeyError(f"Weight column {weight!r} not found")
    rows = []
    for col in columns:
        data = df[col].dropna()
        if weight is not None:
            w = df.loc[data.index, weight]
            mean = np.average(data, weights=w)
            sd = np.sqrt(np.average((data - mean) ** 2, weights=w))
        else:
            mean, sd = data.mean(), data.std()
        rows.append({"Variable": col, "Mean": mean, "Std. Dev.": sd, "Min": data.min(), "Max": data.max()})
    return pd.DataFrame(rows)


VARIABLE_LABELS = {
    **{k: v for k, v in COVARIATE_LABELS.items() if k != "const"},
    "mfg_share16": "Manufacturing Share (2016)",
    "gop_prez_share_2016": "GOP Vote Share (2016)",
    "college16": "College Share (2016)",
}


def _stats_rows(stats: pd.DataFrame) -> str:
    lines = []
    for _, r in stats.iterrows():
        name = VARIABLE_LABELS.get(r["Variable"], r["Variable"])
        lines.append(
            f"{name} & {r['Mean']:.4f} & {r['Std. Dev.']:.4f} & {r['Min']:.4f} & {r['Max']:.4f} \\\\"
        )
    return "\n".join(lines)


def write_descriptive_table(
    industry: pd.DataFrame,
    county: pd.DataFrame,
    n_industries: int,
    n_counties: int,
    inv_hhi: float,
    path: Path,
) -> None:
    """Panel A: industry-level shocks and controls. Panel B: county-level characteristics."""
    body = rf"""\begin{{table}}[!htbp] \centering
  \caption{{Descriptive Statistics}}
  \label{{tab:descriptive_stats}}
\begin{{tabular}}{{lcccc}}
\hline \hline
 & Mean & Std. Dev. & Min & Max \\
\hline
\multicolumn{{5}}{{l}}{{\textit{{Panel A: Industry level (N = {n_industries}, effective N = 1/HHI = {inv_hhi:.2f})}}}} \\
{_stats_rows(industry)}
\hline
\multicolumn{{5}}{{l}}{{\textit{{Panel B: County level (N = {n_counties})}}}} \\
{_stats_rows(county)}
\hline \hline
\end{{tabular}}
\end{{table}}
"""
    Path(path).write_text(body)


def write_ci_table(results: dict[str, dict], path: Path) -> None:
    """Point estimates with asymptotic and null-imposed 95% confidence intervals."""
    rows = []
    for name, r in results.items():
        a_lo, a_hi = r["asymptotic_ci"]
        n_lo, n_hi = r["null_imposed_ci"]
        rows.append(
            f"{name} & {r['estimate']:.3f} & ({r['std_error']:.3f}) & "
            f"[{a_lo:.2f}, {a_hi:.2f}] & [{n_lo:.2f}, {n_hi:.2f}] \\\\"
        )
    inv_hhi = next(iter(results.values()))["inverse_hhi"]
    body = rf"""\begin{{table}}[!htbp] \centering
  \caption{{Asymptotic and Null-Imposed Confidence Intervals}}
  \label{{tab:robust_cis}}
\begin{{tabular}}{{lcccc}}
\hline \hline
Shock & Estimate & Std. Error & Asymptotic 95\% CI & Null-imposed 95\% CI \\
\hline
{chr(10).join(rows)}
\hline
\multicolumn{{5}}{{l}}{{\footnotesize Effective number of shocks (1/HHI): {inv_hhi:.2f}. Controls: markups and NBER-CES controls. SEs clustered by NAICS-3.}} \\
\hline \hline
\end{{tabular}}
\end{{table}}
"""
    Path(path).write_text(body)


def ensure_output_dirs() -> None:
    config.TABLES.mkdir(parents=True, exist_ok=True)
    config.FIGURES.mkdir(parents=True, exist_ok=True)
