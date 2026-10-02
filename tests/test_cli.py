"""Tests for speed_meter.cli."""

import pytest

from speed_meter import __version__
from speed_meter.cli import build_parser, format_output, main
from speed_meter.measurer import MIB, Result, Sample


def test_build_parser_defaults() -> None:
    args = build_parser().parse_args(["http://x/"])
    assert args.requests == 10
    assert args.timeout == 30.0
    assert args.url == "http://x/"


def test_build_parser_custom_args() -> None:
    args = build_parser().parse_args(["-n", "3", "-t", "5.5", "http://x/"])
    assert args.requests == 3
    assert args.timeout == 5.5
    assert args.url == "http://x/"


def test_version_flag_exits(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        build_parser().parse_args(["--version"])
    captured = capsys.readouterr()
    assert __version__ in captured.out


def test_format_output_shape() -> None:
    result = Result(
        url="http://example.com/x",
        samples=(
            Sample(bytes_received=MIB, elapsed_seconds=1.0),
            Sample(bytes_received=2 * MIB, elapsed_seconds=3.0),
        ),
    )
    out = format_output(result)
    assert "http://example.com/x" in out
    assert "Requests:  2" in out
    assert "MiB/s" in out
    assert "3.00 MiB" in out


def test_main_success_exit_code(server_url: str, capsys: pytest.CaptureFixture[str]) -> None:
    assert main([server_url, "-n", "2", "-t", "5"]) == 0
    captured = capsys.readouterr()
    assert "Average:" in captured.out
    assert "MiB/s" in captured.out


def test_main_invalid_url_returns_usage_exit(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["not-a-url"]) == 2
    captured = capsys.readouterr()
    assert "error:" in captured.err


def test_main_zero_requests_returns_usage_exit() -> None:
    assert main(["-n", "0", "http://x/"]) == 2


def test_main_network_error_returns_network_exit(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["http://127.0.0.1:1/", "-n", "1", "-t", "1"]) == 1
    captured = capsys.readouterr()
    assert "network error" in captured.err


def test_main_lists_test_urls(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--list-test-urls"]) == 0
    out = capsys.readouterr().out
    assert "proof.ovh.net/files/100Mb.dat" in out
    assert "proof.ovh.net/files/1Gb.dat" in out
    assert "cachefly.cachefly.net/100mb.test" in out
    assert "speed.hetzner.de" not in out  # we dropped Hetzner — DNS-broken in our env
