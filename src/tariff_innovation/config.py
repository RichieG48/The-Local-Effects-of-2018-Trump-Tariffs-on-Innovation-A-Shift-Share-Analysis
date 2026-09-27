"""Paths and analysis parameters shared by every stage of the pipeline."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

DATA = ROOT / "data"
RAW = DATA / "raw"
EXTERNAL = DATA / "external"
PROCESSED = DATA / "processed"
TABLES = ROOT / "outputs" / "tables"
FIGURES = ROOT / "outputs" / "figures"

# Raw inputs (see data/README.md for where each one comes from)
EFSY_CBP = RAW / "efsy_cbp_2016.csv"
PATENTS_DIR = RAW / "patents"
MASTER_COUNTY = RAW / "master_county.dta"
TARIFFS_NAICS = RAW / "tariffs_naics.dta"
TRADE_FLOWS = RAW / "m_flow_hs10_fm_new.dta"
NBER_CES = RAW / "nberces5818v1_n2012.csv"
MARKUPS = RAW / "markups.dta"
PAC = RAW / "contributions.dta"
COUNTY_GEOJSON = EXTERNAL / "geojson-counties-fips.json"
COUNTY_GEOJSON_URL = (
    "https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json"
)

# Intermediate datasets written by the build stages
COUNTY_PANEL = PROCESSED / "county_panel.parquet"
PATENT_PANEL = PROCESSED / "patent_panel.parquet"
INDUSTRY_MAIN = PROCESSED / "industry_main.parquet"
INDUSTRY_PRE_NBER = PROCESSED / "industry_pre_nber.parquet"
TRADE_TRENDS_13_17 = PROCESSED / "trade_trends_13_17.parquet"
TRADE_TRENDS_17 = PROCESSED / "trade_trends_17.parquet"
IMPORT_CHANGE = PROCESSED / "import_change_17_19.parquet"

# Industry level of the shocks and exposure shares
NAICS_LEVEL = 6

# Patent outcome windows (application years)
FIRST_PATENT_YEAR = 2014
PRE_YEAR = 2014
BASE_YEAR = 2017
POST_YEARS = [2021, 2022, 2023]

# Trade windows
TRADE_PRETREND_YEARS = (2013, 2017)
FIRST_STAGE_YEARS = (2017, 2019)

# County-level (unit-level) controls, residualised out before aggregation
COUNTY_CONTROLS = [
    "mfg_share16",
    "college16",
    "unemployment16",
    "gop_prez_share_2016",
    "gop_prez_share_2016_squared",
]

# Industry-level controls: markups plus the NBER-CES production controls
NBER_CONTROLS = ["prode_share", "cap_vadd_ratio", "log_real_wage", "equip_share"]
INDUSTRY_CONTROLS = ["markups"] + NBER_CONTROLS

OUTCOME_POST = "delta_post_shock_per_100k"
OUTCOME_PRE = "delta_pre_trend_per_100k"
WEIGHT = "s_n"
CLUSTER = "naics_3digit"

WINSOR_QUANTILES = (0.05, 0.95)
