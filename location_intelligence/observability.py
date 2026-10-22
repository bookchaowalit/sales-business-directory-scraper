"""Opt-in Sentry for location analysis runs.

Off unless ``SENTRY_DSN`` is set and the ``sentry`` extra is installed.
``collect_places`` records each failed query and keeps going, so a run with
failed queries still produces a report. :func:`report_collection` turns those
failures into one Sentry event per run: ``warning`` when some queries failed,
``error`` when all of them did. Only counts are sent: no place data, no provider
error text (it could echo request details) and never the API key.
"""

from __future__ import annotations

import os
from importlib import import_module
from types import ModuleType
from typing import Any


def init_sentry(component: str) -> ModuleType | None:
    """Initialise Sentry for one run; return the SDK, or None when it is off."""
    dsn = os.environ.get("SENTRY_DSN", "").strip()
    if not dsn:
        return None
    try:
        sdk = import_module("sentry_sdk")
    except ImportError:
        return None
    sdk.init(
        dsn=dsn,
        environment=os.environ.get("SENTRY_ENVIRONMENT", "local"),
        send_default_pii=False,
        traces_sample_rate=0.0,
    )
    sdk.set_tag("component", component)
    return sdk


def collection_exit_code(collection: dict[str, Any]) -> int:
    """1 when every planned query failed (the report holds no observations), else 0."""
    planned = int(collection.get("request_count") or 0)
    failed = len(collection.get("errors") or [])
    return 1 if planned and failed >= planned else 0


def report_collection(sdk: ModuleType | None, collection: dict[str, Any]) -> None:
    """Send one event when any query failed; nothing for a clean run."""
    failed = len(collection.get("errors") or [])
    if sdk is None or failed == 0:
        return
    planned = int(collection.get("request_count") or 0)
    level = "error" if collection_exit_code(collection) else "warning"
    source = str(collection.get("source") or "unknown")
    sdk.capture_message(
        f"location analysis ({source}): {failed} of {planned} queries failed",
        level=level,
    )
    sdk.flush(timeout=5)
