"""Convert between the codes Britain's railway uses for one place.

Every location has up to five: a TIPLOC (timetables), a CRS code
(passengers, and most open data), an NLC (fares and ticketing), a
STANOX (train movements) and a UIC code. Network Rail's CORPUS extract
lists them all, but not completely. Platform TIPLOCs such as WATRLMN
(Waterloo main) have no CRS in it, and some stations have a second CRS
for a separate set of platforms (SPX for the high-speed side of St
Pancras). This package ships CORPUS with both gaps filled::

    from rail_codes import crs_for_tiploc, find, station_crs

    crs_for_tiploc("WATRLMN")  # 'WAT'
    station_crs("SPX")         # 'STP'
    find("LDS")[0].stanox      # '17132'
"""

from __future__ import annotations

import csv
import dataclasses
import functools
import gzip
import io
from importlib import resources

__version__ = "0.1.0"

__all__ = [
    "Location",
    "crs_for_tiploc",
    "find",
    "locations",
    "second_codes",
    "station_crs",
    "tiploc_to_crs",
    "tiplocs_for_crs",
]


@dataclasses.dataclass(frozen=True)
class Location:
    """One CORPUS entry. Codes CORPUS leaves out are empty strings.

    Platform TIPLOCs that CORPUS gives no CRS, but that the timetable
    books at a station (CLPHMJC at Clapham Junction, VICTRIE at
    Victoria), have the station's CRS filled in.
    """

    tiploc: str
    crs: str
    nlc: str
    stanox: str
    uic: str
    name: str
    short_name: str

    @property
    def nlc4(self) -> str:
        """The 4-digit NLC that the fares feed uses, or ``""``.

        The fares feed's ``2246`` is CORPUS's ``224600``. NLCs ending in
        anything but ``00`` are offices, sidings and accounting codes
        under the same prefix, and have no 4-digit form.
        """
        return self.nlc[:4] if self.nlc.endswith("00") else ""


def _data(name: str) -> bytes:
    return resources.files("rail_codes").joinpath("data", name).read_bytes()


def _rows(name: str) -> list[dict[str, str]]:
    raw = _data(name)
    if name.endswith(".gz"):
        raw = gzip.decompress(raw)
    return list(csv.DictReader(io.StringIO(raw.decode("utf-8"))))


@functools.cache
def locations() -> tuple[Location, ...]:
    """Every location in the bundled CORPUS extract."""
    platforms = {row["tiploc"]: row["crs"] for row in _rows("platform_tiplocs.csv")}
    rows = _rows("corpus.csv.gz")
    for row in rows:
        if not row["crs"]:
            row["crs"] = platforms.get(row["tiploc"], "")
    return tuple(Location(**row) for row in rows)


@functools.cache
def tiploc_to_crs() -> dict[str, str]:
    """TIPLOC to CRS for every TIPLOC with one.

    The codes are as published, so a second code such as SPX stays
    SPX. Pass the result through :func:`station_crs` to merge those.
    """
    return {loc.tiploc: loc.crs for loc in locations() if loc.tiploc and loc.crs}


@functools.cache
def second_codes() -> dict[str, str]:
    """Second CRS code to the code of the station it belongs to.

    Some stations have a second code for a separate set of platforms.
    The timetable books trains there under the second code, while
    passenger counts, the ORR's station usage estimates and the ODM use
    the main one. Nothing in the open feeds maps between them.
    """
    return {row["code"]: row["station"] for row in _rows("second_codes.csv")}


def _norm(code: str) -> str:
    return str(code).strip().upper()


def crs_for_tiploc(tiploc: str) -> str | None:
    """The CRS code for a TIPLOC, or ``None`` if it has none."""
    return tiploc_to_crs().get(_norm(tiploc))


def tiplocs_for_crs(crs: str) -> list[str]:
    """Every TIPLOC booked under a CRS code, sorted."""
    crs = _norm(crs)
    return sorted(t for t, c in tiploc_to_crs().items() if c == crs)


def station_crs(crs: str) -> str:
    """The station's main CRS code: ``SPX`` gives ``STP``.

    Any other code comes back trimmed and upper-cased, unchanged.
    """
    crs = _norm(crs)
    return second_codes().get(crs, crs)


@functools.cache
def _index() -> dict[str, list[Location]]:
    index: dict[str, list[Location]] = {}
    for loc in locations():
        for key in {loc.tiploc, loc.crs, loc.nlc, loc.nlc4, loc.stanox}:
            if key:
                index.setdefault(key, []).append(loc)
    return index


def find(code: str) -> list[Location]:
    """Every location whose TIPLOC, CRS, NLC or STANOX is ``code``.

    NLCs match in their 6-digit form or the 4-digit form the fares feed
    uses. A CRS returns every TIPLOC at that station.
    """
    return list(_index().get(_norm(code), []))
