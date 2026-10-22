---
title: KPI and Instrumentation Plan — book-directory-scraping
created: 2026-10-22
updated: 2026-10-22
status: draft
template: architecture-docs/templates/sdlc/kpi-and-instrumentation-plan.md
---

# book-directory-scraping — KPI and Instrumentation Plan

One plan for this product. Metric definitions live here; specs and reviews link to the
KPI IDs. Honest scope: this is a manual research CLI with no scheduled collection and no
approved lake source yet, so most baselines are not measured.

## Document control

| Field | Value |
|---|---|
| Project / product ID | book-directory-scraping (catalog), repo `sales-business-directory-scraper` |
| Version | 0.1 |
| Status | draft |
| Metric owner | bookchaowalit (owner) |
| AI maker | Claude session b-data, 2026-10-22 |
| AI reviewer | not yet reviewed [ต้องยืนยัน] |
| Charter objectives | Roadmap `data-scrapers.yaml` goals dir-g1..dir-g4 (approved source, storage terms, standalone run, first Bronze landing) |
| Analytics / data source of truth | The run's own report: `data/location-research/location-analysis.json` (`collection.*`) and the CLI summary; Sentry events (opt-in, no DSN yet). No analytics tool: there are no end users |
| Dashboard | none yet [ต้องยืนยัน] |
| Next review | when D6 is decided or the Brreg collection is approved, whichever comes first |

## KPI tree

```text
OBJ-01 Trustworthy, bounded local-business evidence for research decisions
  └─ KPI-O-01 Contract-valid records per approved run
       ├─ KPI-L-01 Query failure rate per run
       ├─ KPI-L-02 Billable HTTP attempts per planned request
       └─ KPI-G-01 Contract violations (must stay 0)
OBJ-02 Directory data in the lake within the 192h SLO (after source approval)
  └─ KPI-O-02 Bronze business_listings freshness
       └─ KPI-G-02 Silent failed runs (must stay 0)
```

## KPI definitions

| KPI ID | Type | Name | Objective | Formula | Unit | Min volume | Segment | Data source and field(s) | Baseline | Target | Alert threshold | Cadence | Owner |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| KPI-O-01 | outcome | Contract-valid records per run | OBJ-01 | count of `places[]` passing the `directory.v1` required/identity checks | records | 1 run | per source (`fixture`, `google_places_new`, later `brreg_enheter`) | report JSON `places[]`; `tests/test_directory_contract.py` rules | fixture: 5 unique places from 21 planned requests (default categories, radii 500/1000/3000; 2026-10-22, offline); live: not yet measured | Brreg first approved run: <= 100 records, all valid [ต้องยืนยัน] | 0 valid records on a non-dry run | per run | owner |
| KPI-L-01 | leading | Query failure rate | OBJ-01 | `len(collection.errors) / collection.request_count` | % | >= 5 planned requests | per source | report JSON `collection.errors`, `collection.request_count`; Sentry event level | not yet measured (no live runs recorded) | < 5% [ต้องยืนยัน] | any run = 100% (exit 1, Sentry `error`) | per run | owner |
| KPI-L-02 | leading | Billable attempts per planned request | OBJ-01 | `collection.attempt_count / collection.request_count` | ratio | >= 5 planned requests | `google_places_new` only | report JSON `collection.attempt_count` | not yet measured | <= 1.2 [ต้องยืนยัน] | > 2.0 on a run | per run | owner |
| KPI-G-01 | guardrail | Contract violations | OBJ-01 | records missing a `quality.required` field or with a duplicate `source|place_id` | count | n/a | all | CI: `tests/test_directory_contract.py` | 0 (2026-10-22, CI) | must stay 0 | any > 0 fails CI | every push | owner |
| KPI-O-02 | outcome | Bronze `business_listings` freshness | OBJ-02 | now − newest Bronze manifest `collected_at` | hours | n/a | per source | parent control plane coverage report (`task scraping:coverage`) | not applicable: no approved source, no landing yet | <= 192h (contract SLO) once collection is approved | > 192h | daily | owner |
| KPI-G-02 | guardrail | Silent failed runs | OBJ-02 | runs with `errors > 0` that produced no Sentry event | count | n/a | all | Sentry vs report files | not measurable until a DSN is set [ต้องยืนยัน] | must stay 0 | any > 0 | weekly | owner |

## Event and data specification

| Event / field | Trigger | Properties | Personal data? | Emitted by | Requirement | Status |
|---|---|---|---|---|---|---|
| `collection.request_count` / `attempt_count` / `errors` / `status` | every non-dry run | counts, per-query status | no | `collect_places` → report JSON | SPEC-001 AC-01 | implemented |
| Sentry message "location analysis (source): N of M queries failed" | a run with >= 1 failed query | level `warning`/`error`, tag `component=location-analysis` | no (counts only, `send_default_pii=False`) | `location_intelligence/observability.py` | SPEC-001 AC-02/AC-03 | implemented, not live (no DSN) |
| CLI exit code 1 | every planned query failed | — | no | `scripts/run_location_analysis.py` | SPEC-001 AC-03 | implemented |
| Bronze `business_listings` manifest | approved capture replayed by the control plane | `collected_at`, checksum, row count | business names/addresses may identify people (privacy review pending) | parent control plane | roadmap dir-t5 | planned |

Privacy: place rows hold business names, addresses and map links. Nothing from a row is
sent to Sentry. Brreg rows exclude person identifiers, roles and contact endpoints per the
2026-10-15 terms decision; a minimisation review is still open.

## Dashboards and alerts

| Dashboard / alert | KPIs | Audience | Location | Refresh | Alert channel | Status |
|---|---|---|---|---|---|---|
| Sentry issue stream for this project | KPI-L-01, KPI-G-02 | owner | Sentry (project not created) | live | Sentry email [ต้องยืนยัน] | planned |
| Coverage report (parent control plane) | KPI-O-02 | owner | `task scraping:coverage` | daily | — | planned after first landing |

## Instrumentation verification (before G10)

| # | Check | Evidence | Result |
|---|---|---|---|
| 1 | Each failed-query run sends one event | `tests/test_observability.py` (fake SDK) | pass (offline) |
| 2 | Counts reconcile with the report | report JSON `collection.*` vs the event message | pass (offline test) |
| 3 | No PII in events | event holds source + counts only; test asserts provider text is absent | pass |
| 4 | Dashboard renders KPIs | — | not started |
| 5 | Alert reaches the owner | needs a Sentry project and DSN (owner action) | not started |
| 6 | Baselines captured | live baselines need an approved run | waived until collection approval |
| 7 | Consent | not applicable: no end users or tracking | n/a |

## Change history of definitions

| Date | KPI ID | Change | Reason | Baseline restated? | Approved by |
|---|---|---|---|---|---|
| 2026-10-22 | all | first draft | Big Loop L3 | n/a | pending |
