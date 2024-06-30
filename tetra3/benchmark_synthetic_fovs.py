import math

import numpy as np
import pytest
from scipy.spatial.transform import Rotation as R

import tetra3
from tetra3 import fov_util

"""
Test utility to enumerate test FOVs from a star catalog and evaluate
Cedar's performance solving them. Adapted from code provided by Iain Clark.

Note: Angle values are in radians unless suffixed with _deg.
"""

def _ra_dec_from_vector(vec):
    """Returns (ra, dec) from the given (x, y, z) star vector."""
    x, y, z = vec
    ra = math.atan2(y, x)
    dec = math.asin(z)
    return (ra, dec)


def benchmark_synthetic_fovs(width, height, fov_deg, num_fovs,
                             num_centroids=20, database='default_database'):
    """Synthesizes and solves star fields.
    width, height: pixel count of camera
    fov_deg: horizontal FOV, in degrees
    num_fovs: Number of FOVs to generate. 2n + 1 FOVs are actually generated.
        0 generates a single FOV; 1 generates 3 FOVs, etc.
    num_centroids: max number of centroids to pass to solver.

    Returns: dict with the following fields:
    num_successes
    num_failures
    mean_solve_time_ms
    max_solve_time_ms
    solve_time_histo
    histo_bin_width_ms
    """

    # TODO: apply noise to x/y centroids; apply noise to brightness ranking.

    diag_pixels = math.sqrt(width * width + height * height)
    diag_fov = np.deg2rad(fov_deg * diag_pixels / width)
    scale_factor = width / 2 / np.tan(np.deg2rad(fov_deg) / 2)

    # Histogram of successful solve times.
    NUM_HISTO_BINS = 200
    MAX_SOLVE_TIME_MS = 1000
    solve_time_histo = [0] * NUM_HISTO_BINS
    bin_width = MAX_SOLVE_TIME_MS / NUM_HISTO_BINS

    total_solve_time_ms = 0
    max_solve_time_ms = 0
    num_successes = 0
    num_failures = 0

    t3 = tetra3.Tetra3(load_database=database)

    print('Start solving...')
    iter_count = 0
    for center_vec in fov_util.fibonacci_sphere_lattice(num_fovs):
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
        proj_xyz_scaled[0] = proj_xyz_scaled[0] + width / 2
        proj_xyz_scaled[1] = proj_xyz_scaled[1] + height / 2

        centroids = []
        for index in range(len(proj_xyz_scaled[0])):
            x = proj_xyz_scaled[0][index]
            y = proj_xyz_scaled[1][index]
            # Only keep centroids within the image area. Add a small border, reflects
            # that Cedar-Detect cannot detect at edge.
            if x < 2 or y < 2 or x >= width - 2 or y >= height - 2:
                continue
            centroids.append((y, x))
            if len(centroids) >= num_centroids:
                break  # Keep only num_centroids brightest centroids.

        solution = t3.solve_from_centroids(centroids, size=(height, width), distortion=0,
                                           fov_estimate=fov_deg, fov_max_error=fov_deg/10.0)
        if iter_count % 1000 == 0:
            print(f'iter {iter_count}; solution for ra/dec {np.rad2deg(ra):.4f}/{np.rad2deg(dec):.4f}: {solution}')

        if solution['RA'] is None:
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
        histo_bin = int(time_ms / bin_width)
        if histo_bin >= len(solve_time_histo):
            histo_bin = len(solve_time_histo) - 1
        solve_time_histo[histo_bin] += 1

    return {'num_successes': num_successes,
            'num_failures': num_failures,
            'mean_solve_time_ms': total_solve_time_ms / num_successes,
            'max_solve_time_ms': max_solve_time_ms,
            'solve_time_histo': solve_time_histo,
            'histo_bin_width_ms': bin_width
            }
