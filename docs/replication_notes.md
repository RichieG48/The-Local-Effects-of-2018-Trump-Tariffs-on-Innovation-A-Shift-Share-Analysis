# Replication notes

This file records how each result in the dissertation maps to the code, how the
refactored pipeline was checked against the original results, and known caveats.

## Provenance

The original analysis was done interactively in a single notebook, which was not run
top to bottom: some cells depended on variables defined only in commented-out cells, and
the estimation sample was overwritten midway. The refactored pipeline makes both
estimation samples explicit:

| Sample | N | Definition | Used for |
|---|---:|---|---|
| `industry_main.parquet` | 333 | Tradable NAICS-6 industries with shocks, markups and all four NBER-CES controls | Every table except the trade pre-trends |
| `industry_pre_nber.parquet` | 361 | Tradable NAICS-6 industries with shocks and markups (before the NBER-CES merge) | 2013–2017 trade pre-trend table |

The outcome is the residualised, share-aggregated change in patents per 100k residents
(not winsorised). Regressions are WLS with weights `s_n` and NAICS-3 clustered standard
errors (21 clusters), unless noted.

## Thesis → code

| Thesis item | Output | Specification |
|---|---|---|
| Descriptive statistics, 1/HHI = 137.15 | `descriptive_statistics_table.tex` | Panel A: industry variables, main sample, unweighted. Panel B: all counties in `master_county`, unweighted (see caveat 3). |
| Tariff exposure maps | `map_protective.pdf`, `map_retaliatory.pdf` | County `Tw0tr` and `Rw0tr` from Fajgelbaum et al. (2020) |
| Political targeting | `political_targeting.pdf` | LOWESS of `Tw0tr` and `Rw0tr` on 2016 GOP vote share, unweighted (see caveat 4) |
| First stage, λ = −1.007 (p = 0.117) | `first_stage_regression.tex` | Δ log imports 2017→2019 on tariff + markups + NBER-CES controls, main sample (see caveat 2) |
| Main result, β = 3.125 (SE 42.233) | `regression.tex` | Outcome on tariff + markups + NBER-CES controls |
| Retaliation, β = 37.937 (SE 33.638) | `retaliation_shock_regression.tex` | Outcome on retaliation + markups + NBER-CES controls |
| Patenting pre-trend | `pre_trend_regression.tex` | 2014–2017 outcome on tariff + controls, **HC1** standard errors (not clustered) |
| Trade pre-trends | `pre_trend_trade_regression.tex` | Mean monthly Δ log import value / quantity / unit value 2013–2017 on tariff, **N = 361** sample |
| Balance tests | `balance_tests.tex` | Each of markups and the four NBER-CES controls on tariff |
| Null-imposed CIs | `null_imposed_CI.tex` | Tariff and retaliation, grid of ±10 SE with 1000 points (see caveat 1) |

Supplementary (not in the thesis): `supp_trade_pretrends_2017.tex`,
`supp_pac_falsification.tex`, `bhj_binscatter.pdf`, `first_stage_avp.pdf`,
`national_heartbeat.png`, `innovation_distribution.png`.

## Verification against the original results

The refactored pipeline was run from the raw data and compared with the tables produced
by the original notebook (kept locally in `archive/`).

- **Every number is identical** in `regression.tex`, `retaliation_shock_regression.tex`,
  `first_stage_regression.tex`, `pre_trend_regression.tex`,
  `pre_trend_trade_regression.tex` and `balance_tests.tex` (coefficients, standard errors,
  R², F-statistics, N).
- Intermediate checkpoints match the notebook: share matrix 3193 counties × 978
  industries (3192 with ≥90% coverage), 2951 patent county names → 2325 FIPS counties,
  2290 counties in the estimation panel, industry samples N = 364 → 333 and 361,
  1/HHI = 137.15, markup balance coefficient −3.2485 (SE 1.4133).
- Null-imposed CIs: the tariff interval matches the thesis exactly
  ([−79.65, 85.90] asymptotic, [−79.31, 85.56] null-imposed). For retaliation, the asymptotic
  interval matches ([−27.99, 103.87]) but the null-imposed interval is
  [−27.72, 103.60] versus [−27.59, 103.46] in the thesis. The difference comes from
  the grid (caveat 1); the grid used for the thesis number is not recorded.
- Reading `patent_number` as a string (the original run let pandas infer mixed types)
  was checked to change no county's patent counts.

## Caveats and differences between the text and the code

1. **"Null-imposed" confidence intervals.** The implemented procedure regresses
   y − β₀·g on the shock and controls and keeps β₀ if the shock coefficient is not
   rejected. Because the regressors and the clustered variance do not depend on β₀, this
   is exactly the Wald test of β = β₀: the accepted set is the asymptotic CI, truncated to
   the nearest grid points. The gap between the "asymptotic" and "null-imposed" columns is
   therefore grid discretisation, not a finite-sample correction. A true BHJ (2022)
   null-imposed interval would compute the variance from residuals estimated with β = β₀
   imposed. The code keeps the thesis procedure so the table reproduces.
2. **First-stage wording.** The thesis text describes an inverse-hyperbolic-sine outcome
   with share-aggregated county controls. The reported λ = −1.007 comes from the log
   outcome with markups and NBER-CES controls, which is what the code estimates. (The IHS
   variant existed in an exploratory notebook, which is not part of this repository.)
3. **Descriptive statistics, Panel B.** The original code intended population weights but
   passed a column name that does not exist (`pop_2016`; the data has `pop16`), so the
   statistics were unweighted. The pipeline reproduces the unweighted statistics, and
   `summary_stats` now raises an error for unknown weight columns.
4. **Political targeting figure.** The figure note says the fit is weighted by county
   population; the LOWESS fit is unweighted.
5. **Outcome windows.** The text describes a 2014–2017 pre-period and a 2018–2023
   post-period. The code defines the pre-trend as patents(2017) − patents(2014) and the
   post-shock change as mean(patents 2021–2023) − patents(2017), by application year.
6. **Trade pre-trend sample.** The text refers to the 333 tradable industries; the trade
   pre-trend table uses the 361-industry sample (before the NBER-CES merge).
7. **Exposure shares** use the midpoint of the EFSY lower and upper employment bounds
   rather than a point imputation.
8. **Grant-lag truncation of the patent outcome.** The patent files contain *granted*
   patents indexed by application year. National counts rise to ~169k (2019) and then
   fall to ~127k (2021), ~82k (2022) and ~35k (2023) (`outputs/figures/national_heartbeat.png`),
   because many recent applications had not yet been granted when the data was
   extracted. The post-shock outcome (mean 2021–2023 minus 2017) is therefore
   mechanically negative almost everywhere. A uniform truncation is absorbed by the
   constant, but pendency varies across technology fields, so truncation that is
   correlated with a region's industry mix could bias the estimates. Robustness checks
   worth considering: an earlier post window (e.g. 2019), normalising county counts by
   the national count in each year, or using application-level (pre-grant publication)
   data.
