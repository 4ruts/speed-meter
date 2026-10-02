"""HTTP download speed measurement."""

import time
import urllib.error
from dataclasses import dataclass
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from . import __version__

MIB = 1024 * 1024


@dataclass(frozen=True)
class Sample:
    bytes_received: int
    elapsed_seconds: float


@dataclass(frozen=True)
class Result:
    url: str
    samples: tuple[Sample, ...]

    @property
    def bytes_total(self) -> int:
        return sum(s.bytes_received for s in self.samples)

    @property
    def bytes_total_mib(self) -> float:
        return self.bytes_total / MIB

    @property
    def elapsed_total(self) -> float:
        return sum(s.elapsed_seconds for s in self.samples)

    @property
    def mib_per_second(self) -> float:
        elapsed = self.elapsed_total
        if elapsed <= 0:
            raise ValueError("elapsed_total must be > 0 to compute speed")
        return (self.bytes_total / MIB) / elapsed


def _download_once(url: str, timeout: float) -> Sample:
    start = time.perf_counter()
    try:
        req = Request(url, headers={"User-Agent": f"speed-meter/{__version__}"})
        with urlopen(req, timeout=timeout) as resp:
            bytes_received = 0
            while chunk := resp.read(64 * 1024):
                bytes_received += len(chunk)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"network error: {exc}") from exc

    elapsed = time.perf_counter() - start
    if bytes_received <= 0:
        raise RuntimeError(f"server returned 0 bytes for {url}")
    return Sample(bytes_received=bytes_received, elapsed_seconds=elapsed)


def measure(url: str, count: int = 10, timeout: float = 30.0) -> Result:
    if count < 1:
        raise ValueError("requests must be >= 1")
    if timeout <= 0:
        raise ValueError("timeout must be > 0")

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"unsupported URL scheme: {parsed.scheme!r} (use http or https)")
    if not parsed.hostname:
        raise ValueError("URL has no host")
    if parsed.port is not None and not 1 <= parsed.port <= 65535:
        raise ValueError(f"invalid port: {parsed.port}")

    samples = tuple(_download_once(url, timeout) for _ in range(count))
    return Result(url=url, samples=samples)
