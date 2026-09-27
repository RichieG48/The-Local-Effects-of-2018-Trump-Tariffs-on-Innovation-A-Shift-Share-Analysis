"""Run the full replication pipeline: raw data -> tables and figures.

Usage:
    python run_all.py               # all stages
    python run_all.py --from 3      # skip the (slow) build stages
"""

import argparse
import time

from tariff_innovation.pipeline import STAGES


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--from", dest="start", type=int, default=1, choices=sorted(STAGES))
    parser.add_argument("--to", dest="end", type=int, default=max(STAGES), choices=sorted(STAGES))
    args = parser.parse_args()

    for number in range(args.start, args.end + 1):
        stage = STAGES[number]
        print(f"\n=== {stage.__doc__.splitlines()[0]}")
        start = time.time()
        stage()
        print(f"--- done in {time.time() - start:.0f}s")


if __name__ == "__main__":
    main()
