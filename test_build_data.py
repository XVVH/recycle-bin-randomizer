#!/usr/bin/env python3
"""Unit tests for build_data.py (doc → JSON parser).

Covers the previously-untested parsing helpers and the template detector,
plus an end-to-end pass over parse_doc using a small synthetic document.
"""
from __future__ import annotations

import json

import pytest

import build_data as bd


# --- is_entry ---------------------------------------------------------------

@pytest.mark.parametrize(
    "line, expected",
    [
        ("IMG XXXX (0-9999)", True),
        ("@credit-only", True),
        ("VDDMMYY", True),
        ("", False),
        ("a", False),  # too short
        ("Map Legend: colors", False),
        ("Sort by upload date", False),
        ("New Leads incoming", False),
        ("YouTube tips", False),
        ("!image note", False),
        ("[example block]", False),
        ("________", False),
        ("----", False),  # all non-word chars
        ("   ", False),  # whitespace collapses to empty after strip? still len>=2
    ],
)
def test_is_entry(line, expected):
    assert bd.is_entry(line) is expected


def test_is_entry_all_skip_prefixes():
    for prefix in bd.SKIP_PREFIXES:
        assert bd.is_entry(prefix + " trailing text") is False


# --- extract_credit ---------------------------------------------------------

def test_extract_credit_found():
    assert bd.extract_credit("IMG XXXX @kvn.aust-1 [ex]") == "@kvn.aust-1"


def test_extract_credit_first_only():
    assert bd.extract_credit("a @first then @second") == "@first"


def test_extract_credit_missing():
    assert bd.extract_credit("no credit here") == ""


# --- extract_example --------------------------------------------------------

def test_extract_example_found():
    assert bd.extract_example("Foo [DSC 0123]  bar") == "DSC 0123"


def test_extract_example_missing():
    assert bd.extract_example("no example") == ""


def test_extract_example_strips_whitespace():
    assert bd.extract_example("x [  padded  ]") == "padded"


# --- extract_sources --------------------------------------------------------

def test_extract_sources_keeps_named_categories():
    assert bd.extract_sources("Foo (Samsung) (Canon)") == ["Samsung", "Canon"]


def test_extract_sources_filters_numeric_and_special():
    got = bd.extract_sources(
        "Foo (Samsung) (0-9999) (>2013) (Variable stuff) (Example here) (A-F / 0-9)"
    )
    assert got == ["Samsung"]


def test_extract_sources_none():
    assert bd.extract_sources("Foo bar baz") == []


# --- year_floor -------------------------------------------------------------

def test_year_floor_found():
    assert bd.year_floor("something (>2013) more") == 2013


def test_year_floor_missing():
    assert bd.year_floor("no floor") is None


# --- strip_meta -------------------------------------------------------------

def test_strip_meta_removes_credit_and_example():
    assert bd.strip_meta("IMG XXXX @kvn [DSC 0001]  extra") == "IMG XXXX extra"


def test_strip_meta_collapses_whitespace():
    assert bd.strip_meta("a    b\tc") == "a b c"


# --- parse_range ------------------------------------------------------------

def test_parse_range_single_int():
    assert bd.parse_range("IMG XXXX (0-9999)") == [
        {"type": "int", "min": 0, "max": 9999, "width": 4, "raw": "(0-9999)"}
    ]


def test_parse_range_dual_int():
    got = bd.parse_range("Photo (0-99 1-31)")
    assert got == [
        {
            "type": "dual_int",
            "min1": 0,
            "max1": 99,
            "width1": 2,
            "min2": 1,
            "max2": 31,
            "width2": 2,
            "raw": "(0-99 1-31)",
        }
    ]


def test_parse_range_multiple_int_ranges():
    got = bd.parse_range("X (1-9) Y (10-20)")
    assert [r["raw"] for r in got] == ["(1-9)", "(10-20)"]
    assert all(r["type"] == "int" for r in got)


def test_parse_range_hex2():
    assert bd.parse_range("Cam XX (A-F / 0-9)") == [
        {"type": "hex2", "raw": "(A-F / 0-9)", "width": 2}
    ]


def test_parse_range_width_uses_longest_bound():
    (r,) = bd.parse_range("(5-1200)")
    assert r["width"] == 4


def test_parse_range_none():
    assert bd.parse_range("no range at all") == []


# --- detect_template --------------------------------------------------------

def _detect(core, extra_ranges=None, example="", yf=None):
    ranges = extra_ranges if extra_ranges is not None else bd.parse_range(core)
    return bd.detect_template(core, ranges, example, yf)


def test_detect_template_int():
    t = _detect("IMG XXXX (0-9999)")
    assert t["kind"] == "int"
    assert t["prefix"] == "IMG {n}"
    assert t["range"] == {"min": 0, "max": 9999, "width": 4}


def test_detect_template_int_clamped_to_x_width():
    # Range wider than the X placeholders is clamped to the placeholder width.
    t = _detect("A XX (0-9999)")
    assert t["kind"] == "int"
    assert t["range"]["width"] == 2
    assert t["range"]["max"] == 99


