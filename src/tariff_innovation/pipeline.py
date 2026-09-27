"""The five pipeline stages. Each reads from data/ and writes to data/processed/ or outputs/."""

import pandas as pd

from . import config, figures
from .analysis import regressions as reg
from .analysis import shiftshare, tables
from .build import county, industry, patents, shares, trade


def build_county_panel() -> None:
    """Stage 1: exposure shares + county patent outcomes + county controls."""
    config.PROCESSED.mkdir(parents=True, exist_ok=True)

    share_matrix = shares.build_share_matrix(shares.load_efsy())
    coverage = shares.share_coverage(share_matrix)
    print(f"Share matrix: {share_matrix.shape[0]} counties x {share_matrix.shape[1] - 1} industries; "
          f"{(coverage >= 0.9).sum()} counties with >=90% of employment mapped")

    patent_panel = patents.build_patent_panel(patents.load_patents())
    patent_panel.to_parquet(config.PATENT_PANEL, index=False)
    patents_fips = patents.map_to_fips(patent_panel)
    print(f"Patent panel: {len(patent_panel)} county names -> {len(patents_fips)} FIPS counties")

    panel = county.build_county_panel(patents_fips, county.load_master_county(), share_matrix)
    panel.to_parquet(config.COUNTY_PANEL, index=False)
    print(f"County panel: {len(panel)} counties -> {config.COUNTY_PANEL.relative_to(config.ROOT)}")


def build_industry_panel() -> None:
    """Stage 2: aggregate to industries, merge shocks and controls, build trade outcomes."""
    aggregated = industry.aggregate_to_industries(pd.read_parquet(config.COUNTY_PANEL))
    main, pre_nber = industry.build_industry_samples(
        aggregated, industry.load_shocks(), industry.load_markups(), industry.load_nber_controls()
    )
    main.to_parquet(config.INDUSTRY_MAIN, index=False)
    pre_nber.to_parquet(config.INDUSTRY_PRE_NBER, index=False)
    print(f"Industry samples: main N={len(main)}, pre-NBER N={len(pre_nber)}")

    print("Loading trade flows (large file, this takes a few minutes)...")
    flows = trade.load_trade_flows()
    monthly = trade.monthly_log_changes(flows)
    trade.average_trends(monthly, "13_17").to_parquet(config.TRADE_TRENDS_13_17, index=False)
    trade.average_trends(monthly[monthly["year"] == 2017], "17").to_parquet(config.TRADE_TRENDS_17, index=False)
    trade.import_change(flows).to_parquet(config.IMPORT_CHANGE, index=False)


def main_results() -> None:
    """Stage 3: main and retaliation regressions."""
    tables.ensure_output_dirs()
    df = pd.read_parquet(config.INDUSTRY_MAIN)

    for control, fit in reg.robustness_one_control(df).items():
        print(f"  tariff + markups + {control:<15} beta={fit.params['tariff_shock']:8.3f}  "
              f"p={fit.pvalues['tariff_shock']:.3f}")

    main = reg.main_regression(df)
    retaliation = reg.retaliation_regression(df)
    print(f"Main: beta={main.params['tariff_shock']:.3f} (SE {main.bse['tariff_shock']:.3f}), N={int(main.nobs)}")
    print(f"Retaliation: beta={retaliation.params['retaliation_shock']:.3f} "
          f"(SE {retaliation.bse['retaliation_shock']:.3f})")

    tables.write_regression_table(
        [main], config.TABLES / "regression.tex",
        "U.S. Protective Tariffs and Local Innovation", "tab:main_regression",
        dependent_variable="Change in patents per 100k",
    )
    tables.write_regression_table(
        [retaliation], config.TABLES / "retaliation_shock_regression.tex",
        "Foreign Retaliatory Tariffs and Local Innovation", "tab:retaliation_regression",
        dependent_variable="Change in patents per 100k",
    )


