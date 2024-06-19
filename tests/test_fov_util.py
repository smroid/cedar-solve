from __future__ import annotations

from typing import List, Tuple

import numpy as np
import pytest

from tetra3 import fov_util


@pytest.mark.parametrize(
    ("fov", "stars_per_fov", "expected"),
    [
        # degrees
        (10, 10, 1.897366596),
        (90, 10, 17.07629936),
        # radians
        (np.deg2rad(10), 10, 0.03311529),
        (np.deg2rad(90), 10, 0.29803764)
    ]
)
def test_fov_util_separation_for_density(fov: float, stars_per_fov: int, expected: float):
    result = fov_util.separation_for_density(fov, stars_per_fov)
    assert result == pytest.approx(expected)


@pytest.mark.parametrize(
    ("fov_rad", "expected"),
    [
        (np.deg2rad(10), 413),
        (np.deg2rad(90), 6)
    ]
)
def test_fov_util_num_fields_for_sky(fov_rad: float, expected: int):
    result = fov_util.num_fields_for_sky(fov_rad)
    assert result == expected


@pytest.mark.parametrize(
    ("num", "expected"),
    [
        (1, [(-0.5496023119586261, -0.5034807387033675, -0.6666666666666666),
             (1.0, 0.0, 0.0),
             (-0.5496023119586261, 0.5034807387033675, 0.6666666666666666)]),
        (2, [(0.05245543483017645, 0.5977026245188964, -0.8),
             (-0.6758097397797131, -0.6190970809322852, -0.4),
             (1.0, 0.0, 0.0),
             (-0.6758097397797131, 0.6190970809322852, 0.4),
             (0.05245543483017645, -0.5977026245188964, 0.8)]),
        (3, [(0.3133939301777415, -0.40876688586127985, -0.8571428571428571),
             (0.0717460789365099, 0.8175095644164282, -0.5714285714285714),
             (-0.7066315439468049, -0.6473323783329011, -0.2857142857142857),
             (1.0, 0.0, 0.0),
             (-0.7066315439468049, 0.6473323783329011, 0.2857142857142857),
             (0.0717460789365099, -0.8175095644164282, 0.5714285714285714),
             (0.3133939301777415, 0.40876688586127985, 0.8571428571428571)]),
    ]
)
def test_fov_util_fibonacci_sphere_lattice(num: int, expected: List[Tuple[float, float, float]]):
    result = list(fov_util.fibonacci_sphere_lattice(num))
    assert result == expected
