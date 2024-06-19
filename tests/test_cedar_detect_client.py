from pathlib import Path
from unittest import mock

import pytest

# TODO: fails w/ ModuleNotFoundError due to improper import paths in generated grpc code.
# from tetra3 import cedar_detect_client


@pytest.mark.skip("skip until import issues fixed")
def test_cedar_detect_client_bad_path():
    """ if the client is created with a bad path to the server binary it should raise an error """
    with pytest.raises(ValueError):
        cedar_detect_client.CedarDetectClient("not/a/valid/path")


@pytest.mark.skip("skip until import issues fixed")
@mock.patch("tetra3.cedar_detect_client._bin_dir", Path("not/a/valid/path"))
def test_cedar_detect_client_auto_detect_error():
    """
    if the client is created with no path but auto-detection failed to find the binary it should
    raise an error.

    Note: the internal reference to the `bin/` directory is mocked to an invalid path so that this
    test will execute properly in a developers local environment regardless of if they did have
    the `cedar-detect-server` binary available.
    """
    with pytest.raises(ValueError):
        cedar_detect_client.CedarDetectClient()  # autodetect exe path
