"""Shared pytest fixtures."""

from typing import Iterator

import pytest

from ._server import PayloadHandler, serve


@pytest.fixture
def server_url() -> Iterator[str]:
    yield from serve(PayloadHandler)