def identification() -> None:
    """Stage 4: first stage, pre-trends, balance tests, inference and descriptive statistics."""
    tables.ensure_output_dirs()
    df = pd.read_parquet(config.INDUSTRY_MAIN)
    pre_nber = pd.read_parquet(config.INDUSTRY_PRE_NBER)
    imports = pd.read_parquet(config.IMPORT_CHANGE)

    fs = reg.first_stage(df, imports)
    print(f"First stage: lambda={fs.params['tariff_shock']:.3f} (p={fs.pvalues['tariff_shock']:.3f})")
    tables.write_regression_table(
        [fs], config.TABLES / "first_stage_regression.tex",
        "First Stage: 2018 Tariffs and 2017--2019 Import Changes", "tab:first_stage",
        dependent_variable="$\\Delta \\ln$ imports, 2017--2019",
    )

    pretrend = reg.innovation_pretrend(df)
    print(f"Innovation pre-trend: beta={pretrend.params['tariff_shock']:.3f}")
    tables.write_regression_table(
        [pretrend], config.TABLES / "pre_trend_regression.tex",
        "Pre-Trend Falsification: 2014--2017 Patenting", "tab:innovation_pretrend",
        dependent_variable="Change in patents per 100k, 2014--2017",
    )

    trade_models = reg.trade_pretrends(pre_nber, pd.read_parquet(config.TRADE_TRENDS_13_17), "13_17")
    print("Trade pre-trends 2013-17: " + ", ".join(f"{m.params['tariff_shock']:.3f}" for m in trade_models)
          + f" (N={int(trade_models[0].nobs)})")
    tables.write_regression_table(
        trade_models, config.TABLES / "pre_trend_trade_regression.tex",
        "Pre-Trend Falsification: 2013--2017 Import Trends", "tab:trade_pretrends",
        column_labels=["Import value", "Import quantity", "Unit value"],
    )

    balance = reg.balance_tests(df)
    print(f"Balance (markups): {balance['Markups'].params['tariff_shock']:.4f} "
          f"(SE {balance['Markups'].bse['tariff_shock']:.4f})")
    tables.write_regression_table(
        list(balance.values()), config.TABLES / "balance_tests.tex",
        "BHJ (2022) Balance Tests: Industry Characteristics on Tariff Shocks", "tab:balance_tests_stacked",
        column_labels=list(balance),
    )

    cis = {
        "U.S. tariff": shiftshare.null_imposed_ci(df, config.OUTCOME_POST, "tariff_shock", config.INDUSTRY_CONTROLS),
        "Retaliation": shiftshare.null_imposed_ci(df, config.OUTCOME_POST, "retaliation_shock", config.INDUSTRY_CONTROLS),
    }
    for name, r in cis.items():
        print(f"{name}: asymptotic CI [{r['asymptotic_ci'][0]:.2f}, {r['asymptotic_ci'][1]:.2f}], "
              f"null-imposed [{r['null_imposed_ci'][0]:.2f}, {r['null_imposed_ci'][1]:.2f}]")
    tables.write_ci_table(cis, config.TABLES / "null_imposed_CI.tex")

    # Panel B is unweighted: the thesis run passed a weight column ('pop_2016') that does
    # not exist in master_county, so the weights were silently ignored.
    diag = shiftshare.shock_diagnostics(df, "tariff_shock")
    print(f"Effective number of shocks (1/HHI): {diag['inverse_hhi']:.2f}")
    panel_a = tables.summary_stats(df, ["tariff_shock", "retaliation_shock", *config.INDUSTRY_CONTROLS])
    counties = county.load_master_county()
    panel_b = tables.summary_stats(counties, ["mfg_share16", "gop_prez_share_2016", "college16"])
    tables.write_descriptive_table(panel_a, panel_b, len(df), len(counties), diag["inverse_hhi"],
                                   config.TABLES / "descriptive_statistics_table.tex")

    # Supplementary (not reported in the thesis)
    short_run = reg.trade_pretrends(pre_nber, pd.read_parquet(config.TRADE_TRENDS_17), "17")
    tables.write_regression_table(
        short_run, config.TABLES / "supp_trade_pretrends_2017.tex",
        "Supplementary: 2017 Import Trends", "tab:supp_trade_pretrends_2017",
        column_labels=["Import value", "Import quantity", "Unit value"],
    )
    pac = reg.pac_falsification(df, industry.load_pac())
    tables.write_regression_table(
        [pac], config.TABLES / "supp_pac_falsification.tex",
        "Supplementary: 2016 PAC Contributions", "tab:supp_pac",
        dependent_variable="PAC contributions (2-digit sector)",
    )


def make_figures() -> None:
    """Stage 5: all figures."""
    tables.ensure_output_dirs()
    df = pd.read_parquet(config.INDUSTRY_MAIN)
    counties = county.load_master_county()
    patent_panel = pd.read_parquet(config.PATENT_PANEL)

    figures.tariff_maps(counties)
    figures.political_targeting(counties)
    figures.bhj_binscatter(df)
    figures.first_stage_avp(reg.first_stage_data(df, pd.read_parquet(config.IMPORT_CHANGE)))
    figures.national_patenting(patent_panel)
    figures.innovation_distribution(patent_panel)
    print(f"Figures written to {config.FIGURES.relative_to(config.ROOT)}")


STAGES = {
    1: build_county_panel,
    2: build_industry_panel,
    3: main_results,
    4: identification,
    5: make_figures,
}
