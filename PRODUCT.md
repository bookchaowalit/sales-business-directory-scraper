# book-directory-scraping — Product brief

**Slug:** `bookchaowalit/sales-business-directory-scraper`
**Catalog tier:** B (Big Loop target L3) · **Updated:** 2026-10-22
**Status:** working local CLI; not a lake-first data product yet (no approved collection)

## Purpose

Bounded local business discovery and location opportunity analysis: from a centre
point, a query plan of radii x categories is run against a saved fixture (default)
or, on explicit opt-in, Google Places API (New). The output is a
`location-opportunity.v1` JSON report plus a Markdown scorecard with evidence IDs,
expiry and billable-attempt counts. Scores rank what to research next; they are not
sales forecasts.

## Runtime status (verified 2026-10-22)

| What | Status |
|---|---|
| Entry point | `python scripts/run_location_analysis.py` (wrapper `scripts/run_location_analysis.sh`); fixture mode by default, `--live` needs `GOOGLE_MAPS_API_KEY`. Exit 0 = report written; exit 1 = every query failed (report still written); exit 2 = usage or plan-limit error |
| Who runs it | The owner, by hand. No cron entry, Windows task or GitHub `schedule:` exists for this repo (this WSL host's crontab has no scraper entries on 2026-10-22; Windows Task Scheduler cannot be checked from WSL [ต้องยืนยัน]) |
| Hosted deployment | None. No port, no API, no cloud job |
| Live collection | Not approved. `directory.v1` names Brreg (Norway, NLOD 2.0) as the only accepted source and `collection_approval: pending_operator_approval`; no Brreg adapter exists. Google Places mode is a manual research tool outside the lake |
| Error reporting | Sentry, opt-in: install the `sentry` extra and set `SENTRY_DSN`. A run with failed queries sends one event (`warning` if some failed, `error` if all failed) with counts only: no place data, provider text or API key. Frame locals, request bodies, breadcrumbs and exception messages are scrubbed from every event. No DSN is configured yet [ต้องยืนยัน] |
| Contract | Records match `directory.v1` `record_fields` and `quality.required` (offline test `tests/test_directory_contract.py`); the report envelope is `location-opportunity.v1` (repo-owned) |
| Quality gates in CI | ruff, ruff format, mypy (gradual; strict on `observability.py`), offline pytest with coverage >= 93%, dry-run plan smoke, on Python 3.10 and 3.13, plus the shared security scan |

## What it does not do

- No lake landing, Bronze manifest or checksum: output is two local report files under
  `data/location-research/` (Git-ignored).
- No scheduled collection and no Yellow Pages scraping (that prototype was removed in
  2026-09; see README).
- No persistence of Google Places content beyond the run's report files; the report
  carries `expires_at` (30 days) for the Google terms review.

## Limits

- Nearby Search returns at most 20 places per request: results are the places the
  plan found, not a census.
- Review counts are a demand proxy, not sales or review velocity.
- The `cleaning` category uses Google's broad `service` type (discovery proxy only).

## Docs

- Spec: `specs/001-l2-baseline/spec.md` · KPI plan: `docs/measurement/KPI-PLAN.md`
- Backlog: `docs/UPGRADE-PLAN.md` · Product card: `DOCPACK/`
