import numpy as np
import pandas as pd
import pytest

from tariff_innovation.analysis.regressions import wls
from tariff_innovation.analysis.shiftshare import inverse_hhi, null_imposed_ci
from tariff_innovation.analysis.tables import summary_stats


@pytest.fixture
def industries():
    rng = np.random.default_rng(0)
    n = 200
    df = pd.DataFrame(
        {
            "tariff_shock": rng.uniform(0, 0.25, n),
            "markups": rng.normal(1.5, 0.2, n),
            "s_n": rng.uniform(0.5, 1.5, n),
            "naics_3digit": rng.choice([f"3{i:02d}" for i in range(20)], n),
        }
    )
    df["y"] = 10 * df["tariff_shock"] + 2 * df["markups"] + rng.normal(0, 1, n)
    return df


def test_inverse_hhi_equal_weights():
    assert inverse_hhi(pd.DataFrame({"s_n": [1.0] * 50})) == pytest.approx(50)


def test_wls_recovers_coefficient(industries):
    fit = wls(industries, "y", ["tariff_shock", "markups"])
    assert fit.params["tariff_shock"] == pytest.approx(10, abs=2)
    assert fit.cov_type == "cluster"
    assert wls(industries, "y", ["tariff_shock"], se="HC1").cov_type == "HC1"


def test_null_imposed_ci_contains_estimate(industries):
    r = null_imposed_ci(industries, "y", "tariff_shock", ["markups"], grid_points=200)
    lo, hi = r["null_imposed_ci"]
    assert lo < r["estimate"] < hi
    a_lo, a_hi = r["asymptotic_ci"]
    assert lo == pytest.approx(a_lo, rel=0.05) and hi == pytest.approx(a_hi, rel=0.05)


def test_summary_stats_rejects_unknown_weight(industries):
    with pytest.raises(KeyError):
        summary_stats(industries, ["y"], weight="pop_2016")
