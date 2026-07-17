#!/usr/bin/env python3
"""Tests for common.py invariants + test-suite determinism."""
from __future__ import annotations

import os
import subprocess
import sys

from common import DATE_KIND_LABELS, DATE_KIND_TO_YMD, DATE_KINDS


def test_date_kinds_matches_labels():
    assert set(DATE_KINDS) == set(DATE_KIND_LABELS)


def test_to_ymd_covers_every_date_kind_except_year():
    # ``year`` is special-cased in generate_from; every other date kind must
    # have a random_ymd key, else generate_from silently falls through to
    # emitting the raw title.
    assert set(DATE_KIND_TO_YMD) == set(DATE_KINDS) - {"year"}


def test_to_ymd_keys_exist_in_random_ymd():
    from test_generation import random_ymd

    sample = random_ymd(2010)
    for key in DATE_KIND_TO_YMD.values():
        assert key in sample, key


def _stable_hash_under_seed(seed_value: str) -> str:
    env = dict(os.environ, PYTHONHASHSEED=seed_value)
    code = "from test_generation import stable_hash; print(stable_hash('IMG XXXX'))"
    out = subprocess.check_output([sys.executable, "-c", code], env=env, text=True)
    return out.strip()


def test_stable_hash_is_reproducible_across_processes():
    # The whole point of stable_hash: independent of PYTHONHASHSEED salting.
    assert _stable_hash_under_seed("0") == _stable_hash_under_seed("12345")
