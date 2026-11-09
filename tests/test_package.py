"""Basic tests for the prokopton.core package."""

from importlib.metadata import version

import prokopton.core


def test_version_matches_package_metadata() -> None:
    assert prokopton.core.__version__ == version("prokopton")
