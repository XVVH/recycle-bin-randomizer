#!/usr/bin/env python3
"""Guard that the committed artifacts stay in sync.

``data.json`` (read by the tests), ``data.min.json`` (embedded in the page),
and ``index.html`` (shipped UI) are generated together but committed as static
files, so they can silently drift if only one is regenerated. These tests fail
loudly when that happens.
"""
from __future__ import annotations

import base64
import json
import re
import shutil
from pathlib import Path

import build_index as bi

ROOT = Path(__file__).resolve().parent


def _load(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def test_data_json_matches_min_json():
    assert _load("data.json") == _load("data.min.json")


def test_index_html_embeds_current_min_json():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    m = re.search(r'id="DATA_B64">([^<]+)<', html)
    assert m, "DATA_B64 payload not found in index.html"
    embedded = json.loads(base64.b64decode(m.group(1).strip()).decode("utf-8"))
    assert embedded == _load("data.min.json")


def test_index_html_has_no_drift(tmp_path, monkeypatch):
    # Regenerating index.html from the committed data.min.json must reproduce
    # the committed index.html byte-for-byte.
    shutil.copy(ROOT / "data.min.json", tmp_path / "data.min.json")
    monkeypatch.setattr(bi, "ROOT", tmp_path)
    bi.main()
    regenerated = (tmp_path / "index.html").read_text(encoding="utf-8")
    committed = (ROOT / "index.html").read_text(encoding="utf-8")
    assert regenerated == committed
