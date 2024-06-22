import tempfile
from pathlib import Path
from typing import Union
from unittest import mock

import pytest

import tetra3
from conftest import lib_root_dir
from tetra3 import Tetra3


@pytest.mark.parametrize(
    ("star_catalog", "expected_name", "expected_path"),
    [
        # TODO: specifying only the catalog name and automatically building the path relative to the
        #  library files doesn't work (and isn't practical) when installing from a wheel
        # ("bsc5", "bsc5", lib_root_dir() / "bsc5"),
        # ("hip_main", "hip_main", lib_root_dir() / "hip_main.dat"),
        # ("tyc_main", "tyc_main", lib_root_dir() / "tyc_main.dat"),

        # specifying full path
        ("/mock/path/hip_main.dat", "hip_main", Path("/mock/path/hip_main.dat")),
        ("/mock/path/hip_main", "hip_main", Path("/mock/path/hip_main.dat")),
        ("/mock/path/tyc_main.dat", "tyc_main", Path("/mock/path/tyc_main.dat")),
        ("/mock/path/tyc_main", "tyc_main", Path("/mock/path/tyc_main.dat")),
    ]
)
@mock.patch("tetra3.tetra3.Path.exists", return_value=True)
def test_build_catalog_path(
    mock_exists: mock.Mock,
    star_catalog: str,
    expected_name: str,
    expected_path: Union[str, Path],
):
    catalog_name, catalog_path = Tetra3._build_catalog_path(star_catalog)

    assert catalog_name == expected_name
    assert str(catalog_path) == str(expected_path)


@pytest.mark.parametrize(
    "star_catalog",
    [
        # failure by name match
        "random",
        "/mock/path/random.dat",
        lib_root_dir() / "random.dat",
        # failure by not found
        Path(tempfile.gettempdir()) / "hip_main.dat",
    ]
)
def test_build_catalog_path_failure(
    star_catalog: str,
):
    with pytest.raises(ValueError):
        Tetra3._build_catalog_path(star_catalog)


@pytest.mark.slow
def test_generate_database(test_data_dir: Path, tmp_path: Path):
    db_target = tmp_path / "test_db.npz"

    t3 = tetra3.Tetra3(load_database=None)
    t3.generate_database(max_fov=20, save_as=db_target, star_catalog=test_data_dir / "bsc5")

    assert db_target.exists()
