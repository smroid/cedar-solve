"""
Enumerate test FOVs from a star catalog and evaluate Cedar's performance
solving them.

Example:
    python benchmark_synthetic_fovs.py --width 1280 --height 960 --fov_deg 12 --num_fovs 1000
"""
import argparse

from tetra3 import benchmark_synthetic_fovs
from pathlib import Path
from typing import List

def _print_histo_bin(solve_time_histo: List[float], bin_width: float):
    for histo_bin, val in enumerate(solve_time_histo):
        if val == 0:
            continue

        hv = histo_bin * bin_width
        if histo_bin < len(solve_time_histo) - 1:
            print(f'{hv}-{(histo_bin + 1) * bin_width}ms: {val}')
        else:
            print(f'>= {hv}ms: {val}')


def main():
    parser = argparse.ArgumentParser(description="Synthesize FOVs and test Cedar-solve")

    # required flags
    parser.add_argument("--width", type=int, required=True,
                        help="Width (in pixels) of image sensor.")
    parser.add_argument("--height", type=int, required=True,
                        help="Height (in pixels) of image sensor.")
    parser.add_argument("--fov_deg", type=float, required=True,
                        help="Horizontal field of view (in degrees) of image.")
    parser.add_argument("--num_fovs", type=int, required=True,
                        help="Number of FOVs to synthesize (2N + 1 actually generated).")

    # optional flags
    parser.add_argument("--num_centroids", type=int, default=20,
                        help="Maximum number of centroids to pass to solver.")
    parser.add_argument("--database", type=Path, default='default_database',
                        help="Pattern database to load.")

    args = parser.parse_args()

    result = benchmark_synthetic_fovs.benchmark_synthetic_fovs(
        args.width, args.height, args.fov_deg, args.num_fovs, args.num_centroids,
        database=args.database)

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
    _print_histo_bin(result['solve_time_histo'], result['histo_bin_width_ms'])


if __name__ == "__main__":
    main()
