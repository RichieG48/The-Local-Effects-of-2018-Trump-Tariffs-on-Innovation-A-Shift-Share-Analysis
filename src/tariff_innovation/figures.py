"""Figures for the thesis (maps, political targeting) and supplementary figures."""

import json
import urllib.request

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.api as sm
import statsmodels.formula.api as smf

from . import config


def _save(fig, name: str, **kwargs) -> None:
    fig.savefig(config.FIGURES / name, **kwargs)
    plt.close(fig)


def county_geojson() -> dict:
    """U.S. county boundaries, downloaded once to data/external/."""
    if not config.COUNTY_GEOJSON.exists():
        config.COUNTY_GEOJSON.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(config.COUNTY_GEOJSON_URL, config.COUNTY_GEOJSON)
    return json.loads(config.COUNTY_GEOJSON.read_text())


def tariff_maps(county: pd.DataFrame) -> None:
    """County exposure to U.S. protective (Tw0tr) and foreign retaliatory (Rw0tr) tariffs.

    Static export uses kaleido, which needs a local Chrome/Chromium install.
    """
    import plotly.express as px

    geojson = county_geojson()
    for column, scale, label, name in [
        ("Tw0tr", "Reds", "US Tariff Exposure", "map_protective.pdf"),
        ("Rw0tr", "Blues", "Foreign Retaliation", "map_retaliatory.pdf"),
    ]:
        fig = px.choropleth(
            county, geojson=geojson, locations="fips", color=column,
            color_continuous_scale=scale, scope="usa", labels={column: label},
        )
        fig.write_image(config.FIGURES / name)


def political_targeting(county: pd.DataFrame) -> None:
    """LOWESS fit of county tariff exposure against the 2016 GOP vote share."""
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.regplot(x="gop_prez_share_2016", y="Tw0tr", data=county, lowess=True, scatter=False,
                color="darkred", label="U.S. Protective", ax=ax)
    sns.regplot(x="gop_prez_share_2016", y="Rw0tr", data=county, lowess=True, scatter=False,
                color="darkblue", label="Foreign Retaliatory", ax=ax)
    ax.legend()
    _save(fig, "political_targeting.pdf")


def bhj_binscatter(industry: pd.DataFrame) -> None:
    """Supplementary: winsorised patent change against the tariff shock, sized by s_n."""
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(industry["tariff_shock"], industry["patents_scaled_winsorized"],
               s=industry[config.WEIGHT] * 500, alpha=0.4, color="darkblue")

    fit = sm.WLS(industry["patents_scaled_winsorized"], sm.add_constant(industry["tariff_shock"]),
                 weights=industry[config.WEIGHT]).fit()
    x = np.linspace(industry["tariff_shock"].min(), industry["tariff_shock"].max(), 100)
    ax.plot(x, fit.predict(sm.add_constant(x)), color="red", linestyle="--", label="WLS Fit")

    ax.set_xlabel("Industry Tariff Shock ($T_0$)")
    ax.set_ylabel("Patents per 100k (Winsorized)")
    ax.set_title("BHJ Binscatter: Industry Shock vs Innovation")
    sns.despine()
    _save(fig, "bhj_binscatter.pdf")


def first_stage_avp(first_stage: pd.DataFrame) -> None:
    """Supplementary: added-variable plot of import change on the tariff shock, net of markups."""
    res_imports = smf.ols("delta_ln_imports ~ markups", data=first_stage).fit().resid
    res_shock = smf.ols("tariff_shock ~ markups", data=first_stage).fit().resid

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(res_shock, res_imports, s=first_stage[config.WEIGHT] * 10000, alpha=0.3, color="black")
    fit = sm.OLS(res_imports, sm.add_constant(res_shock)).fit()
    x = np.linspace(res_shock.min(), res_shock.max(), 100)
    ax.plot(x, fit.predict(sm.add_constant(x)), color="red", label="First Stage Fit")

    ax.set_xlabel("Statutory Tariff Shock (Residualized on Markups)")
    ax.set_ylabel("Actual Import Volume Change (Residualized on Markups)")
    ax.set_title("First-Stage Added Variable Plot (ADH Style)", fontweight="bold")
    ax.legend(frameon=False)
    sns.despine()
    fig.tight_layout()
    _save(fig, "first_stage_avp.pdf")


def national_patenting(patents: pd.DataFrame) -> None:
    """Descriptive: granted U.S. patents by application year (recent years are truncated by grant lags)."""
    years = [str(y) for y in range(2014, 2024)]
    with sns.axes_style("whitegrid"), sns.plotting_context("talk"):
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.lineplot(x=years, y=patents[years].sum().values, marker="o", color="#2c3e50",
                     linewidth=2.5, ax=ax)
        ax.axvline(x="2018", color="#e74c3c", linestyle="--", linewidth=2, label="2018: Tariff Shock")
        ax.axvline(x="2020", color="#95a5a6", linestyle=":", linewidth=2, label="2020: COVID-19")
        ax.set_title("Granted US Patents by Application Year", pad=20, fontweight="bold")
        ax.set_xlabel("Application Year")
        ax.set_ylabel("Granted Patents")
        ax.legend()
        fig.tight_layout()
        _save(fig, "national_heartbeat.png", dpi=300)


def innovation_distribution(patents: pd.DataFrame) -> None:
    """Descriptive: distribution of county patent changes (5th-95th percentile)."""
    delta = patents["delta_post_shock"]
    trimmed = delta[delta.between(delta.quantile(0.05), delta.quantile(0.95))]
    with sns.axes_style("whitegrid"), sns.plotting_context("talk"):
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.histplot(trimmed, bins=40, kde=True, color="#3498db", edgecolor="black", ax=ax)
        ax.axvline(x=0, color="black", linewidth=1.5)
        ax.set_title("Distribution of Local Innovation Changes (Post-Shock)", pad=20, fontweight="bold")
        ax.set_xlabel("Δ Patents (Post-Shock Avg vs 2017)")
        ax.set_ylabel("Number of Counties")
        fig.tight_layout()
        _save(fig, "innovation_distribution.png", dpi=300)
