"""Offline check of the place records against the directory.v1 draft contract.

The contract lives in the private architecture-docs repository
(``systems/architecture/scraping-contracts/directory.v1.yaml``, status ``draft``,
collection approval pending), which CI cannot read, so the field lists below are a
copy taken on 2026-10-22. If the contract changes, update this copy in the same
change that adapts the code.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from location_intelligence.models import DEFAULT_CATEGORIES
from location_intelligence.providers import FixtureProvider, collect_places

FIXTURE = ROOT / "fixtures" / "bangkapi_sample.json"

# directory.v1 record_fields, in contract order.
RECORD_FIELDS = [
    "place_id",
    "name",
    "category",
    "matched_categories",
    "types",
    "primary_type",
    "formatted_address",
    "lat",
    "lng",
    "distance_m",
    "matched_radii_m",
    "rating",
    "user_rating_count",
    "price_level",
    "business_status",
    "delivery",
    "takeout",
    "opening_hours",
    "closing_hour",
    "website_uri",
    "google_maps_uri",
    "source",
    "collected_at",
    "expires_at",
    "evidence_id",
    "data_status",
]
# directory.v1 quality.required
REQUIRED = ["place_id", "name", "source", "collected_at", "evidence_id", "data_status"]


def _records() -> list[dict]:
    collection = collect_places(
        FixtureProvider(FIXTURE),
        center_lat=13.7652,
        center_lng=100.6431,
        radii_m=[500, 1000, 3000],
        categories=DEFAULT_CATEGORIES,
        max_requests=25,
        collected_at="2026-10-22T00:00:00Z",
    )
    assert collection["errors"] == []
    return collection["records"]


def test_records_carry_exactly_the_contract_fields():
    records = _records()
    assert records
    for row in records:
        assert list(row) == RECORD_FIELDS


def test_required_fields_are_present_and_non_empty():
    for row in _records():
        for field in REQUIRED:
            assert row[field] not in (None, ""), field


def test_identity_source_and_place_id_is_unique_per_run():
    # identity.fields = [source, place_id]; the collector merges duplicates
    # from overlapping radii/categories into one observation.
    keys = [f"{row['source']}|{row['place_id']}" for row in _records()]
    assert len(keys) == len(set(keys))


def test_timestamps_are_utc_iso_and_expiry_follows_collection():
    for row in _records():
        assert row["collected_at"].endswith("Z")
        assert row["expires_at"] > row["collected_at"]
