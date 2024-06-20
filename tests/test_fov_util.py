from typing import List, Tuple

import numpy as np
import pytest

from tetra3 import fov_util


@pytest.mark.parametrize(
    ("fov", "stars_per_fov", "expected"),
    [
        # degrees
        (10, 10, 1.89736659),
        (90, 10, 17.0762993),
        # radians
        (np.deg2rad(10), 10, 0.0331153),
        (np.deg2rad(90), 10, 0.2980376)
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
    ("num", "expected_list"),
    [
        (1, [(-0.54960231, -0.50348073, -0.66666666),
             (1.0, 0.0, 0.0),
             (-0.54960231, 0.50348073, 0.66666666)]),
        (2, [(0.052455434, 0.59770262, -0.8),
             (-0.67580973, -0.61909708, -0.4),
             (1.0, 0.0, 0.0),
             (-0.67580973, 0.61909708, 0.4),
             (0.052455434, -0.59770262, 0.8)]),
        (3, [(0.31339393, -0.408766885, -0.85714285),
             (0.07174607, 0.81750956, -0.57142857),
             (-0.70663154, -0.64733237, -0.28571428),
             (1.0, 0.0, 0.0),
             (-0.70663154, 0.64733237, 0.28571428),
             (0.07174607, -0.81750956, 0.57142857),
             (0.31339393, 0.408766885, 0.85714285)]),
    ]
)
def test_fov_util_fibonacci_sphere_lattice(num: int, expected_list: List[Tuple[float, float, float]]):
    result_list = list(fov_util.fibonacci_sphere_lattice(num))
    for actual_tuple, expected_tuple in zip(result_list, expected_list):
        for actual, expected in zip(actual_tuple, expected_tuple):
            assert actual == pytest.approx(expected)
