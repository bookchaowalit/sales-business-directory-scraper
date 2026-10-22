# book-directory-scraping

**Tier:** B (catalog label; Big Loop target L3)  
**Owner path:** `bookchaowalit/book-apps/tools/book-directory-scraping`

## Purpose

Bounded local business discovery (saved fixtures, or Google Places on explicit opt-in)
and location opportunity analysis for local research. No scheduled collection; see
`PRODUCT.md` "Runtime status".

## Automated location opportunity analysis

The `location_intelligence` module turns a center point into a bounded,
evidence-aware comparison of local business categories. It supports a local
synthetic/JSON fixture first, then an explicit Google Places API (New) mode.
The output is a JSON contract plus a Markdown report with query coverage,
expiry, evidence IDs, and a scorecard. Missing demand evidence stays explicit;
the score is a prioritization aid and is not a sales forecast.

Run the deterministic demo from this repository root:

```bash
python3 scripts/run_location_analysis.py \
  --input fixtures/bangkapi_sample.json \
  --radii 500,1000,3000 \
  --analysis-radius 1000 \
  --categories coffee,laundry,cleaning,beauty,pet
```

It writes `data/location-research/location-analysis.json` and
`data/location-research/location-analysis.md` (the directory is ignored by
Git). The default 25-request guard prevents an accidental unbounded run. Use
`--dry-run` to inspect the request plan without collecting rows.

To call Google Places (New), set `GOOGLE_MAPS_API_KEY` in the process
environment and opt in explicitly:

```bash
GOOGLE_MAPS_API_KEY='…' python3 scripts/run_location_analysis.py \
  --live --lat 13.7652 --lng 100.6431 \
  --radii 500,1000 --categories coffee,laundry \
  --max-requests 10
```

The client requests only the fields needed for the first scorecard and caps
each Nearby Search at 20 results. It never logs the key or raw provider error
body (the key is also hidden from the provider's `repr`). HTTP 429/5xx,
network errors and timeouts are retried at most twice more with 1 s / 2 s
backoff; other 4xx errors fail immediately. `--max-requests` bounds the query
plan, so the worst case is `3 x max-requests` billable calls. Each query's HTTP
attempts are recorded in `collection.query_results[].attempts`, with the total
in `collection.attempt_count` and the Markdown report, so retries stay visible
in cost reviews. Reports are written atomically (temp file + `os.replace`), so
an interrupted run never leaves a half-written JSON/Markdown file. `--lat`/`--lng`
must be given together and within range; `--budget-thb`/`--hours-per-week`
cannot be negative. Review Google Maps attribution, caching, and service terms before using
the live output in a customer-facing product.

The `cleaning` candidate uses Google's broad `service` type because the current
type table has no dedicated cleaning-service filter. Treat that category as a
discovery proxy and add a keyword/Text Search or manual verification step before
using it for a decision.

Run the offline checks (no network; the Google client is mocked) with
[uv](https://docs.astral.sh/uv/) and the committed `uv.lock`:

```bash
uv sync --frozen --all-extras      # dev tools (pytest, ruff, mypy) + optional sentry extra
uv run ruff check . && uv run ruff format --check .
uv run mypy .                      # gradual config in pyproject.toml
uv run pytest -q --cov             # CI gate: total coverage >= 93%
```

CI (`.github/workflows/ci.yml`, shared `platform-ci-workflows` v1.1.1) runs the same
lint, format, type check and tests on Python 3.10 and 3.13, then a `--dry-run` plan.

Error reporting is opt-in: with the `sentry` extra installed and `SENTRY_DSN` set, a
run in which queries failed sends one Sentry event with counts only
(`SENTRY_ENVIRONMENT` sets the environment). A run in which every query failed exits 1.

## Entry points

- `scripts/run_location_analysis.py` — location opportunity analysis (active, stdlib-only).

The former `directories/yellow_pages_scraper.py` prototype was removed in the
2026-09 upgrade pass: it imported the retired monorepo `adapters`/`core`
packages, never ran from a standalone checkout, used unverified selectors, and
would have bulk-collected business phone numbers. Business discovery is served
by the Google Places / fixture providers in `location_intelligence/`. Recover
it from Git history if a directory source is ever needed again, and add a
privacy note before porting.

## Stack

Python 3.10+ standard library (`pyproject.toml` has no runtime dependencies; dev tools
and the optional `sentry` extra are pinned in `uv.lock`).

## Boundaries

- **Not** a lake-first data product. Durable market datasets live under `book-*-data` repos.
- **Not** coupled to Solo Empire monorepo runtime. Nested Git repo; commit only inside this tree.
- Never commit `.env`, cookies, session dumps, or scraped PII dumps to Git.

## Source terms decision (2026-10-15)

**Brreg Enhetsregisteret accepted as a Norway-only pilot (owner decision
2026-10-15, BOO-131).** The Brønnøysund Register Centre publishes organisation
data under [NLOD 2.0](https://data.norge.no/nlod/en/2.0). The coverage registry
now lists source `brreg_enheter` (status `planned`) with these limits:

- Norway only. **Not** a Bangkok or Thai replacement; the Bangkok inventory gap stays open.
- Attribution: "Contains data under NLOD 2.0 from Brønnøysundregistrene", with
  source/licence links and normalisation changes marked.
- Limited-company (AS/ASA) organisation metadata only. No person identifiers,
  roles, sole-proprietor personal details or contact endpoints.
- Capture path `data/exported/brreg_business_listings.jsonl`, 24h cadence, 48h
  max age (an operational target, not a licence term or SLA), ≤100 records on
  the first approved run.

**Caveats:** register rows are legal entities, not physical venues or demand
evidence, and a privacy/minimisation review is still required because company
names and addresses can identify people.

**Not done yet:** no Brreg adapter exists in this repository, and no API request,
download or collection has been made or approved. Building a bounded,
offline-tested adapter and getting collection approval is a separate follow-up.
Record: architecture-docs `systems/ai-data/source-terms-decisions-2026-10-15.md` (private repository).
Sources: [Brreg datasets and API](https://www.brreg.no/en/use-of-data-from-the-bronnoysund-register-centre/datasets-and-api/),
[API documentation](https://data.brreg.no/enhetsregisteret/api/dokumentasjon/en/index.html).

## Limitations (honest)

Not a production data product. No lake-first contract. Respect site ToS and robots rules; personal research use only.

## Related

- Active collection product: `book-job-scraping` (Tier A tool)
- Lake products: `book-crypto-data`, `book-fx-data`, `book-stock-data`, …
- Solo Empire catalog: `repository-catalog/BOOK-DEV-BACKLOG-BD.md` (BD-012)
