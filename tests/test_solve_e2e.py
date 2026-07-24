"""End-to-end plate-solve tests on realistic synthetic star fields.

Opt-in (marker `e2e`; skipped by default). Drives the *production centroid
path*: 8-bit PNG -> Cedar Detect (gRPC) centroids -> tetra3.solve_from_centroids,
using production solver params (distortion=0, match_max_error=0.005, 1s timeout),
and asserts the recovered pose against the WCS ground truth in the manifest.

Ground truth (per-field ra/dec/rotation/fov) is committed in
tests/data/synthetic_v1/manifest.csv. The images themselves are NOT committed;
they are fetched on demand from a GitHub Release (see tests/data/README.md and
tools/fetch_corpus.py). So plain collection needs only the manifest; the ~110 MB
image download happens lazily, once, when an e2e test actually runs.

Run:   pytest -m e2e
"""
import csv
import os
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

_HERE = Path(__file__).parent
MANIFEST = _HERE / "data" / "synthetic_v1" / "manifest.csv"
DEFAULT_DATASET = "synthetic_v1"

# Pass criteria: center offset, roll, and FOV vs. ground truth. Roll uses the
# empirically-pinned mapping solver_Roll == (180 + rotation_deg) mod 360.
CENTER_TOL_ARCMIN = 5.0
ROLL_TOL_DEG = 1.0
FOV_TOL_FRAC = 0.02

# Production solver / detector params (match the cedar-server solve pipeline).
SOLVE_KW = dict(distortion=0.0, match_max_error=0.005, solve_timeout=1000)
DETECT_KW = dict(sigma=8, use_binned=True, detect_hot_pixels=True)


def _fields():
    if not MANIFEST.exists():
        return []
    with open(MANIFEST) as f:
        return list(csv.DictReader(f))


def _sep_arcmin(ra1, dec1, ra2, dec2):
    from astropy.coordinates import SkyCoord
    import astropy.units as u
    a = SkyCoord(ra1 * u.deg, dec1 * u.deg)
    b = SkyCoord(ra2 * u.deg, dec2 * u.deg)
    return float(a.separation(b).arcmin)


def _roll_err_deg(solved_roll, rotation_deg):
    expected = (180.0 + rotation_deg) % 360.0
    return abs((solved_roll - expected + 180.0) % 360.0 - 180.0)


@pytest.fixture(scope="module")
def image_dir():
    """Dir holding the field PNGs.

    - CEDAR_E2E_DATA_DIR=<dir> : use that dir (e.g. a locally regenerated corpus).
    - else                     : fetch+verify the dataset named by CEDAR_E2E_DATASET
                                 (default `synthetic_v1`) from its GitHub Release.
    """
    override = os.environ.get("CEDAR_E2E_DATA_DIR")
    if override:
        return Path(override)
    sys.path.insert(0, str(_HERE.parent / "tools"))
    import fetch_corpus
    return fetch_corpus.fetch(os.environ.get("CEDAR_E2E_DATASET", DEFAULT_DATASET))


@pytest.fixture(scope="module")
def solver():
    import tetra3
    return tetra3.Tetra3(load_database="default_database")


@pytest.fixture(scope="module")
def detector():
    import tetra3
    from tetra3 import cedar_detect_client
    binpath = Path(tetra3.__file__).parent / "bin" / "cedar-detect-server"
    if not binpath.exists():
        pytest.skip(f"cedar-detect-server binary not found at {binpath}; "
                    "see tests/data/README.md")
    client = cedar_detect_client.CedarDetectClient()
    yield client
    del client


@pytest.mark.e2e
@pytest.mark.parametrize("field", _fields(), ids=lambda f: f["name"])
def test_solve_field(field, image_dir, solver, detector):
    """Each synthetic field solves and recovers pose within tight tolerance."""
    img = np.asarray(Image.open(image_dir / f"{field['name']}.png").convert("L"),
                     dtype=np.uint8)
    h, w = img.shape

    centroids = detector.extract_centroids(img, **DETECT_KW)
    sol = solver.solve_from_centroids(centroids[:30], (h, w), **SOLVE_KW)

    assert sol.get("RA") is not None, \
        f"{field['name']}: no solution from {len(centroids)} centroids"

    ra, dec = float(field["ra"]), float(field["dec"])
    fov_gt = float(field["fov_x_deg"])
    rot = float(field["rotation_deg"])

    center_err = _sep_arcmin(sol["RA"], sol["Dec"], ra, dec)
    fov_err = abs(sol["FOV"] - fov_gt) / fov_gt
    roll_err = _roll_err_deg(sol["Roll"], rot)

    assert center_err < CENTER_TOL_ARCMIN, \
        f"{field['name']}: center off by {center_err:.2f}' (> {CENTER_TOL_ARCMIN}')"
    assert fov_err < FOV_TOL_FRAC, \
        f"{field['name']}: FOV off by {fov_err*100:.2f}% (> {FOV_TOL_FRAC*100}%)"
    assert roll_err < ROLL_TOL_DEG, \
        f"{field['name']}: roll off by {roll_err:.2f} deg (> {ROLL_TOL_DEG})"


@pytest.mark.e2e
def test_blank_frame_does_not_solve(solver, detector):
    """Negative control: an empty frame must not yield a (false) solution."""
    img = np.zeros((1080, 1920), dtype=np.uint8)
    centroids = detector.extract_centroids(img, **DETECT_KW)
    sol = solver.solve_from_centroids(centroids[:30], (1080, 1920), **SOLVE_KW)
    assert sol.get("RA") is None


@pytest.mark.e2e
def test_random_centroids_do_not_solve(solver):
    """Negative control: random (non-sky) centroids must not solve -- guards
    against a tautological always-pass test."""
    rng = np.random.default_rng(0)
    centroids = rng.uniform([0, 0], [1080, 1920], size=(30, 2))
    sol = solver.solve_from_centroids(centroids, (1080, 1920), **SOLVE_KW)
    assert sol.get("RA") is None
