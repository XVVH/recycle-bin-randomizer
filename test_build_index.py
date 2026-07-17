#!/usr/bin/env python3
"""Unit tests for build_index.py (data.min.json → self-contained index.html)."""
from __future__ import annotations

import base64
import json

import pytest

import build_index as bi


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    """Point build_index at a temp dir so we never touch the real index.html."""
    data = {
        "meta": {"entryCount": 1, "sourceDoc": "https://example.test/doc"},
        "entries": [
            {
                "map": "map1",
                "title": "IMG XXXX",
                "template": {"kind": "int", "prefix": "IMG {n}"},
            }
        ],
    }
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    (tmp_path / "data.min.json").write_text(payload, encoding="utf-8")
    monkeypatch.setattr(bi, "ROOT", tmp_path)
    return tmp_path, payload


def test_main_writes_index_html(sandbox):
    tmp_path, _ = sandbox
    bi.main()
    out = tmp_path / "index.html"
    assert out.exists()
    assert out.stat().st_size > 0


def test_main_embeds_base64_payload(sandbox):
    tmp_path, payload = sandbox
    bi.main()
    html = (tmp_path / "index.html").read_text(encoding="utf-8")
    expected_b64 = base64.b64encode(payload.encode("utf-8")).decode("ascii")
    assert expected_b64 in html


def test_embedded_payload_decodes_back_to_data(sandbox):
    tmp_path, payload = sandbox
    bi.main()
    html = (tmp_path / "index.html").read_text(encoding="utf-8")
    marker = 'id="DATA_B64">'
    start = html.index(marker) + len(marker)
    end = html.index("</script>", start)
    b64 = html[start:end].strip()
    decoded = base64.b64decode(b64).decode("utf-8")
    assert json.loads(decoded) == json.loads(payload)


def test_main_output_has_expected_structure(sandbox):
    tmp_path, _ = sandbox
    bi.main()
    html = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert html.startswith("<!DOCTYPE html>")
    assert "<title>Recycle Bin Randomizer</title>" in html
    # f-string double-brace escaping must yield single-brace JS placeholders.
    assert "replace('{n}'" in html
    assert "{{" not in html
    assert 'id="btnGen"' in html


def test_main_is_idempotent(sandbox):
    tmp_path, _ = sandbox
    bi.main()
    first = (tmp_path / "index.html").read_text(encoding="utf-8")
    bi.main()
    second = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert first == second
