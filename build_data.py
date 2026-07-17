#!/usr/bin/env python3
"""Parse YouTube Recycle Bin Google Doc export → data.json + embed index.html."""
from __future__ import annotations

import base64
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOC = Path("/tmp/yt-recycle-doc.txt")

sections_meta = [
    dict(
        id="map1",
        title="Map 1 — Brand new (~0 views)",
        hint="Sort by Upload Date (mandatory). Prefer non-biased searcher.",
        start=82,
        end=316,
    ),
    dict(
        id="map2",
        title="Map 2 — Old & forgotten (~0 views)",
        hint="Sort by View Count optional. Optional Before:YEAR filter.",
        start=316,
        end=1386,
    ),
    dict(
        id="map3",
        title="Map 3 — Low-view 2006–2008",
        hint="Before:2008 / early years. Sort by View Count optional.",
        start=1386,
        end=1585,
    ),
]

SKIP_PREFIXES = (
    "Map Legend",
    "Sort by",
    "Search Tools",
    "Find brand",
    "Find old",
    "Find low",
    "New Leads",
    "YouTube",
    "____",
    "What is",
    "KVN",
    "UPDATE",
    "TABLE",
    "Preface",
    "Tools",
    "Special Thanks",
    "http",
    "NoViewTube",
    "Other",
)


def is_entry(line: str) -> bool:
    if not line or len(line) < 2:
        return False
    if any(line.startswith(p) for p in SKIP_PREFIXES):
        return False
    if line.startswith("!") or line.startswith("["):
        return False
    if re.fullmatch(r"[\W_]+", line):
        return False
    return True


def extract_credit(s: str) -> str:
    m = re.search(r"(@[\w.\-]+)", s)
    return m.group(1) if m else ""


def extract_example(s: str) -> str:
    m = re.search(r"\[([^\]]+)\]", s)
    return m.group(1).strip() if m else ""


def extract_sources(s: str) -> list[str]:
    cats = []
    for m in re.finditer(r"\(([^)]+)\)", s):
        inner = m.group(1).strip()
        if re.fullmatch(r"[\dA-Fa-f\s/\-]+", inner):
            continue
        if re.fullmatch(r"\d+-\d+", inner):
            continue
        if re.fullmatch(r">\d{4}", inner):
            continue
        if "Variable" in inner or "Example" in inner:
            continue
        cats.append(inner)
    return cats


def year_floor(s: str) -> int | None:
    m = re.search(r"\(>(\d{4})\)", s)
    return int(m.group(1)) if m else None


def strip_meta(s: str) -> str:
    s2 = re.sub(r"@[^\s]+", "", s)
    s2 = re.sub(r"\[[^\]]*\]", "", s2)
    return " ".join(s2.split()).strip()


def parse_range(s: str) -> list[dict]:
    m = re.search(r"\((\d+)\s*-\s*(\d+)\s+(\d+)\s*-\s*(\d+)\)", s)
    if m:
        return [
            {
                "type": "dual_int",
                "min1": int(m.group(1)),
                "max1": int(m.group(2)),
                "width1": max(len(m.group(1)), len(m.group(2))),
                "min2": int(m.group(3)),
                "max2": int(m.group(4)),
                "width2": max(len(m.group(3)), len(m.group(4))),
                "raw": m.group(0),
            }
        ]
    ranges = []
    for m in re.finditer(r"\((\d+)\s*-\s*(\d+)\)", s):
        a, b = m.group(1), m.group(2)
        ranges.append(
            {
                "type": "int",
                "min": int(a),
                "max": int(b),
                "width": max(len(a), len(b)),
                "raw": m.group(0),
            }
        )
    if re.search(r"\(A-F\s*/\s*0-9\)", s, re.I):
        ranges.append({"type": "hex2", "raw": "(A-F / 0-9)", "width": 2})
    return ranges


