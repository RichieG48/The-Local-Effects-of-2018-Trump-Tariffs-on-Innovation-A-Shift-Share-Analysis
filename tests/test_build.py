import pandas as pd
import pytest

from tariff_innovation.build.patents import build_patent_panel, clean_county_names
from tariff_innovation.build.shares import build_share_matrix, share_coverage
from tariff_innovation.build.trade import import_change
from tariff_innovation.naics import normalize_naics


def test_normalize_naics_strips_float_suffix():
    codes = pd.Series([311111.0, "336111", " 3121 "])
    assert normalize_naics(codes).tolist() == ["311111", "336111", "3121"]


def test_share_matrix_keeps_six_digit_rows_and_sums_to_one():
    cbp = pd.DataFrame(
        {
            "fipstate": [1, 1, 1, 1, 2],
            "fipscty": [1, 1, 1, 1, 3],
            "naics": ["------", "311111", "336111", "3111//", "311111"],
            "lb": [100, 30, 60, 30, 10],
            "ub": [100, 30, 80, 30, 10],
        }
    )
    shares = build_share_matrix(cbp)
    assert shares["fips"].tolist() == ["01001", "02003"]
    assert set(shares.columns) == {"fips", "share_naics_311111", "share_naics_336111"}
    assert share_coverage(shares).tolist() == pytest.approx([1.0, 1.0])
    assert shares.loc[0, "share_naics_311111"] == pytest.approx(30 / 100)


def test_clean_county_names():
    names = pd.Series(["Baltimore (city)", "St.Louis", "Carson City (city)"])
    assert clean_county_names(names).tolist() == ["Baltimore City", "St. Louis", "Carson City"]


def test_patent_panel_deltas():
    rows = []
    counts = {2014: 2, 2017: 5, 2021: 6, 2022: 8, 2023: 10}
    for year, n in counts.items():
        rows += [
            {"patent_number": f"{year}-{i}", "application_year": year, "country": "US",
             "state": "CA", "county": "Santa Clara"}
            for i in range(n)
        ]
    rows.append({"patent_number": "x", "application_year": 2017, "country": "DE",
                 "state": "CA", "county": "Santa Clara"})
    raw = pd.DataFrame(rows).astype({"application_year": "Int64"})

    panel = build_patent_panel(raw)
    row = panel.iloc[0]
    assert row["delta_pre_trend"] == 5 - 2
    assert row["delta_post_shock"] == pytest.approx((6 + 8 + 10) / 3 - 5)


def test_import_change_drops_zero_trade():
    trade = pd.DataFrame(
        {
            "naics": ["A", "A", "B", "B"],
            "year": [2017, 2019, 2017, 2019],
            "m_val": [100.0, 200.0, 0.0, 50.0],
        }
    )
    out = import_change(trade)
    assert out["naics"].tolist() == ["A"]
    assert out["delta_ln_imports"].iloc[0] == pytest.approx(0.6931, abs=1e-4)
