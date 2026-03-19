"""Download a PRISM daily zip and extract the TIF."""

import argparse
import zipfile
from pathlib import Path

import requests

BASE_URL = "https://data.prism.oregonstate.edu/time_series/us/an/800m"


def download(variable: str, date: str, output_dir: str = ".") -> None:
    """Download a PRISM zip for *variable* on *date* (YYYYMMDD) and extract the TIF."""
    filename = f"prism_{variable}_us_30s_{date}"
    zip_name = f"{filename}.zip"
    tif_name = f"{filename}.tif"

    url = f"{BASE_URL}/{variable}/daily/{date[:4]}/{zip_name}"

    out = Path(output_dir) / date
    out.mkdir(parents=True, exist_ok=True)

    zip_path = out / zip_name
    tif_path = out / tif_name

    # Download zip
    print(f"Downloading {url}")
    resp = requests.get(url, stream=True, timeout=120)
    resp.raise_for_status()
    with open(zip_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"Saved {zip_path}")

    # Extract just the TIF
    with zipfile.ZipFile(zip_path) as zf:
        if tif_name not in zf.namelist():
            raise FileNotFoundError(
                f"{tif_name} not found in zip. Contents: {zf.namelist()}"
            )
        zf.extract(tif_name, path=out)
    print(f"Extracted {tif_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download a PRISM daily TIF.")
    parser.add_argument("variable", help="Variable name (e.g. ppt, tmean)")
    parser.add_argument("date", help="Date as YYYYMMDD (e.g. 20251201)")
    parser.add_argument(
        "-o", "--output-dir", default=".", help="Root output directory (default: .)"
    )
    args = parser.parse_args()
    download(args.variable, args.date, args.output_dir)
