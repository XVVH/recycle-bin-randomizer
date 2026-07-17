#!/usr/bin/env python3
"""Shared generation logic (Python mirror of index.html JS) + rubric tests."""
from __future__ import annotations

import json
import random
import re
import sys
from calendar import monthrange
from datetime import date
from pathlib import Path

from common import DATE_KIND_TO_YMD, DATE_KINDS, MONTHS

ROOT = Path(__file__).resolve().parent


def pad(n: int, w: int) -> str:
    s = str(int(n))
    width = max(0, int(w or 0))
    if width <= 0:
        return s
    return s.zfill(width)


def random_ymd(year_min: int, year_max: int | None = None, rng: random.Random | None = None) -> dict:
    rng = rng or random
    this_year = date.today().year
    y0 = year_min or 2008
    y1 = year_max if year_max is not None else this_year
    y1 = max(y0, min(y1, this_year))
    y = rng.randint(y0, y1)
    m = rng.randint(1, 12)
    d = rng.randint(1, monthrange(y, m)[1])
    return {
        "y": y,
        "m": m,
        "d": d,
        "compact": f"{y}{m:02d}{d:02d}",
        "spaced": f"{y} {m:02d} {d:02d}",
        "dashed": f"{y}-{m:02d}-{d:02d}",
        "ddmmyyyy": f"{d:02d}{m:02d}{y}",
        "ddmmyy": f"{d:02d}{m:02d}{y % 100:02d}",
        "mm_dd_yyyy": f"{m:02d} {d:02d} {y}",
        "yyyy_mm": f"{y} {m:02d}",
        "long": f"{MONTHS[m-1]} {d:02d}, {y}",
        "long_single_d": f"{MONTHS[m-1]} {d}, {y}",
        "month_yyyy": f"{MONTHS[m-1]} {y}",
        "ko": f"{y}년 {m}월 {d}일",
        "ja": f"{y}年{m}月{d}日",
    }


def maybe_quote(s: str, quoted: bool, prefer: bool) -> str:
    if prefer and quoted and not (s.startswith('"') and s.endswith('"')):
        return f'"{s}"'
    return s