def test_detect_template_single_x_pads_to_max_width():
    t = _detect("My Movie X (1-20)")
    assert t["kind"] == "int"
    assert t["prefix"] == "My Movie {n}"
    assert t["range"] == {"min": 1, "max": 20, "width": 2}


def test_detect_template_int_append():
    t = _detect("Photo (100-200)")
    assert t["kind"] == "int_append"
    assert t["prefix"] == "Photo"
    assert t["range"]["width"] == 3


def test_detect_template_dual_int():
    t = _detect("IMG XXXX-XX (0-9999 0-99)")
    assert t["kind"] == "dual_int"
    assert "{a}" in t["prefix"] and "{b}" in t["prefix"]


def test_detect_template_multi_int():
    t = _detect("P1XX0XXX")
    assert t["kind"] == "multi_int"
    assert t["prefix"] == "P1{n0}0{n1}"
    assert [f["width"] for f in t["fields"]] == [2, 3]


def test_detect_template_multi_int_applies_range_to_last_field():
    t = _detect("P1XX0XXX (0-50)")
    assert t["kind"] == "multi_int"
    assert t["fields"][-1]["max"] == 50


def test_detect_template_hex2():
    t = _detect("Cam XX (A-F / 0-9)")
    assert t["kind"] == "hex2"
    assert t["prefix"] == "Cam {n}"
    assert t["range"] == {"width": 2}


def test_detect_template_hhmmss():
    t = _detect("Screenshot HHMMSS")
    assert t["kind"] == "hhmmss"
    assert t["prefix"] == "Screenshot {n}"
    assert t["range"] == {"min": 0, "max": 235959, "width": 6}


@pytest.mark.parametrize(
    "core, kind, prefix",
    [
        ("WIN YYYYMMDD", "yyyymmdd", "WIN {date}"),
        ("Desktop YYYY MM DD", "yyyy_mm_dd", "Desktop {date}"),
        ("obs YYYY-MM-DD", "yyyy_dash_mm_dd", "obs {date}"),
        ("XRecorder DDMMYYYY", "ddmmyyyy", "XRecorder {date}"),
        ("VDDMMYY", "ddmmyy", "V{date}"),
        ("ScreenRecording MM DD YYYY", "mm_dd_yyyy", "ScreenRecording {date}"),
        ("KakaoTalk Video YYYY MM", "yyyy_mm", "KakaoTalk Video {date}"),
        ("Month DD, YYYY", "month_dd_yyyy", "{date}"),
        ("Flipagram Month YYYY", "month_yyyy", "Flipagram {date}"),
        ("WhatsApp Video YYYY", "year", "WhatsApp Video {year}"),
        ("photo YYYY\ub144 M\uc6d4 D\uc77c", "ko_ymd", "photo {date}"),
        ("photo YYYY\u5e74M\u6708D\u65e5", "ja_ymd", "photo {date}"),
    ],
)
def test_detect_template_date_kinds(core, kind, prefix):
    t = _detect(core)
    assert t["kind"] == kind
    assert t["prefix"] == prefix


def test_detect_template_date_order_month_before_bare_year():
    # "Month DD, YYYY" must win over the bare-YYYY branch.
    assert _detect("For Month DD, YYYY")["kind"] == "month_dd_yyyy"


def test_detect_template_year_floor_applied():
    t = _detect("WhatsApp Video YYYY", yf=2015)
    assert t["yearMin"] == 2015


def test_detect_template_ddmmyy_year_window():
    t = _detect("VDDMMYY", yf=2006)
    assert t["yearMin"] == 2006
    assert t["yearMax"] == 2026


def test_detect_template_dual_int_without_x_runs():
    # No X placeholders in the core: falls back to bare XX/X token substitution.
    t = bd.detect_template(
        "Photo",
        [
            {
                "type": "dual_int",
                "min1": 0,
                "max1": 99,
                "width1": 2,
                "min2": 1,
                "max2": 9,
                "width2": 1,
                "raw": "(0-99 1-9)",
            }
        ],
        "",
        None,
    )
    assert t["kind"] == "dual_int"


def test_detect_template_multi_x_run_no_range():
    t = _detect("Doc XXX")
    assert t["kind"] == "int"
    assert t["range"] == {"min": 0, "max": 999, "width": 3}


def test_detect_template_single_x_no_range_defaults():
    t = _detect("My Movie X")
    assert t["kind"] == "int"
    assert t["range"]["min"] == 1
    assert t["range"]["max"] == 20


def test_detect_template_fixed():
    t = _detect("Just a plain string")
    assert t["kind"] == "fixed"
    assert t["prefix"] == "Just a plain string"


def test_detect_template_quoted_flag_from_core():
    t = _detect('"Quoted Name"')
    assert t["quoted"] is True


# --- parse_doc (end to end) -------------------------------------------------