def detect_template(core: str, ranges: list, example: str, y_floor: int | None) -> dict:
    core_clean = re.sub(r"\([^)]*\)", "", core)
    core_clean = " ".join(core_clean.split()).strip().strip('"').strip("'")
    quoted = core.strip().startswith('"') or (example and str(example).startswith('"'))
    t = core_clean
    r0 = ranges[0] if ranges else None
    yf = y_floor

    # --- Date patterns (order matters: specific before bare YYYY) ---

    # Month DD, YYYY / Month D, YYYY (English long form)
    if re.search(r"Month\s+D{1,2},\s*YYYY", t, re.I):
        pref = re.sub(r"Month\s+D{1,2},\s*YYYY", "{date}", t, flags=re.I)
        return {
            "kind": "month_dd_yyyy",
            "prefix": pref,
            "quoted": True,
            "raw_core": core_clean,
            "yearMin": yf or 2006,
            "yearMax": 2015 if (yf or 2006) < 2010 else None,
        }

    # YYYY-MM-DD
    if re.search(r"YYYY-MM-DD", t):
        return {
            "kind": "yyyy_dash_mm_dd",
            "prefix": t.replace("YYYY-MM-DD", "{date}"),
            "quoted": quoted,
            "raw_core": core_clean,
            "yearMin": yf or 2008,
        }

    # DDMMYYYY (no separators, 4-digit year)
    if re.search(r"DDMMYYYY", t):
        return {
            "kind": "ddmmyyyy",
            "prefix": t.replace("DDMMYYYY", "{date}"),
            "quoted": quoted,
            "raw_core": core_clean,
            "yearMin": yf or 2008,
        }

    # DDMMYY (2-digit year) — e.g. VDDMMYY → V + 181015
    if re.search(r"DDMMYY", t):
        return {
            "kind": "ddmmyy",
            "prefix": t.replace("DDMMYY", "{date}"),
            "quoted": quoted,
            "raw_core": core_clean,
            "yearMin": yf or 2006,
            "yearMax": yf + 20 if yf else 2015,
        }

    # MM DD YYYY
    if re.search(r"MM\s+DD\s+YYYY", t):
        return {
            "kind": "mm_dd_yyyy",
            "prefix": re.sub(r"MM\s+DD\s+YYYY", "{date}", t),
            "quoted": quoted,
            "raw_core": core_clean,
            "yearMin": yf or 2008,
        }

    # YYYY MM DD
    if re.search(r"YYYY\s+MM\s+DD", t):
        return {
            "kind": "yyyy_mm_dd",
            "prefix": re.sub(r"YYYY\s+MM\s+DD", "{date}", t),
            "quoted": quoted,
            "raw_core": core_clean,
            "yearMin": yf or 2008,
        }

    # YYYY MM (year + month only)
    if re.search(r"YYYY\s+MM\b", t) and "DD" not in t:
        return {
            "kind": "yyyy_mm",
            "prefix": re.sub(r"YYYY\s+MM\b", "{date}", t),
            "quoted": quoted,
            "raw_core": core_clean,
            "yearMin": yf or 2008,
        }

    # Compact YYYYMMDD
    if re.search(r"YYYYMMDD", t):
        return {
            "kind": "yyyymmdd",
            "prefix": t.replace("YYYYMMDD", "{date}"),
            "quoted": quoted,
            "raw_core": core_clean,
            "yearMin": yf or 2008,
        }

    # Korean / Japanese calendar placeholders
    if re.search(r"YYYY년\s*M월\s*D일", t):
        return {
            "kind": "ko_ymd",
            "prefix": re.sub(r"YYYY년\s*M월\s*D일", "{date}", t),
            "quoted": quoted,
            "raw_core": core_clean,
            "yearMin": yf or 2008,
        }
    if re.search(r"YYYY年M月D日", t):
        return {
            "kind": "ja_ymd",
            "prefix": t.replace("YYYY年M月D日", "{date}"),
            "quoted": quoted,
            "raw_core": core_clean,
            "yearMin": yf or 2008,
        }

    # Flipagram Month YYYY — month name + year
    if re.search(r"Month\s+YYYY", t, re.I) and "DD" not in t and "D," not in t:
        return {
            "kind": "month_yyyy",
            "prefix": re.sub(r"Month\s+YYYY", "{date}", t, flags=re.I),
            "quoted": quoted,
            "raw_core": core_clean,
            "yearMin": yf or 2010,
        }

    # Bare YYYY (after all multi-token date forms)
    if re.search(r"YYYY", t):
        return {
            "kind": "year",
            "prefix": t.replace("YYYY", "{year}"),
            "quoted": quoted,
            "raw_core": core_clean,
            "yearMin": yf or 2010,
        }

    if re.search(r"HHMMSS", t):
        return {
            "kind": "hhmmss",
            "prefix": t.replace("HHMMSS", "{n}"),
            "quoted": True,
            "raw_core": core_clean,
            "range": {"min": 0, "max": 235959, "width": 6},
        }

    if r0 and r0.get("type") == "dual_int":
        m1 = re.search(r"(X+)", t)
        w1 = len(m1.group(1)) if m1 else r0["width1"]
        t2 = t.replace(m1.group(1), "{a}", 1) if m1 else t
        m2 = re.search(r"(X+)", t2)
        w2 = len(m2.group(1)) if m2 else r0["width2"]
        if m2:
            t2 = t2.replace(m2.group(1), "{b}", 1)
        else:
            t2 = re.sub(r"\bXX\b", "{a}", t, count=1)
            t2 = re.sub(r"\bX\b", "{b}", t2, count=1)
            w1, w2 = 2, 1
        return {
            "kind": "dual_int",
            "prefix": t2,
            "quoted": quoted,
            "raw_core": core_clean,
            "range": {**r0, "width1": w1, "width2": w2},
        }

    # Multiple X-runs (e.g. P1XX0XXX): independent zero-padded fields
    x_runs = list(re.finditer(r"X+", t))
    if len(x_runs) >= 2:
        widths = [len(m.group(0)) for m in x_runs]
        pref = t
        # replace right-to-left so indices stay stable
        for i, m in enumerate(reversed(x_runs)):
            idx = len(x_runs) - 1 - i
            pref = pref[: m.start()] + "{n%d}" % idx + pref[m.end() :]
        fields = []
        for w in widths:
            fields.append({"min": 0, "max": 10**w - 1, "width": w})
        # if a single int range was given, apply to the last field (often the varying suffix)
        if r0 and r0.get("type") == "int":
            last = fields[-1]
            last["min"] = max(0, r0["min"])
            last["max"] = min(r0["max"], last["max"])
            last["min"] = min(last["min"], last["max"])
        return {
            "kind": "multi_int",
            "prefix": pref,
            "quoted": quoted,
            "raw_core": core_clean,
            "fields": fields,
        }

    m = re.search(r"(X{2,})", t)
    if m:
        x_count = len(m.group(1))
        if r0 and r0.get("type") == "hex2":
            return {
                "kind": "hex2",
                "prefix": t.replace(m.group(1), "{n}", 1),
                "quoted": quoted,
                "raw_core": core_clean,
                "range": {"width": x_count},
            }
        field_max = 10**x_count - 1
        if r0 and r0.get("type") == "int":
            mn, mx = r0["min"], r0["max"]
        else:
            mn, mx = 0, field_max
        # X width is authoritative: never generate more digits than placeholders
        mx = min(mx, field_max)
        mn = max(0, min(mn, mx))
        return {
            "kind": "int",
            "prefix": t.replace(m.group(1), "{n}", 1),
            "quoted": quoted,
            "raw_core": core_clean,
            "range": {"min": mn, "max": mx, "width": x_count},
        }

    if re.search(r"\bX\b", t):
        if r0 and r0.get("type") == "int":
            mn, mx = r0["min"], r0["max"]
        else:
            mn, mx = 1, 20
        # single X: pad to digit width of max (My Movie 05 / 20), not forced 1
        w = max(1, len(str(mx)), (r0 or {}).get("width", 1) if r0 else 1)
        field_max = 10**w - 1
        mx = min(mx, field_max)
        mn = max(0, min(mn, mx))
        return {
            "kind": "int",
            "prefix": re.sub(r"\bX\b", "{n}", t, count=1),
            "quoted": quoted,
            "raw_core": core_clean,
            "range": {"min": mn, "max": mx, "width": w},
        }

    if r0 and r0.get("type") == "int":
        w = max(r0.get("width", 1), len(str(r0["max"])))
        return {
            "kind": "int_append",
            "prefix": t,
            "quoted": quoted,
            "raw_core": core_clean,
            "range": {"min": r0["min"], "max": r0["max"], "width": w},
        }

    return {"kind": "fixed", "prefix": t, "quoted": quoted, "raw_core": core_clean}


