"""Download the publicly available inputs and check that the manual ones are in place.

Usage:
    python scripts/00_download_data.py

See data/README.md for a description of every file.
"""

import io
import shutil
import urllib.request
import zipfile

from tariff_innovation import config

DOWNLOADS = {
    config.NBER_CES: "https://data.nber.org/nberces/nberces5818v1/nberces5818v1_n2012.csv",
    config.COUNTY_GEOJSON: config.COUNTY_GEOJSON_URL,
}

EFSY_URL = "https://github.com/fpeckert/website/releases/download/cbp-data/efsy_2016.zip"
EFSY_MEMBER = "2016/Final Imputed/efsy_cbp_2016.csv"

MANUAL = {
    config.MASTER_COUNTY: "Fajgelbaum et al. (2020) replication package",
    config.TARIFFS_NAICS: "Fajgelbaum et al. (2020) replication package",
    config.TRADE_FLOWS: "Fajgelbaum et al. (2020) replication package",
    config.PAC: "Fajgelbaum et al. (2020) replication package",
    config.MARKUPS: "Fajgelbaum et al. (2020) replication package (to confirm)",
    config.PATENTS_DIR: "annual USPTO patent files, one <year>.csv.zip per year 2014-2024",
}


def download(url: str, dest) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"  downloading {url}")
    with urllib.request.urlopen(url) as response, open(dest, "wb") as out:
        shutil.copyfileobj(response, out)


def main() -> None:
    for dest, url in DOWNLOADS.items():
        if dest.exists():
            print(f"[ok]      {dest.relative_to(config.ROOT)}")
        else:
            download(url, dest)

    if config.EFSY_CBP.exists():
        print(f"[ok]      {config.EFSY_CBP.relative_to(config.ROOT)}")
    else:
        print(f"  downloading {EFSY_URL}")
        with urllib.request.urlopen(EFSY_URL) as response:
            archive = zipfile.ZipFile(io.BytesIO(response.read()))
        config.EFSY_CBP.parent.mkdir(parents=True, exist_ok=True)
        config.EFSY_CBP.write_bytes(archive.read(EFSY_MEMBER))

    missing = []
    for path, source in MANUAL.items():
        present = path.exists() and (not path.is_dir() or any(path.glob("*.zip")))
        print(f"[{'ok' if present else 'MISSING'}]{' ' * (7 if present else 2)}"
              f"{path.relative_to(config.ROOT)}  ({source})")
        if not present:
            missing.append(path)

    if missing:
        print("\nSome inputs must be obtained manually; see data/README.md.")
    else:
        print("\nAll inputs present. Run: python run_all.py")


if __name__ == "__main__":
    main()
