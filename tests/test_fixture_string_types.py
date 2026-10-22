"""FixtureProvider must read ``types`` the same way normalization does.

``models._types`` accepts a comma/pipe separated string (CSV exports) and the
``categories`` alias, but ``FixtureProvider.search`` iterated the raw value, so a
string ``"pet_store"`` became the characters ``{"p", "e", ...}`` and the row was
never returned for the pet query: replaying a CSV-shaped capture silently lost rows.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from location_intelligence.models import CandidateCategory, SearchRequest
from location_intelligence.providers import FixtureProvider

PET = CandidateCategory("pet", ("pet_store", "pet_care"), ("pet",))
REQUEST = SearchRequest(13.7652, 100.6431, 1000, PET)


def _provider(tmp_path: Path, row: dict) -> FixtureProvider:
    path = tmp_path / "capture.json"
    path.write_text(json.dumps([row]), encoding="utf-8")
    return FixtureProvider(path)


BASE = {"id": "p1", "name": "Happy Paws", "lat": 13.7655, "lng": 100.6433}


def test_string_types_match_the_category(tmp_path):
    provider = _provider(tmp_path, {**BASE, "types": "veterinary_care|pet_store"})
    assert [row["id"] for row in provider.search(REQUEST)] == ["p1"]


def test_categories_alias_matches_the_category(tmp_path):
    provider = _provider(tmp_path, {**BASE, "categories": ["pet_care"]})
    assert [row["id"] for row in provider.search(REQUEST)] == ["p1"]


def test_unrelated_string_types_do_not_match(tmp_path):
    provider = _provider(tmp_path, {**BASE, "types": "laundry"})
    assert provider.search(REQUEST) == []
