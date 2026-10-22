"""Transient connection failures that urllib does not wrap in URLError.

``urlopen`` only wraps errors raised while *sending* the request. A server that
drops the connection before or while answering raises ``RemoteDisconnected`` /
``ConnectionResetError`` (both ``OSError``) or ``http.client.IncompleteRead``
straight through. They are as transient as a 503, so they must be retried and,
when retries run out, surface as ``ProviderError`` so ``collect_places`` records a
per-query error instead of aborting the whole run.
"""

from __future__ import annotations

import http.client
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from location_intelligence.models import CandidateCategory, SearchRequest
from location_intelligence.providers import (
    GooglePlacesProvider,
    ProviderError,
    collect_places,
)

COFFEE = CandidateCategory("coffee", ("cafe",), ("coffee",))
REQUEST = SearchRequest(13.7652, 100.6431, 1000, COFFEE)


class _Response:
    def __init__(self, body: bytes):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.body


TRANSIENT = [
    http.client.RemoteDisconnected("Remote end closed connection without response"),
    ConnectionResetError(104, "Connection reset by peer"),
    http.client.IncompleteRead(b"{", 10),
]


@pytest.mark.parametrize("error", TRANSIENT, ids=lambda e: type(e).__name__)
def test_transient_connection_error_is_retried(error):
    sleeps: list[float] = []
    provider = GooglePlacesProvider("key", sleep=sleeps.append)
    effects = [error, _Response(b'{"places": [{"id": "a"}]}')]
    with patch("location_intelligence.providers.urlopen", side_effect=effects) as mocked:
        rows = provider.search(REQUEST)
    assert rows == [{"id": "a"}]
    assert mocked.call_count == 2
    assert sleeps == [1.0]
    assert provider.last_attempts == 2


@pytest.mark.parametrize("error", TRANSIENT, ids=lambda e: type(e).__name__)
def test_exhausted_transient_error_becomes_a_partial_collection(error):
    provider = GooglePlacesProvider("key", sleep=lambda _s: None)
    with patch("location_intelligence.providers.urlopen", side_effect=error):
        with pytest.raises(ProviderError):
            provider.search(REQUEST)
        collection = collect_places(
            provider,
            center_lat=13.7652,
            center_lng=100.6431,
            radii_m=[1000],
            categories=(COFFEE,),
            collected_at="2026-10-22T00:00:00Z",
        )
    assert collection["status"] == "partial"
    assert collection["attempt_count"] == 3
    assert len(collection["errors"]) == 1
