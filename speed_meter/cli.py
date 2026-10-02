"""Command-line interface for speed-meter."""

import argparse
import http.client
import sys

from . import __version__
from .measurer import Result, measure

_EXIT_OK = 0
_EXIT_NETWORK = 1
_EXIT_USAGE = 2

_TEST_URLS: tuple[str, ...] = (
    "https://proof.ovh.net/files/100Mb.dat",
    "https://proof.ovh.net/files/1Gb.dat",
    "https://cachefly.cachefly.net/100mb.test",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Measure HTTP download speed via sequential GETs.",
    )
    parser.add_argument(
        "url",
        nargs="?",
        help="URL of a heavy resource to download (e.g. large image, ISO).",
    )
    parser.add_argument(
        "--list-test-urls",
        action="store_true",
        help="print curated public test URLs and exit",
    )
    parser.add_argument(
        "-n", "--requests",
        type=int,
        default=10,
        help="number of sequential requests (default: 10)",
    )
    parser.add_argument(
        "-t", "--timeout",
        type=float,
        default=30.0,
        help="per-request timeout in seconds (default: 30)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def format_output(result: Result) -> str:
    total = result.elapsed_total
    speed = result.mib_per_second
    return (
        f"Target:    {result.url}\n"
        f"Requests:  {len(result.samples)} (sequential)\n"
        f"Total:     {result.bytes_total_mib:.2f} MiB in {total:.2f} s\n"
        f"Average:   {speed:.2f} MiB/s"
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_test_urls:
        for u in _TEST_URLS:
            print(u)
        return _EXIT_OK

    if args.url is None:
        parser.error("the following arguments are required: url")

    try:
        result = measure(args.url, count=args.requests, timeout=args.timeout)
    except UnicodeError:
        print("error: invalid URL encoding", file=sys.stderr)
        return _EXIT_USAGE
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return _EXIT_USAGE
    except http.client.HTTPException as exc:
        print(f"error: {exc}", file=sys.stderr)
        return _EXIT_NETWORK
    except RuntimeError as exc:
        print(f"network error: {exc}", file=sys.stderr)
        return _EXIT_NETWORK
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130

    print(format_output(result))
    return _EXIT_OK