def generate_from(entry: dict, prefer_quoted: bool = True, rng: random.Random | None = None) -> str:
    rng = rng or random
    t = entry["template"]
    s = t.get("prefix") or t.get("raw_core") or entry["title"]
    r = t.get("range") or {}
    y_min = t.get("yearMin") or 2008
    y_max = t.get("yearMax")

    kind = t.get("kind")
    if kind == "fixed":
        pass
    elif kind in ("int", "int_append"):
        n = rng.randint(r.get("min", 0), r.get("max", 9999))
        p = pad(n, r.get("width") if r.get("width") is not None else len(str(r.get("max", 0))))
        s = (t["prefix"] + " " + p).strip() if kind == "int_append" else t["prefix"].replace("{n}", p)
    elif kind == "dual_int":
        a = pad(rng.randint(r["min1"], r["max1"]), r["width1"])
        b = pad(rng.randint(r["min2"], r["max2"]), r["width2"])
        s = t["prefix"].replace("{a}", a).replace("{b}", b)
    elif kind == "multi_int":
        s = t["prefix"]
        for i, f in enumerate(t.get("fields") or []):
            n = rng.randint(f.get("min", 0), f.get("max", 10 ** f.get("width", 1) - 1))
            s = s.replace("{n%d}" % i, pad(n, f.get("width", 1)))
    elif kind == "hex2":
        hexchars = "0123456789ABCDEF"
        n = hexchars[rng.randint(0, 15)] + hexchars[rng.randint(0, 15)]
        # pad to width if >2
        w = (r or {}).get("width", 2)
        while len(n) < w:
            n = "0" + n
        s = t["prefix"].replace("{n}", n[:w] if len(n) > w else n)
    elif kind == "hhmmss":
        s = t["prefix"].replace(
            "{n}", f"{rng.randint(0,23):02d}{rng.randint(0,59):02d}{rng.randint(0,59):02d}"
        )
    elif kind in DATE_KIND_TO_YMD:
        s = t["prefix"].replace("{date}", random_ymd(y_min, y_max, rng)[DATE_KIND_TO_YMD[kind]])
    elif kind == "year":
        this_year = date.today().year
        y1 = y_max if y_max is not None else this_year
        s = t["prefix"].replace("{year}", str(rng.randint(y_min, max(y_min, min(y1, this_year)))))
    else:
        s = entry["title"]

    s = re.sub(r"\{[^}]+\}", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return maybe_quote(s, bool(t.get("quoted")), prefer_quoted)


# --- Rubric validation ---

RE_YMD_COMPACT = re.compile(r"(?<!\d)(\d{4})(\d{2})(\d{2})(?!\d)")
RE_YMD_SPACED = re.compile(r"(?<!\d)(\d{4}) (\d{2}) (\d{2})(?!\d)")
RE_YMD_DASH = re.compile(r"(?<!\d)(\d{4})-(\d{2})-(\d{2})(?!\d)")
RE_DMY = re.compile(r"(?<!\d)(\d{2})(\d{2})(\d{4})(?!\d)")
RE_MDY = re.compile(r"(?<!\d)(\d{2}) (\d{2}) (\d{4})(?!\d)")
RE_YM = re.compile(r"(?<!\d)(\d{4}) (\d{2})(?!\d)")
RE_LONG = re.compile(
    r"(January|February|March|April|May|June|July|August|September|October|November|December) (\d{1,2}), (\d{4})"
)
RE_MONTH_YEAR = re.compile(
    r"(January|February|March|April|May|June|July|August|September|October|November|December) (\d{4})"
)
RE_YEAR = re.compile(r"(?<!\d)(19|20)\d{2}(?!\d)")
RE_KO = re.compile(r"(\d{4})년 (\d{1,2})월 (\d{1,2})일")
RE_JA = re.compile(r"(\d{4})年(\d{1,2})月(\d{1,2})日")


def valid_ymd(y: int, m: int, d: int) -> bool:
    if not (1 <= m <= 12):
        return False
    if y < 1990 or y > date.today().year + 1:
        return False
    return 1 <= d <= monthrange(y, m)[1]


def assert_no_placeholders(s: str) -> None:
    assert "{date}" not in s and "{year}" not in s and "{n}" not in s
    assert "YYYY" not in s and "Month DD" not in s and "Month D," not in s
    assert "MM DD" not in s or re.search(r"\d{2} \d{2}", s)  # numeric ok
    assert "YYYYMMDD" not in s
    assert "DDMMYYYY" not in s


def validate_output(entry: dict, s: str) -> None:
    """Rubric: output is pasteable, padded/dated correctly for template kind."""
    kind = entry["template"]["kind"]
    bare = s.strip('"')
    assert_no_placeholders(bare) if kind != "fixed" else None

    if kind in ("int", "int_append"):
        r = entry["template"]["range"]
        w = r["width"]
        bare = s.strip('"')
        # Reconstruct: padded field must appear as zero-padded substring of width w
        # and value in [min,max]. Prefer matching replace of {n} pattern.
        pref = entry["template"]["prefix"]
        if "{n}" in pref:
            # escape and allow the number
            left, right = pref.split("{n}", 1)
            # strip quotes already in bare
            assert bare.startswith(left.rstrip()) or left.strip() in bare or bare.startswith(left), (bare, pref)
        nums = re.findall(r"\d+", bare)
        assert nums, (entry["title"], s)
        ok = False
        for n in nums:
            if len(n) == w and r["min"] <= int(n) <= r["max"]:
                ok = True
                break
            # prefix digit merge: e.g. MAQ0 + 0489 → MAQ00489 — accept trailing w digits
            if len(n) > w and r["min"] <= int(n[-w:]) <= r["max"] and n.endswith(n[-w:]):
                ok = True
                break
        assert ok, (entry["title"], s, w, r, nums)

    if kind == "multi_int":
        bare = s.strip('"')
        assert "X" not in bare and "{n" not in bare, (entry["title"], s)
        for f in entry["template"].get("fields") or []:
            w = f["width"]
            # at least one w-digit run in range
            found = False
            for n in re.findall(r"\d+", bare):
                if len(n) >= w and f["min"] <= int(n[-w:]) <= f["max"]:
                    found = True
                    break
            assert found, (entry["title"], s, f)

    if kind == "yyyymmdd":
        m = RE_YMD_COMPACT.search(bare)
        assert m, s
        assert valid_ymd(int(m.group(1)), int(m.group(2)), int(m.group(3))), s
    if kind == "yyyy_mm_dd":
        m = RE_YMD_SPACED.search(bare)
        assert m, s
        assert valid_ymd(int(m.group(1)), int(m.group(2)), int(m.group(3))), s
    if kind == "yyyy_dash_mm_dd":
        m = RE_YMD_DASH.search(bare)
        assert m, s
        assert valid_ymd(int(m.group(1)), int(m.group(2)), int(m.group(3))), s
    if kind == "ddmmyyyy":
        m = RE_DMY.search(bare)
        assert m, s
        assert valid_ymd(int(m.group(3)), int(m.group(2)), int(m.group(1))), s
    if kind == "ddmmyy":
        m = re.search(r"(?<!\d)(\d{2})(\d{2})(\d{2})(?!\d)", bare)
        assert m, s
        yy = int(m.group(3))
        # map 00–99 → 2000–2099 for recycle-bin era
        y = 2000 + yy if yy < 100 else yy
        assert valid_ymd(y, int(m.group(2)), int(m.group(1))), s
        assert "DDMMYY" not in bare and "VDDMMYY" not in bare
    if kind == "mm_dd_yyyy":
        m = RE_MDY.search(bare)
        assert m, s
        assert valid_ymd(int(m.group(3)), int(m.group(1)), int(m.group(2))), s
    if kind == "yyyy_mm":
        m = RE_YM.search(bare)
        assert m, s
        assert 1 <= int(m.group(2)) <= 12
    if kind == "month_dd_yyyy":
        m = RE_LONG.search(bare)
        assert m, s
        mon = MONTHS.index(m.group(1)) + 1
        assert valid_ymd(int(m.group(3)), mon, int(m.group(2))), s
        assert "Month" not in bare
    if kind == "month_yyyy":
        m = RE_MONTH_YEAR.search(bare)
        assert m, s
    if kind == "year":
        assert RE_YEAR.search(bare), s
        assert "YYYY" not in bare
    if kind == "ko_ymd":
        m = RE_KO.search(bare)
        assert m, s
        assert valid_ymd(int(m.group(1)), int(m.group(2)), int(m.group(3))), s
    if kind == "ja_ymd":
        m = RE_JA.search(bare)
        assert m, s
        assert valid_ymd(int(m.group(1)), int(m.group(2)), int(m.group(3))), s
    if kind == "hhmmss":
        m = re.search(r"(\d{6})", bare)
        assert m, s
        hh, mm, ss = int(m.group(1)[:2]), int(m.group(1)[2:4]), int(m.group(1)[4:6])
        assert 0 <= hh <= 23 and 0 <= mm <= 59 and 0 <= ss <= 59


def run_tests(seed: int = 42, rounds: int = 5) -> int:
    data_path = ROOT / "data.json"
    if not data_path.exists():
        raise SystemExit(f"Missing {data_path.name}; run build_data.py first to generate it.")
    data = json.loads(data_path.read_text(encoding="utf-8"))
    entries = data["entries"]
    rng = random.Random(seed)
    failures = []

    # Rubric R1: IMG XXXX pads to 4
    img = next((e for e in entries if e["title"] == "IMG XXXX"), None)
    if img is None:
        failures.append("R1 | fixture entry 'IMG XXXX' not found in data.json")
    else:
        for _ in range(50):
            s = generate_from(img, True, random.Random(rng.randint(0, 10**9)))
            bare = s.strip('"')
            m = re.search(r"IMG\s+(\d+)", bare)
            try:
                assert m and len(m.group(1)) == 4, s
                assert 0 <= int(m.group(1)) <= 9999
            except AssertionError as ex:
                failures.append(f"R1 | IMG XXXX | {ex}")
                break

    # Rubric R2: date kinds leave no Month/YYYY tokens
    date_kinds = DATE_KINDS
    by_kind = {}
    for e in entries:
        by_kind.setdefault(e["template"]["kind"], []).append(e)

    for kind in sorted(date_kinds):
        pool = by_kind.get(kind, [])
        if not pool:
            # only fail if we expect them from doc
            if kind in ("yyyymmdd", "yyyy_mm_dd", "year", "month_dd_yyyy"):
                failures.append(f"missing kind {kind}")
            continue
        for e in pool:
            for i in range(rounds):
                try:
                    s = generate_from(e, True, random.Random(seed + i * 17 + hash(e["title"]) % 1000))
                    validate_output(e, s)
                except Exception as ex:
                    failures.append(f"{kind} | {e['title'][:50]} | {ex}")

    # Rubric R3: every entry generates without exception; no leftover placeholders for non-fixed
    for e in entries:
        try:
            s = generate_from(e, True, random.Random(hash(e["title"]) % (10**6)))
            if e["template"]["kind"] != "fixed":
                assert "{date}" not in s and "YYYYMMDD" not in s
                if e["template"]["kind"] == "month_dd_yyyy":
                    assert "Month DD" not in s and not re.search(r"\bMonth\b", s)
        except Exception as ex:
            failures.append(f"gen | {e['title'][:50]} | {ex}")

    # Rubric R4: fixed date-like residue should be zero after parse fix
    residue = [
        e
        for e in entries
        if e["template"]["kind"] == "fixed"
        and re.search(r"YYYY|Month DD|DDMMYYYY|YYYY-MM-DD", e["title"])
    ]
    if residue:
        failures.append("fixed residue: " + "; ".join(e["title"][:40] for e in residue[:8]))

    # Spot prints
    print("--- spot samples ---")
    for title in [
        "IMG XXXX",
        "WIN YYYYMMDD",
        "Desktop YYYY MM DD",
        "Month DD, YYYY",
        "For Month DD, YYYY",
        "WhatsApp Video YYYY",
        "obs YYYY-MM-DD",
        "XRecorder DDMMYYYY",
        "VDDMMYY",
        "ScreenRecording MM DD YYYY",
        "KakaoTalk Video YYYY MM",
    ]:
        e = next((x for x in entries if x["title"] == title), None)
        if not e:
            e = next((x for x in entries if title in x["title"]), None)
        if e:
            samples = [generate_from(e, True, random.Random(i + 3)) for i in range(3)]
            print(f"{e['title'][:40]:40} kind={e['template']['kind']:16} → {samples}")

    print("--- kind counts ---")
    from collections import Counter

    print(Counter(e["template"]["kind"] for e in entries))

    if failures:
        print(f"\nFAIL {len(failures)} issues:")
        for f in failures[:40]:
            print(" ", f)
        return 1
    print(f"\nPASS rubric ({len(entries)} entries, seed={seed})")
    return 0


if __name__ == "__main__":
    sys.exit(run_tests())
