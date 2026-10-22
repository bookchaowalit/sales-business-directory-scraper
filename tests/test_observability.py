"""Failed queries in a location run must not stay silent (opt-in Sentry).

``collect_places`` catches every ``ProviderError`` and keeps going, so a run in
which some or all Google Places queries failed still printed a summary and exited
0. With ``SENTRY_DSN`` set, such a run sends one Sentry event (no payloads, no
place data, no API key); a run in which every query failed also exits 1.
A fake ``sentry_sdk`` module stands in for the SDK, so nothing leaves the process.
"""

from __future__ import annotations

import io
import sys
import types
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from location_intelligence.providers import FixtureProvider, ProviderError
from scripts.run_location_analysis import main as location_main

FIXTURE = ROOT / "fixtures" / "bangkapi_sample.json"
SECRET = "test-secret-key-123"


class FakeSentry(types.ModuleType):
    def __init__(self) -> None:
        super().__init__("sentry_sdk")
        self.init_kwargs: dict[str, Any] | None = None
        self.messages: list[tuple[str, str]] = []
        self.tags: dict[str, str] = {}
        self.flushed = 0

    def init(self, **kwargs: Any) -> None:
        self.init_kwargs = kwargs

    def set_tag(self, key: str, value: str) -> None:
        self.tags[key] = value

    def capture_message(self, message: str, level: str = "info") -> None:
        self.messages.append((level, message))

    def flush(self, timeout: float | None = None) -> None:
        self.flushed += 1


@pytest.fixture
def fake_sentry(monkeypatch):
    sdk = FakeSentry()
    monkeypatch.setitem(sys.modules, "sentry_sdk", sdk)
    monkeypatch.setenv("SENTRY_DSN", "https://public@example.invalid/1")
    monkeypatch.setenv("SENTRY_ENVIRONMENT", "test")
    return sdk


def _run(tmp_path: Path, *extra: str) -> int:
    with redirect_stdout(io.StringIO()):
        return location_main(
            [
                "--input",
                str(FIXTURE),
                "--radii",
                "500,1000",
                "--analysis-radius",
                "1000",
                "--categories",
                "coffee,laundry",
                "--output-dir",
                str(tmp_path / "out"),
                *extra,
            ]
        )


def _fail_laundry(self, request):
    if request.category.name == "laundry":
        raise ProviderError(f"Google Places request failed with HTTP 503 {SECRET}")
    return _ORIGINAL_SEARCH(self, request)


_ORIGINAL_SEARCH = FixtureProvider.search


def test_partial_run_reaches_sentry(fake_sentry, tmp_path):
    with patch.object(FixtureProvider, "search", _fail_laundry):
        code = _run(tmp_path)
    assert code == 0
    assert fake_sentry.init_kwargs is not None
    assert fake_sentry.init_kwargs["send_default_pii"] is False
    assert fake_sentry.init_kwargs["traces_sample_rate"] == 0.0
    assert fake_sentry.init_kwargs["environment"] == "test"
    assert len(fake_sentry.messages) == 1
    level, message = fake_sentry.messages[0]
    assert level == "warning"
    assert "2 of 4" in message
    assert SECRET not in message
    assert fake_sentry.flushed == 1


def test_run_where_every_query_failed_is_an_error_and_exits_1(fake_sentry, tmp_path):
    def fail_all(self, request):
        raise ProviderError("Google Places request failed with HTTP 503")

    with patch.object(FixtureProvider, "search", fail_all):
        code = _run(tmp_path)
    assert code == 1
    assert [level for level, _ in fake_sentry.messages] == ["error"]
    assert "4 of 4" in fake_sentry.messages[0][1]
    # The report is still written so the operator can see which queries failed.
    assert (tmp_path / "out" / "location-analysis.json").exists()


def test_clean_run_sends_nothing(fake_sentry, tmp_path):
    assert _run(tmp_path) == 0
    assert fake_sentry.messages == []


def test_without_dsn_sentry_is_never_initialised(fake_sentry, monkeypatch, tmp_path):
    monkeypatch.delenv("SENTRY_DSN")
    with patch.object(FixtureProvider, "search", _fail_laundry):
        assert _run(tmp_path) == 0
    assert fake_sentry.init_kwargs is None
    assert fake_sentry.messages == []


def test_dry_run_never_initialises_sentry(fake_sentry, tmp_path):
    assert _run(tmp_path, "--dry-run") == 0
    assert fake_sentry.init_kwargs is None


def test_init_disables_locals_and_request_bodies(fake_sentry, tmp_path):
    # After init, Sentry's default excepthook would ship an uncaught crash with frame
    # locals (which can hold the API key or response bodies) unless turned off.
    with patch.object(FixtureProvider, "search", _fail_laundry):
        _run(tmp_path)
    kwargs = fake_sentry.init_kwargs
    assert kwargs is not None
    assert kwargs["include_local_variables"] is False
    assert kwargs["max_request_body_size"] == "never"
    assert callable(kwargs["before_send"])


def test_before_send_strips_frame_vars_request_and_messages(fake_sentry, tmp_path):
    _run(tmp_path, "--max-requests", "25")
    assert fake_sentry.init_kwargs is not None
    before_send = fake_sentry.init_kwargs["before_send"]
    event = {
        "request": {"url": "https://places.example/?key=abc", "data": "body"},
        "breadcrumbs": {"values": [{"message": f"POST with {SECRET}"}]},
        "extra": {"payload": "body"},
        "exception": {
            "values": [
                {
                    "type": "ProviderError",
                    "value": f"failed {SECRET}",
                    "stacktrace": {
                        "frames": [{"function": "search", "vars": {"api_key": SECRET}}]
                    },
                }
            ]
        },
        "threads": {"values": [{"stacktrace": {"frames": [{"vars": {"raw": "x"}}]}}]},
    }
    cleaned = before_send(event, {})
    assert not {"request", "breadcrumbs", "extra"} & set(cleaned)
    value = cleaned["exception"]["values"][0]
    assert value["type"] == "ProviderError"
    assert value["value"] == ""
    assert "vars" not in value["stacktrace"]["frames"][0]
    assert "vars" not in cleaned["threads"]["values"][0]["stacktrace"]["frames"][0]
    assert SECRET not in repr(cleaned)
