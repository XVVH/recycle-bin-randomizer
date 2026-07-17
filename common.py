#!/usr/bin/env python3
"""Shared constants for parsing, generation, and the embedded UI.

Single source of truth for the date template kinds so ``build_data.py``,
``build_index.py`` (which injects them into the page's JS), and
``test_generation.py`` cannot drift apart.
"""
from __future__ import annotations

MONTHS = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

# Template kind -> human label shown in the "Range / date form" column.
DATE_KIND_LABELS = {
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
}

# All template kinds that render a date/year (used for pool filtering + labels).
DATE_KINDS = frozenset(DATE_KIND_LABELS)

# Template kind -> key of the ``random_ymd`` result to substitute for ``{date}``.
# ``year`` is intentionally absent: it is handled specially (clamped to the
# current year) rather than via a full calendar date.
DATE_KIND_TO_YMD = {
    "yyyymmdd": "compact",
    "yyyy_mm_dd": "spaced",
    "yyyy_dash_mm_dd": "dashed",
    "ddmmyyyy": "ddmmyyyy",
    "ddmmyy": "ddmmyy",
    "mm_dd_yyyy": "mm_dd_yyyy",
    "yyyy_mm": "yyyy_mm",
    "month_dd_yyyy": "long",
    "month_yyyy": "month_yyyy",
    "ko_ymd": "ko",
    "ja_ymd": "ja",
}