@pytest.fixture
def small_section(monkeypatch):
    monkeypatch.setattr(
        bd,
        "sections_meta",
        [dict(id="map1", title="T1", hint="H1", start=1, end=6)],
    )


def test_parse_doc_end_to_end(small_section):
    text = "\n".join(
        [
            "HEADER (before start, ignored)",
            "IMG XXXX (0-9999) @bob [IMG 0057]",
            "Map Legend: ignore me",
            "WIN YYYYMMDD",
            "\u201cQuoted Name\u201d",  # smart quotes normalized
            "NSFW playlist keyword thing",
        ]
    )
    out = bd.parse_doc(text)

    assert out["meta"]["entryCount"] == len(out["entries"])
    titles = [e["title"] for e in out["entries"]]
    assert "IMG XXXX" in titles
    assert "WIN YYYYMMDD" in titles
    assert "Quoted Name" in titles  # smart quotes were normalized to ASCII

    img = next(e for e in out["entries"] if e["title"] == "IMG XXXX")
    assert img["map"] == "map1"
    assert img["credit"] == "@bob"
    assert img["example"] == "IMG 0057"
    assert img["padWidth"] == 4
    assert img["rangeDisplay"] == "(0-9999)"

    win = next(e for e in out["entries"] if e["title"] == "WIN YYYYMMDD")
    assert win["template"]["kind"] == "yyyymmdd"
    assert win["rangeDisplay"].startswith("YYYYMMDD")

    nsfw_entry = next(e for e in out["entries"] if "NSFW" in e["title"])
    assert nsfw_entry["nsfw"] is True


def test_parse_doc_meta_shape(small_section):
    out = bd.parse_doc("x\nIMG XXXX (0-9999)\n")
    meta = out["meta"]
    for key in ("sourceDoc", "sourceTitle", "entryCount", "maps", "attribution"):
        assert key in meta
    assert isinstance(meta["maps"], list)


def test_parse_doc_deduplicates(small_section):
    text = "\n".join(["h", "IMG XXXX (0-9999)", "IMG XXXX (0-9999)", "x", "y", "z"])
    out = bd.parse_doc(text)
    assert [e["title"] for e in out["entries"]].count("IMG XXXX") == 1


def test_parse_doc_skips_map_find_sort_lines(small_section):
    # "Findings" passes is_entry but is dropped by the Map/Find/Sort re.match guard.
    text = "\n".join(["h", "Findings summary line", "IMG XXXX (0-9999)", "x", "y", "z"])
    out = bd.parse_doc(text)
    titles = [e["title"] for e in out["entries"]]
    assert "IMG XXXX" in titles
    assert not any(t.startswith("Findings") for t in titles)


def test_parse_doc_int_append_range_display(small_section):
    # int_append has no raw range token, so rangeDisplay is synthesized from min/max.
    text = "\n".join(["h", "Photo (100-200)", "x", "y", "z", "w"])
    out = bd.parse_doc(text)
    photo = next(e for e in out["entries"] if e["title"] == "Photo")
    assert photo["template"]["kind"] == "int_append"
    assert photo["rangeDisplay"] == "(100-200)"


def test_parse_doc_skips_entries_with_empty_core(small_section):
    # "@only" is a valid entry line but strip_meta reduces it to nothing.
    text = "\n".join(["h", "@only", "IMG XXXX (0-9999)", "x", "y", "z"])
    out = bd.parse_doc(text)
    assert [e["title"] for e in out["entries"]] == ["IMG XXXX"]


def test_parse_doc_range_display_from_template_range(small_section):
    # "My Movie X" has no parenthesised range, so rangeDisplay is derived from
    # the template's synthesized range.
    text = "\n".join(["h", "My Movie X", "x", "y", "z", "w"])
    out = bd.parse_doc(text)
    mm = next(e for e in out["entries"] if e["title"] == "My Movie X")
    assert mm["rangeDisplay"] == "(1-20)"


def test_parse_doc_json_serializable(small_section):
    out = bd.parse_doc("h\nIMG XXXX (0-9999)\n")
    # Must round-trip through JSON exactly like main() writes it.
    assert json.loads(json.dumps(out, ensure_ascii=False)) == out


def test_main_writes_json_files(tmp_path, monkeypatch):
    doc = tmp_path / "doc.txt"
    doc.write_text("\n".join(["h", "IMG XXXX (0-9999)", "x", "y", "z"]), encoding="utf-8")
    monkeypatch.setattr(bd, "DOC", doc)
    monkeypatch.setattr(bd, "ROOT", tmp_path)
    monkeypatch.setattr(
        bd, "sections_meta", [dict(id="map1", title="T1", hint="H1", start=1, end=5)]
    )

    bd.main()

    data = json.loads((tmp_path / "data.json").read_text(encoding="utf-8"))
    minified = json.loads((tmp_path / "data.min.json").read_text(encoding="utf-8"))
    assert data == minified
    assert data["meta"]["entryCount"] == len(data["entries"])
    assert any(e["title"] == "IMG XXXX" for e in data["entries"])
