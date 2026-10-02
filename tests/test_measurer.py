"""Tests for speed_meter.measurer using a local HTTP server."""

import socket
from http.server import BaseHTTPRequestHandler
from typing import Iterator

import pytest

from speed_meter.measurer import MIB, Result, Sample, measure

from ._server import PayloadHandler, serve


class _EmptyHandler(BaseHTTPRequestHandler):
    """Returns 200 with an empty body."""

    def do_GET(self) -> None:  # noqa: N802 - http.server protocol
        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        return


_captured_user_agents: list[str] = []


class _UAHandler(PayloadHandler):
    """PayloadHandler that records the User-Agent of each request."""

    def do_GET(self) -> None:  # noqa: N802 - http.server protocol
        _captured_user_agents.append(self.headers.get("User-Agent", ""))
        super().do_GET()


@pytest.fixture
def empty_server_url() -> Iterator[str]:
    yield from serve(_EmptyHandler)


@pytest.fixture
def ua_server_url() -> Iterator[str]:
    _captured_user_agents.clear()
    yield from serve(_UAHandler)


def test_measure_returns_expected_sample_count(server_url: str) -> None:
    result = measure(server_url, count=3, timeout=5.0)
    assert len(result.samples) == 3
    assert result.bytes_total == 3 * 256 * 1024
    assert result.elapsed_total > 0


def test_measure_computes_positive_speed(server_url: str) -> None:
    result = measure(server_url, count=2, timeout=5.0)
    assert result.mib_per_second > 0


def test_measure_rejects_invalid_args() -> None:
    with pytest.raises(ValueError):
        measure("http://127.0.0.1:1/", count=0, timeout=5.0)
    with pytest.raises(ValueError):
        measure("http://127.0.0.1:1/", count=1, timeout=0.0)


def test_measure_rejects_unsupported_scheme() -> None:
    with pytest.raises(ValueError):
        measure("ftp://example.com/x", count=1, timeout=1.0)
    with pytest.raises(ValueError):
        measure("not-a-url", count=1, timeout=1.0)


def test_measure_rejects_url_without_host() -> None:
    with pytest.raises(ValueError, match="host"):
        measure("http:///path", count=1, timeout=1.0)


def test_measure_rejects_invalid_port() -> None:
    with pytest.raises(ValueError, match="(?i)port"):
        measure("http://example.com:99999/x", count=1, timeout=1.0)
    with pytest.raises(ValueError):
        measure("http://example.com:0/x", count=1, timeout=1.0)


def test_measure_raises_on_network_error() -> None:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    with pytest.raises(RuntimeError):
        measure(f"http://127.0.0.1:{port}/", count=1, timeout=1.0)


def test_measure_raises_runtime_on_real_timeout() -> None:
    """Socket read timeout → RuntimeError (not uncaught TimeoutError)."""
    import threading

    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    sock.listen(1)
    port = sock.getsockname()[1]

    def accept_and_hang() -> None:
        try:
            conn, _ = sock.accept()
            # never read, never write — forces read timeout
        finally:
            pass

    threading.Thread(target=accept_and_hang, daemon=True).start()
    try:
        with pytest.raises(RuntimeError):
            measure(f"http://127.0.0.1:{port}/", count=1, timeout=0.5)
    finally:
        sock.close()


def test_measure_raises_on_zero_bytes(empty_server_url: str) -> None:
    with pytest.raises(RuntimeError, match="0 bytes"):
        measure(empty_server_url, count=1, timeout=5.0)


def test_measure_sends_user_agent(ua_server_url: str) -> None:
    measure(ua_server_url, count=1, timeout=5.0)
    assert len(_captured_user_agents) == 1
    assert _captured_user_agents[0].startswith("speed-meter/")


def test_result_zero_elapsed_raises() -> None:
    result = Result(url="x", samples=(Sample(bytes_received=1024, elapsed_seconds=0.0),))
    with pytest.raises(ValueError):
        _ = result.mib_per_second


def test_result_aggregates_multi_sample() -> None:
    result = Result(
        url="http://example.com/x",
        samples=(
            Sample(bytes_received=MIB, elapsed_seconds=1.0),
            Sample(bytes_received=2 * MIB, elapsed_seconds=3.0),
        ),
    )
    assert result.bytes_total == 3145728
    assert result.bytes_total_mib == pytest.approx(result.bytes_total / MIB, abs=1e-9)
    assert result.elapsed_total == 4.0
    assert result.mib_per_second == pytest.approx((result.bytes_total / MIB) / 4.0)
