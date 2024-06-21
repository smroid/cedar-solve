import math
from typing import List

import numpy as np
import pytest
from scipy.spatial.transform import Rotation as R

import tetra3
from tetra3 import fov_util


def _ra_dec_from_vector(vec):
    """Returns (ra, dec) from the given (x, y, z) star vector."""
    x, y, z = vec
    ra = math.atan2(y, x)
    dec = math.asin(z)
    return (ra, dec)


def _print_histo_bin(solve_time_histo: List[float], bin_width: float):
    for histo_bin, val in enumerate(solve_time_histo):
        if val == 0:
            continue

        hv = histo_bin * bin_width
        if histo_bin < len(solve_time_histo) - 1:
            print(f'{hv}-{(histo_bin + 1) * bin_width}ms: {val}')
        else:
            print(f'>= {hv}ms: {val}')


@pytest.mark.slow
def test_fov_util_fibonacci_sphere_lattice_performance():
    """
    Test script to enumerate test FOVs from a star catalog and evaluate
    Cedar's performance solving them. Adapted from code provided by Iain Clark.

    Note: Angle values are in radians unless suffixed with _deg.
    """

    # TODO: apply noise to x/y centroids; apply noise to brightness ranking.

    # Pixel c`ount of sensor.
    WIDTH = 1280
    HEIGHT = 960

    # Horizontal FOV, in degrees.
    FOV_DEG = 15

    # Number of FOVs to generate. 2n + 1 FOVs are actually generated.
    # 0 generates a single FOV; 1 generates 3 FOVs, etc.
    FOV_N = 1000

    NUM_CENT = 20  # Number of centroids to pass to solver.`

    diag_pixels = math.sqrt(WIDTH * WIDTH + HEIGHT * HEIGHT)
    diag_fov = np.deg2rad(FOV_DEG * diag_pixels / WIDTH)
    scale_factor = WIDTH / 2 / np.tan(np.deg2rad(FOV_DEG) / 2)

    # Histogram of successful solve times.
    NUM_HISTO_BINS = 200
    MIN_SOLVE_TIME_MS = 0
    MAX_SOLVE_TIME_MS = 1000
    solve_time_histo = [0] * NUM_HISTO_BINS
    bin_width = (MAX_SOLVE_TIME_MS - MIN_SOLVE_TIME_MS) / NUM_HISTO_BINS

    total_solve_time_ms = 0
    max_solve_time_ms = 0
    num_successes = 0
    num_failures = 0

    t3 = tetra3.Tetra3(load_database='default_database')

    print('Start solving...')
    iter_count = 0
    for center_vec in fov_util.fibonacci_sphere_lattice(FOV_N):
        iter_count += 1

        ra, dec = _ra_dec_from_vector(center_vec)
        if ra < 0:
            ra += 2 * np.pi

        nearby_star_inds = t3._get_nearby_stars(center_vec, diag_fov / 2)
        nearby_stars = t3.star_table[nearby_star_inds]

        nearby_ra = nearby_stars.transpose()[0]
        nearby_dec = nearby_stars.transpose()[1]

        # un-rotate RA
        nearby_ra_rot = nearby_ra - ra

        # convert rotated to cartesian
        proj_xyz = np.zeros([3, nearby_ra.shape[0]])
        proj_xyz[0] = np.cos(nearby_ra_rot) * np.cos(nearby_dec)  # x
        proj_xyz[1] = np.sin(nearby_ra_rot) * np.cos(nearby_dec)  # y
        proj_xyz[2] = np.sin(nearby_dec)  # z

        # rotate to remove dec of target star
        # rotate from xy plane parallel to xz plane to +ve Z to zero declination
        r = R.from_rotvec([0, (-np.pi / 2 + dec), 0])
        proj_xyz = r.apply(proj_xyz.transpose()).transpose()

        # project stars on z=1 plane perpendicular to boresight
        proj_xyz[0] = proj_xyz[0] / proj_xyz[2]
        proj_xyz[1] = proj_xyz[1] / proj_xyz[2]

        # scale to image pixels
        proj_xyz_scaled = proj_xyz * scale_factor
        proj_xyz_scaled[0] = proj_xyz_scaled[0] + WIDTH / 2
        proj_xyz_scaled[1] = proj_xyz_scaled[1] + HEIGHT / 2

        centroids = []
        for index in range(len(proj_xyz_scaled[0])):
            x = proj_xyz_scaled[0][index]
            y = proj_xyz_scaled[1][index]
            # Only keep centroids within the image area. Add a small border, reflects
            # that Cedar-Detect cannot detect at edge.
            if x < 2 or y < 2 or x >= WIDTH - 2 or y >= HEIGHT - 2:
                continue
            centroids.append((y, x))
            if len(centroids) >= NUM_CENT:
                break  # Keep only NUM_CENT brightest centroids.

        solution = t3.solve_from_centroids(centroids, size=(HEIGHT, WIDTH), distortion=0)
        if iter_count % 1000 == 0:
            print(f'iter {iter_count}; solution for ra/dec {np.rad2deg(ra):.4f}/{np.rad2deg(dec):.4f}: {solution}')

        if solution['RA'] is None:
            # soft failure, assert total at end
            num_failures += 1
            continue

        num_successes += 1
        ra_diff = np.rad2deg(ra) - solution['RA']
        if ra_diff > 180:
            ra_diff -= 360
        if ra_diff < -180:
            ra_diff += 360
        if abs(ra_diff) > 0.3:
            pytest.fail(f"'expected RA {np.rad2deg(ra)}, got {solution['RA']} (dec {solution['Dec']})'")
        if abs(np.rad2deg(dec) - solution['Dec']) > 0.3:
            pytest.fail(f"expected Dec {np.rad2deg(dec)}, got {solution['Dec']}")

        total_solve_time_ms += solution['T_solve']
        time_ms = int(solution['T_solve'])
        max_solve_time_ms = max(time_ms, max_solve_time_ms)
        histo_bin = int((time_ms - MIN_SOLVE_TIME_MS) / bin_width)
        if histo_bin >= len(solve_time_histo):
            histo_bin = len(solve_time_histo) - 1
        solve_time_histo[histo_bin] += 1

    print(
        'Results - '
        f'num_failures: {num_failures} '
        f'mean_solve_time_ms: {(total_solve_time_ms / num_successes):.1f} '
        f'max_solve_time_ms: {max_solve_time_ms}'
    )
    _print_histo_bin(solve_time_histo, bin_width)

    assert num_failures == 0
    assert num_successes == 2001
