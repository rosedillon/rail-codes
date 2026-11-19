"""Command-line interface: look up any code and print all the others."""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from typing import TYPE_CHECKING

from rail_codes import find, station_crs

if TYPE_CHECKING:
    from collections.abc import Sequence

FIELDS = ["tiploc", "crs", "nlc", "stanox", "uic", "name"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rail-codes",
        description=(
            "Look up a GB rail location by TIPLOC, CRS, NLC or STANOX and print all its codes."
        ),
    )
    parser.add_argument("codes", nargs="+", metavar="CODE", help="one or more codes")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    results = {code: find(code) for code in args.codes}

    if args.json:
        payload = {
            code: [
                dataclasses.asdict(loc) | {"station_crs": station_crs(loc.crs)} for loc in found
            ]
            for code, found in results.items()
        }
        json.dump(payload, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        rows = [[f.upper() for f in FIELDS]]
        for found in results.values():
            rows += [[getattr(loc, f) for f in FIELDS] for loc in found]
        widths = [max(len(row[i]) for row in rows) for i in range(len(FIELDS))]
        for row in rows:
            print("  ".join(v.ljust(w) for v, w in zip(row, widths, strict=True)).rstrip())

    missing = [code for code, found in results.items() if not found]
    for code in missing:
        print(f"no location has the code {code.strip().upper()}", file=sys.stderr)
    return 1 if missing else 0
