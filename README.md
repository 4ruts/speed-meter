# speed-meter

Sequential HTTP download speed meter for the terminal. Stdlib only.

## Run it

```bash
python -m speed_meter https://proof.ovh.net/files/100Mb.dat
```

Example output:

```
Target:    https://proof.ovh.net/files/100Mb.dat
Requests:  10 (sequential)
Total:     100.00 MiB in 4.00 s
Average:   25.00 MiB/s
```

Requires Python 3.10+.

## CLI

```bash
python -m speed_meter <url> [flags]
python -m speed_meter --list-test-urls
```

| Flag               | Default | Meaning                          |
|--------------------|---------|----------------------------------|
| `url`              | —       | Target URL (positional)          |
| `-n`, `--requests` | `10`    | Number of sequential requests    |
| `-t`, `--timeout`  | `30.0`  | Per-request timeout (seconds)    |
| `--list-test-urls` | —       | Print curated test URLs, exit    |
| `--version`        | —       | Print version, exit              |

## Library

```python
from speed_meter import measure, Result, Sample, MIB

result: Result = measure("https://proof.ovh.net/files/100Mb.dat", count=3)
print(f"{result.mib_per_second:.2f} MiB/s")
```

Public API: `measure`, `Result`, `Sample`, `MIB`, `__version__`.

## How it works

Sequential `urllib.request.urlopen` GETs, `count` times, each timed with
`time.perf_counter()`. Total bytes divided by total elapsed time.
Speed is reported in **MiB/s** (1 MiB = 1 048 576 B).

URLs are validated (scheme, host, port) before any network I/O.
Invalid URLs raise `ValueError`; network failures raise `RuntimeError`.

## Exit codes

| Code | Meaning           |
|------|-------------------|
| 0    | Success           |
| 1    | Network error     |
| 2    | Invalid arguments |
| 130  | Interrupted       |

## Test URLs

Static, cacheable, large. `--list-test-urls` prints them:

```
https://proof.ovh.net/files/100Mb.dat
https://proof.ovh.net/files/1Gb.dat
https://cachefly.cachefly.net/100mb.test
```

## Development

```bash
pip install pytest
pytest
```

Tests use a local `http.server` fixture — no network needed.

