from pathlib import Path
from unittest import mock

import pytest

# TODO: fails w/ ModuleNotFoundError due to improper import paths in generated grpc code.
# from tetra3 import cedar_detect_client


@pytest.mark.skip("skip until import issues fixed")
def test_cedar_detect_client_bad_path():
    with pytest.raises(ValueError):
        cedar_detect_client.CedarDetectClient("not/a/valid/path")


@pytest.mark.skip("skip until import issues fixed")
@mock.patch("tetra3.cedar_detect_client._bin_dir", Path("not/a/valid/path"))
def test_cedar_detect_client_auto_detect_error():
    with pytest.raises(ValueError):
        cedar_detect_client.CedarDetectClient()  # autodetect exe path
