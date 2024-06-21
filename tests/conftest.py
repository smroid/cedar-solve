from pathlib import Path

import pytest

_TEST_DIR = Path(__file__).parent


def lib_root_dir() -> Path:
    """ fetch the library package root directory """
    return (_TEST_DIR / "../tetra3").resolve()


@pytest.fixture
def test_data_dir() -> Path:
    """ fetch the tests/data directory"""
    return _TEST_DIR / "data"
