"""Download PRISM daily TIFs for a range of dates and multiple variables."""

import argparse
import subprocess
import sys
from datetime import datetime, timedelta


def date_range(start: str, end: str):
    """Yield YYYYMMDD strings from start to end (inclusive)."""
    s = datetime.strptime(start, "%Y%m%d")
    e = datetime.strptime(end, "%Y%m%d")
    while s <= e:
        yield s.strftime("%Y%m%d")
        s += timedelta(days=1)


def main():
    parser = argparse.ArgumentParser(
        description="Download PRISM daily TIFs for a date range."
    )
    parser.add_argument(
        "--vars",
        required=True,
        help="Comma-separated variable names (e.g. ppt,tmean)",
    )
    parser.add_argument("--start", required=True, help="Start date YYYYMMDD")
    parser.add_argument("--end", required=True, help="End date YYYYMMDD")
    parser.add_argument(
        "-o", "--output-dir", default=".", help="Root output directory (default: .)"
    )
    args = parser.parse_args()

    variables = [v.strip() for v in args.vars.split(",")]

    for date in date_range(args.start, args.end):
        for var in variables:
            print(f"\n--- {var} {date} ---")
            result = subprocess.run(
                [sys.executable, "download.py", var, date, "-o", args.output_dir],
                check=False,
            )
            if result.returncode != 0:
                print(f"WARNING: failed to download {var} for {date}")


if __name__ == "__main__":
    main()
