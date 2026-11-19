from __future__ import annotations

import json

import pytest

import rail_codes
from rail_codes import cli


def test_corpus_is_loaded() -> None:
    assert len(rail_codes.locations()) > 50_000


def test_tiploc_to_crs() -> None:
    assert rail_codes.crs_for_tiploc("LEEDS") == "LDS"
    assert rail_codes.crs_for_tiploc(" leeds ") == "LDS"
    assert rail_codes.crs_for_tiploc("NOSUCH") is None


@pytest.mark.parametrize(
    ("tiploc", "crs"),
    [("WATRLMN", "WAT"), ("VICTRIE", "VIC"), ("CLPHMJC", "CLJ"), ("LNDNBDE", "LBG")],
)
def test_platform_tiplocs_corpus_misses(tiploc: str, crs: str) -> None:
    assert rail_codes.crs_for_tiploc(tiploc) == crs


def test_tiplocs_for_crs_include_platforms() -> None:
    assert {"CLPHMJN", "CLPHMJC"} <= set(rail_codes.tiplocs_for_crs("CLJ"))


def test_second_codes() -> None:
    assert rail_codes.station_crs("SPX") == "STP"
    assert rail_codes.station_crs("spl") == "STP"
    assert rail_codes.station_crs("LDS") == "LDS"
    # Every second code points at a station that is not itself a
    # second code, so one lookup is always enough.
    codes = rail_codes.second_codes()
    assert not set(codes.values()) & set(codes)


def test_find_by_each_code() -> None:
    loc = next(loc for loc in rail_codes.find("LDS") if loc.tiploc == "LEEDS")
    assert loc.nlc == "848700"
    assert loc.nlc4 == "8487"
    for code in (loc.tiploc, loc.nlc, loc.nlc4, loc.stanox):
        assert loc in rail_codes.find(code)


def test_find_platform_tiploc() -> None:
    assert [loc.crs for loc in rail_codes.find("WATRLMN")] == ["WAT"]
    assert "WATRLMN" in {loc.tiploc for loc in rail_codes.find("WAT")}


def test_find_nothing() -> None:
    assert rail_codes.find("ZZZZZZZ") == []


def test_cli_table(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["LDS"]) == 0
    out = capsys.readouterr().out.splitlines()
    assert out[0].split()[:2] == ["TIPLOC", "CRS"]
    assert ["LEEDS", "LDS", "848700"] in [line.split()[:3] for line in out[1:]]


def test_cli_json(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["SPX", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["SPX"][0]["station_crs"] == "STP"


def test_cli_unknown(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["LDS", "QQQQQQ"]) == 1
    assert "QQQQQQ" in capsys.readouterr().err


def test_nlc4_is_the_station_entry_only() -> None:
    assert [loc.crs for loc in rail_codes.find("1555")] == ["STP"]
