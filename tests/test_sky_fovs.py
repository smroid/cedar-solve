from tetra3 import benchmark_synthetic_fovs
import pytest

@pytest.mark.slow
def test_benchmark_synthetic_fovs():
    """
    Test to enumerate test FOVs from a star catalog and evaluate
    Cedar's performance solving them.
    """
    # Pixel count of sensor.
    WIDTH = 1280
    HEIGHT = 960

    # Horizontal FOV, in degrees.
    FOV_DEG = 15

    # Number of FOVs to generate. 2n + 1 FOVs are actually generated.
    FOV_N = 1000

    NUM_CENT = 20  # Number of centroids to pass to solver.

    result = benchmark_synthetic_fovs.benchmark_synthetic_fovs(
        WIDTH, HEIGHT, FOV_DEG, FOV_N, NUM_CENT)
    num_failures = result['num_failures']
    num_successes = result['num_successes']
    mean_solve_time_ms = result['mean_solve_time_ms']
    max_solve_time_ms = result['max_solve_time_ms']
    print(
        'Results - '
        f'num_failures: {num_failures} '
        f'mean_solve_time_ms: {mean_solve_time_ms:.1f} '
        f'max_solve_time_ms: {max_solve_time_ms}'
    )

    assert num_failures == 0
    assert num_successes == 2001
