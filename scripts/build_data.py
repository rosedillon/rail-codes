"""Rebuild the package data from Network Rail's CORPUS extract.

    python scripts/build_data.py CORPUSExtract.json [calls.csv]

CORPUSExtract.json comes from the Network Rail Open Data feeds (a free
account at https://publicdatafeeds.networkrail.co.uk). The optional
second argument is a calls table from cif-timetable; TIPLOCs it books
at a station that CORPUS leaves without a CRS are written to
platform_tiplocs.csv. Without it that file is left as it is.
"""

from __future__ import annotations

import csv
import gzip
import io
import json
import pathlib
import sys

DATA = pathlib.Path(__file__).resolve().parents[1] / "src" / "rail_codes" / "data"
COLUMNS = ["tiploc", "crs", "nlc", "stanox", "uic", "name", "short_name"]


def _clean(value: object) -> str:
    return str(value).strip()


def main() -> None:
    source = pathlib.Path(sys.argv[1])
    rows = json.loads(source.read_text(encoding="utf-8"))["TIPLOCDATA"]
    out = [
        {
            "tiploc": _clean(r["TIPLOC"]),
            "crs": _clean(r["3ALPHA"]),
            "nlc": f"{int(r['NLC']):06d}",
            "stanox": _clean(r["STANOX"]),
            "uic": _clean(r["UIC"]),
            "name": _clean(r["NLCDESC"]),
            "short_name": _clean(r["NLCDESC16"]),
        }
        for r in rows
    ]
    text = io.StringIO()
    writer = csv.DictWriter(text, COLUMNS)
    writer.writeheader()
    writer.writerows(out)
    # mtime=0 keeps the file byte-identical when CORPUS has not changed.
    (DATA / "corpus.csv.gz").write_bytes(gzip.compress(text.getvalue().encode(), mtime=0))
    print(f"{len(out):,} CORPUS locations written")

    if len(sys.argv) > 2:
        known = {r["tiploc"]: r["crs"] for r in out if r["tiploc"]}
        extra: dict[str, str] = {}
        with open(sys.argv[2], newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                tiploc, crs = row["tiploc"].strip(), (row.get("crs") or "").strip()
                if tiploc and crs and not known.get(tiploc):
                    extra[tiploc] = crs
        with (DATA / "platform_tiplocs.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["tiploc", "crs"])
            writer.writerows(sorted(extra.items()))
        print(f"{len(extra):,} platform TIPLOCs written")


if __name__ == "__main__":
    main()
