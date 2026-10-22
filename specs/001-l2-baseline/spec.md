---
id: SPEC-001
title: L2/L3 baseline for sales-business-directory-scraper
status: in review
created: 2026-10-22
owner: bookchaowalit
---

# SPEC-001: L2/L3 baseline

## Document control

| Field | Value |
|---|---|
| Main-only | yes (ADR-0004 v1.1: red run is local, red and green commits pushed together) |
| Maker | Claude session b-data (2026-10-22) |
| Checker / approver | pending (owner) |

## Problem

The Big Loop scorecard (2026-10-22) had this repo at L0: no lockfile, no type check,
no error reporting, no spec or KPI plan. Review of the collector found three silent
failure paths:

1. A connection dropped by Google before or during the response
   (`RemoteDisconnected`, `ConnectionResetError`, `IncompleteRead`) is not wrapped
   in `URLError` by `urlopen`, so it was neither retried nor turned into a per-query
   error: it aborted the whole run and lost every query already made (and billed).
2. `collect_places` records failed queries and continues, so a run where some or
   all queries failed printed a summary and exited 0. Nobody is told.
3. `FixtureProvider.search` iterated `types` as given, so a CSV-shaped capture with
   `"types": "a|b"` (which normalization accepts) or the `categories` alias was
   never matched: replaying such a capture silently dropped rows.

## Behaviour

1. Dependencies resolve from the committed `uv.lock`; CI installs with `uv sync --frozen --all-extras`.
2. `mypy .` runs in CI (gradual; strict on `location_intelligence/observability.py`).
3. Dropped connections and incomplete reads are retried like 429/5xx (max 3 attempts,
   1 s / 2 s backoff) and, when exhausted, become a `ProviderError` recorded per query.
4. With `SENTRY_DSN` set and the `sentry` extra installed, a run with failed queries
   sends exactly one event: `warning` when some failed, `error` when all failed. The
   message holds the source and counts only (no provider text, place data or key);
   `send_default_pii=False`, `traces_sample_rate=0.0`, environment from
   `SENTRY_ENVIRONMENT`. Without a DSN the SDK is never imported. `--dry-run` never
   initialises it.
5. A run in which every planned query failed exits 1 (the report is still written).
6. Fixture replay parses `types` with the same rules as normalization.
7. Place records carry exactly the `directory.v1` `record_fields`, with the
   `quality.required` fields non-empty and `source|place_id` unique per run.
8. CI fails when total coverage drops below 93%.

## Acceptance

| AC | Given / When / Then | Test |
|---|---|---|
| AC-01 | Given Google drops the connection once, when a query runs, then it is retried and succeeds; given it keeps dropping, then the query is a recorded error and the run is `partial` | `tests/test_transient_connection_errors.py` |
| AC-02 | Given `SENTRY_DSN` is set, when 2 of 4 queries fail, then one `warning` event "2 of 4 queries failed" is sent without the provider text, and the exit code is 0 | `tests/test_observability.py::test_partial_run_reaches_sentry` |
| AC-03 | Given `SENTRY_DSN` is set, when all 4 queries fail, then one `error` event is sent, the report is written and the exit code is 1; a clean run, a run without DSN and a dry run send nothing | `tests/test_observability.py` (other 4 tests) |
| AC-04 | Given a fixture row with `types` as a `"a|b"` string or a `categories` list, when its category is queried, then the row is returned | `tests/test_fixture_string_types.py` |
| AC-05 | Records match the `directory.v1` field list, required fields and identity | `tests/test_directory_contract.py` |
| AC-06 | CI on `main` is green on Python 3.10 and 3.13 with the coverage gate | CI run below |

## Red/green log

| AC | Red (sha · command · failure) | Green |
|---|---|---|
| AC-01 | `4d2792b` · `python -m pytest -q tests/test_transient_connection_errors.py` · `ConnectionResetError: [Errno 104] Connection reset by peer` (6 failed) | `GREEN_CI` |
| AC-02, AC-03 | `ad4ae28` · `python -m pytest -q tests/test_observability.py` · `AssertionError: assert None is not None` (init never called) and `assert 0 == 1` (exit code) | `GREEN_CI` |
| AC-04 | `c192366` · `python -m pytest -q tests/test_fixture_string_types.py` · `AssertionError: assert [] == ['p1']` | `GREEN_CI` |

## Contract findings (directory.v1, draft)

- Field list, required fields and identity match the code (AC-05).
- `directory.v1` names Brreg Enhetsregisteret (Norway, NLOD 2.0) as the only permitted
  source and keeps collection `pending_operator_approval`; its `allowed_inputs` is only
  `fixtures/bangkapi_sample.json`. This repo has no Brreg adapter, and its live mode is
  Google Places, which the contract does not list. Google Places output must therefore
  stay out of the lake (the report's 30-day `expires_at` follows Google's caching terms).
- The lake-first path (exact landing bytes + checksum, Bronze `business_listings`
  manifest) is not implemented here; the contract's `storage.landing` is
  `exact_capture_bytes_after_approval`, so it waits on the collection approval.

## Schedule (planned replacement, D6)

No change made. Today nothing schedules this repo: it is a manual CLI (no cron entry,
no `setup_cron.sh`, no Windows task script, no GitHub `schedule:`). Planned once owner
decision D6 picks the host for scheduled jobs and the Brreg collection is approved: one
hosted daily job (24h cadence, 48h max age per the 2026-10-15 terms decision) that runs
a bounded Brreg capture (<= 100 records on the first run) with `SENTRY_DSN` set, landing
exact bytes for the parent control plane to replay into Bronze `business_listings`.
Google Places runs stay manual.

## Out of scope

Live captures, a Brreg adapter, lake writes to R2, changes to `directory.v1`, and the
P1/P2 items in `docs/UPGRADE-PLAN.md`.
