# rail-codes

[![PyPI](https://img.shields.io/pypi/v/rail-codes)](https://pypi.org/project/rail-codes/)
[![Python](https://img.shields.io/pypi/pyversions/rail-codes)](https://pypi.org/project/rail-codes/)
[![CI](https://github.com/rosedillon/rail-codes/actions/workflows/ci.yml/badge.svg)](https://github.com/rosedillon/rail-codes/actions/workflows/ci.yml)
[![Licence: GPL-3.0](https://img.shields.io/badge/licence-GPL--3.0-blue)](https://github.com/rosedillon/rail-codes/blob/main/LICENSE)

Convert between the codes Britain's railway uses for the same place.

A station has up to five. The timetable calls Leeds `LEEDS` (its
TIPLOC), passengers and most open data call it `LDS` (its CRS code),
the fares feed calls it `8487` (its NLC), train movement messages call
it `17132` (its STANOX), and European systems use `84870` (its UIC
code). Any project that joins two rail datasets has to translate
between them.

Network Rail's CORPUS extract lists them all, but it has two gaps that
lose real trains. Platform TIPLOCs such as `WATRLMN` (Waterloo main)
and `VICTRIE` (Victoria eastern) have no CRS in it, so every call there
drops out of a join. And some stations have a second CRS for a
separate set of platforms: the timetable books Southeastern high-speed
trains at `SPX`, while passenger counts and station usage
figures only know St Pancras as `STP`. This package ships CORPUS with
both gaps filled.

```python
from rail_codes import crs_for_tiploc, find, station_crs

crs_for_tiploc("WATRLMN")  # 'WAT'
station_crs("SPX")  # 'STP'
find("LDS")[0].stanox  # '17132'
```

## Install

Python 3.11 or later.

```sh
pip install rail-codes
```

It has no dependencies. The data is about 650 kB and loads in a tenth
of a second.

## Command line

Give it any code and it prints the others:

```console
$ rail-codes LDS WATRLMN SPX 2246
TIPLOC   CRS  NLC     STANOX  UIC    NAME
LEEDS    LDS  848700  17132   84870  LEEDS
WATRLMN  WAT  559801  87212   55984  WATERLOO MAIN
STPANCI  SPX  154000  63631   15400  ST PANCRAS
LVRPLSH  LIV  224600  36151   22460  LIVERPOOL LIME STREET
```

A CRS code lists every TIPLOC at the station:

```console
$ rail-codes CLJ
TIPLOC   CRS  NLC     STANOX  UIC    NAME
CLPHMJN  CLJ  559500  87219   55950  CLAPHAM JUNCTION LONDON
CLPHMJ1  CLJ  559518  87219   55954  CLAPHAM JUNCTION PLATS 0-2
CLPHMJC  CLJ  559569  87219   55956  CLAPHAM JUNCTION (C)
CLPHMJW  CLJ  559572  87219   55957  CLAPHAM JN (WINDSOR)
CLPHMJM  CLJ  559591  87219   55958  CLAPHAM JN (MAIN)
```

Only the first of those has a CRS in CORPUS. Add `--json` for
machine-readable output. An unknown code is reported and the exit
status is 1.

## Platform TIPLOCs

Large stations have one TIPLOC per group of platforms, and CORPUS gives
a CRS to only one of them. The timetable books trains at the others,
so code that maps TIPLOCs through CORPUS alone loses Waterloo's main
line, Victoria's eastern side, most of Clapham Junction and both halves
of London Bridge. On a national timetable that is every South Western
Railway train into London.

The 25 TIPLOCs in
[`platform_tiplocs.csv`](https://github.com/rosedillon/rail-codes/blob/main/src/rail_codes/data/platform_tiplocs.csv)
are the ones the May 2026 timetable books at a station that CORPUS
leaves without a CRS. `find` and `crs_for_tiploc` include them.

## Second codes

[`second_codes.csv`](https://github.com/rosedillon/rail-codes/blob/main/src/rail_codes/data/second_codes.csv)
lists 29 codes that belong to another station's platforms:

| Code | Station | Platforms |
|---|---|---|
| `SPX` | `STP` | St Pancras International, high-speed platforms |
| `SPL` | `STP` | St Pancras low level (Thameslink) |
| `PDX` | `PAD` | Paddington, Elizabeth line |
| `LVL` | `LIV` | Liverpool Lime Street low level |
| `GCL` | `GLC` | Glasgow Central low level |
| ... | | |

`station_crs` maps a second code to its station and passes anything
else through, so it is safe to apply to a whole column:

```python
calls["crs"] = calls["crs"].map(station_crs)
```

Whether to merge them depends on the job. Counting trains at St Pancras
wants `SPX` and `STP` together; telling Eurostar's platforms from
Thameslink's wants them apart. `tiploc_to_crs()` gives codes as
published and leaves that choice to you.

`HEZ` (Heworth) and `NCZ` (Newcastle) are not on the list. They are
Tyne and Wear Metro platforms, which most rail datasets leave out.

## NLCs

CORPUS gives 6-digit NLCs. The fares feed uses 4 digits, which are the
first four of the station's `xx xx 00` entry: Liverpool Lime Street is
`224600` in CORPUS and `2246` in the fares feed. `Location.nlc4` gives
that form, and `find` accepts either. The other NLCs under the same
prefix (`155501` to `155598` for St Pancras) are offices, sidings and
accounting codes, and have no 4-digit form.

## Python API

| Name | |
|---|---|
| `find(code)` | every `Location` with that TIPLOC, CRS, NLC or STANOX |
| `crs_for_tiploc(tiploc)` | the CRS, or `None` |
| `tiplocs_for_crs(crs)` | every TIPLOC at a station |
| `tiploc_to_crs()` | the whole TIPLOC to CRS map, as a dict |
| `station_crs(crs)` | a second code's station, or the code itself |
| `second_codes()` | the second-code table, as a dict |
| `locations()` | every CORPUS entry |
| `Location` | `tiploc`, `crs`, `nlc`, `nlc4`, `stanox`, `uic`, `name`, `short_name` |

## Updating the data

CORPUS is republished every few months. Download `CORPUSExtract.json`
from the [Network Rail Open Data feeds](https://publicdatafeeds.networkrail.co.uk)
(a free account) and run:

```sh
python scripts/build_data.py CORPUSExtract.json
```

To refresh the platform TIPLOCs as well, pass a calls table from
[cif-timetable](https://github.com/rosedillon/cif-timetable) as a
second argument. The second-code table is maintained by hand.

## Related packages

Part of a set of Python packages for Great Britain's open rail data:

- [bplan-geography](https://github.com/rosedillon/bplan-geography), minimum running times from Network Rail's BPLAN extract
- [cif-timetable](https://github.com/rosedillon/cif-timetable), calling points and trains per route from the Network Rail CIF timetable
- [hsp-client](https://github.com/rosedillon/hsp-client), how late UK trains actually ran, from the National Rail HSP API
- [rail-loading](https://github.com/rosedillon/rail-loading), UK train operators' passenger loading data in one schema
- [rsp-fares-feed](https://github.com/rosedillon/rsp-fares-feed), every fare between two stations, from the National Rail fares feed
- [tag-databook](https://github.com/rosedillon/tag-databook), DfT TAG Data Book appraisal values without opening Excel
- [track-distance](https://github.com/rosedillon/track-distance), station distances along the rails, from Network Rail's track model
- [orr-station-usage](https://github.com/rosedillon/orr-station-usage), entries and exits at every station by year, from ORR tables 1410 and 1415

## Development

```sh
git clone https://github.com/rosedillon/rail-codes
cd rail-codes
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
ruff check . && ruff format --check . && mypy src
```

## Licence

The code is GPL-3.0. See
[LICENSE](https://github.com/rosedillon/rail-codes/blob/main/LICENSE).

The bundled CORPUS data contains information of Network Rail
Infrastructure Limited licensed under the
[Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).
