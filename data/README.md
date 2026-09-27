# Data

The raw data (~2.3 GB) is not stored in this repository. Put the files below in
`data/raw/`, then run

```bash
python scripts/00_download_data.py   # fetches the public files, checks the rest
```

The script downloads everything that has a stable public URL and prints which manual
files are still missing.

## Inputs

| File (in `data/raw/`) | Content | Source | How to get it |
|---|---|---|---|
| `efsy_cbp_2016.csv` | 2016 County Business Patterns with suppressed cells imputed (lower/upper employment bounds) | Eckert, Fort, Schott and Yang (2020), [fpeckert.me/cbp](https://fpeckert.me/cbp/) | Automatic |
| `nberces5818v1_n2012.csv` | NBER-CES Manufacturing Industry Database, 1958–2018, NAICS 2012 | Becker, Gray and Marvakov, [NBER](https://www.nber.org/research/data/nber-ces-manufacturing-industry-database) | Automatic |
| `master_county.dta` | County controls (2016 GOP vote share, college, unemployment, manufacturing share, population) and county tariff exposures `Tw0tr`, `Rw0tr` | Fajgelbaum, Goldberg, Kennedy and Khandelwal (2020), *The Return to Protectionism*, QJE, replication package | Manual |
| `tariffs_naics.dta` | 2018 U.S. tariff (`T0`) and foreign retaliation (`R0`) shocks by NAICS | Fajgelbaum et al. (2020) replication package | Manual |
| `m_flow_hs10_fm_new.dta` | Monthly U.S. HS10 import flows (value, quantity) mapped to NAICS (~2.1 GB) | Fajgelbaum et al. (2020) replication package | Manual |
| `contributions.dta` | 2016 PAC contributions by NAICS (supplementary test only) | Fajgelbaum et al. (2020) replication package ⚠ *to confirm* | Manual |
| `markups.dta` | Markups by 2-digit NAICS sector | Believed to come from the Fajgelbaum et al. (2020) replication package ⚠ *to confirm* | Manual |
| `patents/<year>.csv.zip` | One file per application year 2014–2024; patent-inventor rows with `patent_number`, `application_year`, `country`, `state`, `county` | USPTO patent data by inventor location ⚠ *exact dataset/URL to confirm* | Manual |

`data/raw/cbp16co.zip` (raw Census CBP 2016) is **not needed**. It was only used by an
earlier 4-digit version of the analysis.

## Generated files

- `data/external/geojson-counties-fips.json`: county boundaries for the maps, downloaded
  automatically from the Plotly datasets repository.
- `data/processed/*.parquet`: intermediate datasets written by pipeline stages 1–2. Delete
  them to force a rebuild.

## Licences

Each dataset keeps its original licence and terms of use. Cite the original sources
listed above if you use them.
