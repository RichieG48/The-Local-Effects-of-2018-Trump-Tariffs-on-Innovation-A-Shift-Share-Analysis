# The Direct Effect of the 2018 Trade War on Local Innovation

**A Reduced-Form Shift-Share Approach.** MSc Economics dissertation, London School of
Economics (2026). Supervisor: Xavier Jaravel.

📄 [Read the dissertation (PDF)](paper/Thesis.pdf)

## Summary

Did the 2018 U.S. tariffs, and the retaliation they triggered, change how much U.S.
regions innovate? This project regresses county-level changes in patenting (per 100,000
residents) on exposure to the 2018 statutory tariff shocks of
[Fajgelbaum et al. (2020)](https://doi.org/10.1093/qje/qjz036), using the shock-level
shift-share framework of [Borusyak, Hull and Jaravel (2022)](https://doi.org/10.1093/restud/rdab030):

- **Exposure shares:** 2016 county × NAICS-6 employment from County Business Patterns,
  with suppressed cells imputed by Eckert et al. (2020).
- **Shocks:** U.S. protective tariffs (`T0`) and foreign retaliatory tariffs (`R0`) for
  333 tradable NAICS-6 industries.
- **Inference:** the equivalent shock-level WLS regression (via `ssaggregate`), with
  county controls residualised out, industry controls (markups, NBER-CES), NAICS-3
  clustered standard errors and null-imposed confidence intervals.

### Headline results

| | Estimate | Std. error | 95% CI | N |
|---|---:|---:|---|---:|
| U.S. protective tariff shock | 3.13 | 42.23 | [−79.65, 85.90] | 333 |
| Foreign retaliatory tariff shock | 37.94 | 33.64 | [−27.99, 103.87] | 333 |

Shock-level WLS with markups and NBER-CES controls, NAICS-3 clustered standard errors.

Neither shock has a statistically detectable short-run effect on local patenting. The
confidence intervals are wide, so this is a failure to detect an effect rather than
evidence of no effect. Pre-trend tests on patenting and on 2013–2017 trade flows support
the design. The statutory tariffs are a weak predictor of aggregate NAICS-6 imports
(trade diversion), which motivates the reduced-form approach.

## Replicating the results

Requires Python 3.11 and ~8 GB of RAM. The static map export needs Chrome or Chromium,
which kaleido uses.

```bash
git clone https://github.com/RichieG48/The-Local-Effects-of-2018-Trump-Tariffs-on-Innovation-A-Shift-Share-Analysis.git
cd The-Local-Effects-of-2018-Trump-Tariffs-on-Innovation-A-Shift-Share-Analysis
python -m venv .venv && source .venv/bin/activate
make install          # pinned dependencies + this package

make data             # download public inputs; see data/README.md for the manual ones
make all              # raw data -> outputs/tables/*.tex and outputs/figures/*
make test             # quick unit tests (no data needed)
```

`make all` runs `run_all.py`, which executes five stages. Use `python run_all.py --from 3`
to re-run only the analysis once the processed data exists.

| Stage | Script | Output |
|---|---|---|
| 1 | `scripts/01_build_county_panel.py` | `data/processed/county_panel.parquet`: shares, patent outcomes, county controls |
| 2 | `scripts/02_build_industry_panel.py` | `data/processed/industry_*.parquet`: `ssaggregate` output, shocks, industry controls, trade outcomes |
| 3 | `scripts/03_main_results.py` | main and retaliation regressions |
| 4 | `scripts/04_identification.py` | first stage, pre-trends, balance tests, confidence intervals, descriptive statistics |
| 5 | `scripts/05_figures.py` | maps and figures |

Stages 1–2 take roughly 10 minutes, most of it reading the 2 GB trade-flow file. The
analysis stages take seconds.

For a guided tour of the method and results, open
[`notebooks/walkthrough.ipynb`](notebooks/walkthrough.ipynb).

## Where each result comes from

| Thesis | Output | Code |
|---|---|---|
| Descriptive statistics, 1/HHI | `outputs/tables/descriptive_statistics_table.tex` | `pipeline.identification` |
| Tariff exposure maps | `outputs/figures/map_protective.pdf`, `map_retaliatory.pdf` | `figures.tariff_maps` |
| Political targeting | `outputs/figures/political_targeting.pdf` | `figures.political_targeting` |
| First stage | `outputs/tables/first_stage_regression.tex` | `regressions.first_stage` |
| Main result | `outputs/tables/regression.tex` | `regressions.main_regression` |
| Retaliation | `outputs/tables/retaliation_shock_regression.tex` | `regressions.retaliation_regression` |
| Patenting pre-trend | `outputs/tables/pre_trend_regression.tex` | `regressions.innovation_pretrend` |
| Trade pre-trends | `outputs/tables/pre_trend_trade_regression.tex` | `regressions.trade_pretrends` |
| Balance tests | `outputs/tables/balance_tests.tex` | `regressions.balance_tests` |
| Null-imposed CIs | `outputs/tables/null_imposed_CI.tex` | `shiftshare.null_imposed_ci` |

Tables prefixed `supp_` and the binscatter, first-stage added-variable plot and
patenting charts are supplementary; they are not in the thesis.
[`docs/replication_notes.md`](docs/replication_notes.md) documents the exact
specifications, the checks against the thesis numbers and known caveats.

## Known issues

A review during the refactor found several open questions about the analysis. They are
documented in [`docs/replication_notes.md`](docs/replication_notes.md#caveats-and-differences-between-the-text-and-the-code)
and have not been addressed yet, so the code still reproduces the thesis exactly:

- **Null-imposed confidence intervals.** The implemented grid procedure is equivalent to
  the Wald test, so the reported "null-imposed" intervals are the asymptotic intervals
  up to grid discretisation (caveat 1).
- **Grant-lag truncation.** The patent data are granted patents by application year, and
  2021–2023, which make up the post-shock window, are heavily truncated (caveat 8).
- Smaller mismatches between the text and the code: first-stage wording, unweighted
  summary statistics and LOWESS fit, outcome-window description, trade pre-trend sample
  (caveats 2–6).
- The exact sources of `markups.dta`, `contributions.dta` and the patent files still need
  to be confirmed (see [`data/README.md`](data/README.md)).

## Repository layout

```
├── paper/                  dissertation PDF and LaTeX source
├── data/                   README with sources; raw/ and processed/ are not tracked
├── src/tariff_innovation/
│   ├── config.py           paths, years, control lists
│   ├── build/              shares, patents, county panel, industry panel, trade
│   ├── analysis/           regressions, shift-share inference, LaTeX tables
│   ├── figures.py
│   └── pipeline.py         the five stages
├── scripts/                one entry point per stage (+ data download)
├── run_all.py              runs the whole pipeline
├── notebooks/              walkthrough notebook
├── outputs/                tables (.tex) and figures, as reported in the thesis
├── tests/                  unit tests on synthetic data
└── docs/                   replication notes
```

## Citation

See [`CITATION.cff`](CITATION.cff). Code is released under the [MIT licence](LICENSE).
The data belong to their original providers (see [`data/README.md`](data/README.md)).