def parse_doc(text: str) -> dict:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = (
        text.replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2019", "'")
        .replace("\u2013", "-")
        .replace("\u2014", "-")
    )
    lines = [ln.strip() for ln in text.split("\n")]
    entries = []
    seen = set()

    for sec in sections_meta:
        for i in range(sec["start"], min(sec["end"], len(lines))):
            line = lines[i]
            if not is_entry(line):
                continue
            if re.match(r"^(Map|Find|Sort|Search|New Leads)", line):
                continue
            credit = extract_credit(line)
            example = extract_example(line)
            sources = extract_sources(line)
            yf = year_floor(line)
            core = strip_meta(line)
            if not core or len(core) < 2:
                continue
            ranges = parse_range(line) or parse_range(core)
            tmpl = detect_template(core, ranges, example, yf)
            title = tmpl["raw_core"]
            source_label = ", ".join(sources) if sources else ""
            key = (sec["id"], title, tmpl["kind"], str(tmpl.get("range")), str(tmpl.get("yearMin")))
            if key in seen:
                continue
            seen.add(key)
            rd = ranges[0]["raw"] if ranges else ""
            if not rd and tmpl.get("range") and isinstance(tmpl["range"], dict) and "min" in tmpl["range"]:
                rd = f"({tmpl['range']['min']}-{tmpl['range']['max']})"
            # surface date field in range column for UI
            if not rd and tmpl["kind"] in {
                "yyyymmdd",
                "yyyy_mm_dd",
                "yyyy_dash_mm_dd",
                "ddmmyyyy",
                "ddmmyy",
                "mm_dd_yyyy",
                "yyyy_mm",
                "month_dd_yyyy",
                "month_yyyy",
                "year",
                "ko_ymd",
                "ja_ymd",
            }:
                rd = {
                    "yyyymmdd": "YYYYMMDD",
                    "yyyy_mm_dd": "YYYY MM DD",
                    "yyyy_dash_mm_dd": "YYYY-MM-DD",
                    "ddmmyyyy": "DDMMYYYY",
                    "ddmmyy": "DDMMYY",
                    "mm_dd_yyyy": "MM DD YYYY",
                    "yyyy_mm": "YYYY MM",
                    "month_dd_yyyy": "Month DD, YYYY",
                    "month_yyyy": "Month YYYY",
                    "year": "YYYY",
                    "ko_ymd": "YYYY년 M월 D일",
                    "ja_ymd": "YYYY年M月D日",
                }[tmpl["kind"]]
                if tmpl.get("yearMin"):
                    rd += f" (≥{tmpl['yearMin']})"
            pad_w = None
            if tmpl.get("range") and isinstance(tmpl["range"], dict):
                pad_w = tmpl["range"].get("width") or tmpl["range"].get("width1")
            blob = " ".join(
                [
                    title,
                    source_label,
                    line,
                    example or "",
                ]
            )
            nsfw = bool(re.search(r"\bNSFW\b", blob, re.I))
            entries.append(
                {
                    "map": sec["id"],
                    "mapTitle": sec["title"],
                    "mapHint": sec["hint"],
                    "title": title,
                    "source": source_label,
                    "credit": credit,
                    "example": example,
                    "rangeDisplay": rd,
                    "padWidth": pad_w,
                    "nsfw": nsfw,
                    "template": tmpl,
                }
            )

    return {
        "meta": {
            "sourceDoc": "https://docs.google.com/document/d/1mV5PhumaIJ8mtH8XmohqXkk5fjK_HlqcineMccPQm5A",
            "sourceTitle": "YouTube's Recycle Bin (KVN AUST) Update 5.0",
            "entryCount": len(entries),
            "maps": sections_meta,
            "attribution": (
                "Keyphrases compiled by KVN AUST and community contributors. "
                "This UI is an independent helper; not affiliated with YouTube or the doc author."
            ),
            "paddingRule": (
                "Numeric fields pad with leading zeros to the width of the X placeholder "
                "(XXXX → 4 digits: 57 → 0057)."
            ),
            "dateRule": (
                "Date placeholders fill real calendar dates: YYYYMMDD, YYYY MM DD, YYYY-MM-DD, "
                "DDMMYYYY, DDMMYY (e.g. VDDMMYY), MM DD YYYY, YYYY MM, Month DD, YYYY, "
                "Month YYYY, bare YYYY, KO/JA forms. Year floors from (>YYYY) notes when present."
            ),
        },
        "entries": entries,
    }


def main() -> None:
    if not DOC.exists():
        raise SystemExit(
            f"Input doc not found: {DOC}\n"
            "Download it first (see README 'Rebuild from the Google Doc'):\n"
            '  curl -sSL "https://docs.google.com/document/d/'
            '1mV5PhumaIJ8mtH8XmohqXkk5fjK_HlqcineMccPQm5A/export?format=txt" '
            f'-o {DOC}'
        )
    text = DOC.read_text(encoding="utf-8", errors="replace")
    out = parse_doc(text)
    (ROOT / "data.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    (ROOT / "data.min.json").write_text(
        json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    print("entries", out["meta"]["entryCount"])
    print(Counter(e["template"]["kind"] for e in out["entries"]))
    missed = [
        e
        for e in out["entries"]
        if e["template"]["kind"] == "fixed"
        and re.search(r"YYYY|Month|MM DD|DDMM", e["title"])
    ]
    print("fixed still looking date-like:", len(missed))
    for e in missed[:15]:
        print(" ", e["title"][:80])


if __name__ == "__main__":
    main()
