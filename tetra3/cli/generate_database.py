"""
Generate a database file from a star-catalog.
Provide any argument from Tetra3.generate_database()

Example:
    tetra3-gen-db --max-fov 30  path/to/database/tyc_main path/to/target.npz
"""
import argparse
from pathlib import Path
from typing import Callable, Tuple, Union

import tetra3


def _tuple_type(type_: type) -> Callable[[str], Tuple]:
    def _fn(value: str) -> Tuple:
        string = value.lstrip("(").rstrip(")")
        return tuple(type_(s.strip()) for s in string.split(","))
    return _fn


def _epoch_type(value: str) -> Union[float, str, None]:
    if not value or value.lower() == 'none':
        return None
    if value.lower() == 'now':
        return 'now'
    return float(value)


def main():
    parser = argparse.ArgumentParser(description="Generate star pattern database")

    # positional arguments
    parser.add_argument("STAR_CATALOG", type=Path, help="Star catalog file to load")
    parser.add_argument("SAVE_AS", type=Path, help="File location to save the database")

    # required flags
    parser.add_argument("--max-fov", type=float, required=True,
                        help="Maximum angle (in degrees) between stars in the same pattern.")

    # optional flags
    parser.add_argument("--min-fov", type=float,
                        help="Minimum FOV considered when the catalogue density is trimmed to size.")
    parser.add_argument("--lattice-field-oversampling", type=int, default=100,
                        help="When uniformly distributing pattern generation fields over the celestial sphere, "
                             "this determines the overlap factor.")
    parser.add_argument("--patterns-per-lattice-field", type=int, default=50,
                        help="The number of patterns generated for each lattice field. "
                             "Typical values are 20 to 100.")
    parser.add_argument("--verification-stars-per-fov", type=int, default=150,
                        help="Target number of stars used for generating patterns in each FOV region. "
                             "Also used to limit the number of stars considered for matching in solve images. "
                             "Typical values are large.")
    parser.add_argument("--star-max-magnitude", type=float,
                        help="Dimmest apparent magnitude of stars retained from star catalog. "
                             "When not specified causes the limiting magnitude to be computed based on "
                             "`min_fov` and `verification_stars_per_fov`.")
    parser.add_argument("--pattern-max-error", type=float, default=0.001,
                        help="This value determines the number of bins into which a pattern hash's "
                             "edge ratios are each quantized: `pattern_bins = 0.25 / pattern_max_error` "
                             "Default 0.001, corresponding to pattern_bins=250. For a database with "
                             "limiting magnitude 7, this yields a reasonable pattern hash collision rate.")
    parser.add_argument("--range-ra", type=_tuple_type(float),
                        help="Tuple with the range (min_ra, max_ra) in degrees (0 to 360). "
                             "Given as a comma separated string."
                             "If set, only stars within the given right ascension will be kept in the database.")
    parser.add_argument("--range-dec", type=_tuple_type(float),
                        help="Tuple with the range (min_dec, max_dec) in degrees (-90 to 90). "
                             "Given as a comma separated string."
                             "If set, only stars within the give declination will be kept in the database.")
    parser.add_argument("--presort-patterns", type=bool, default=True,
                        help="If True (the default), all star patterns will be sorted during database "
                             "generation to avoid doing it when solving. Makes database generation "
                             "slower but the solver faster.")
    parser.add_argument("--save-largest-edge", type=bool, default=True,
                        help="If True (default), the absolute size of each pattern is stored "
                             "(via its largest edge angle) in a separate array. This makes the database "
                             "larger but the solver faster.")
    parser.add_argument("--multiscale-step", type=float, default=1.5,
                        help="Determines the largest ratio between subsequent FOVs that is allowed "
                             "when generating a multiscale database. If the ratio max_fov/min_fov "
                             "is less than sqrt(multiscale_step) a single scale database is built.")
    parser.add_argument("--epoch-proper-motion", type=_epoch_type, default='now',
                        help="Determines the end year to which stellar proper motions are propagated. "
                             "If 'now' (default), the current year is used. If 'none', star motions "
                             "are not propagated and this allows catalogue entries without proper "
                             "motions to be used in the database.")

    args = parser.parse_args()

    t3 = tetra3.Tetra3(load_database=None)
    t3.generate_database(
        star_catalog=args.STAR_CATALOG,
        save_as=args.SAVE_AS,
        max_fov=args.max_fov,
        min_fov=args.min_fov,
        lattice_field_oversampling=args.lattice_field_oversampling,
        patterns_per_lattice_field=args.patterns_per_lattice_field,
        verification_stars_per_fov=args.verification_stars_per_fov,
        star_max_magnitude=args.star_max_magnitude,
        pattern_max_error=args.pattern_max_error,
        range_ra=args.range_ra,
        range_dec=args.range_dec,
        presort_patterns=args.presort_patterns,
        save_largest_edge=args.save_largest_edge,
        multiscale_step=args.multiscale_step,
        epoch_proper_motion=args.epoch_proper_motion,
    )

if __name__ == "__main__":
    main()
