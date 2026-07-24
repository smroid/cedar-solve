# e2e plate-solve corpus

Realistic synthetic star fields used by `tests/test_solve_e2e.py` to test the
full solve pipeline end to end: 8-bit PNG → Cedar Detect centroids →
`tetra3.solve_from_centroids`, asserting the recovered pose against known ground
truth.

Images are rendered from **real Gaia DR3** star positions (patterns must match
the solver's index) onto a TAN WCS we define, so RA/Dec/roll/FOV are all
ground-truthed. Deterministic per seed. Target finder-camera spec:

- 1920×1080, **12.71° × 7.16°** field of view, ~**23.83 arcsec/px**.

## Layout

| path | committed? | purpose |
|------|-----------|---------|
| `datasets.json` | yes | remote dataset registry: download URL + pinned SHA256 |
| `synthetic_v1/manifest.csv` | yes | per-field ground truth (ra/dec/rotation/fov …) — the solver test reads this |
| `synthetic_large/` | **no** (git-ignored) | images fetched at runtime by `tools/fetch_corpus.py` |

The PNGs (~110 MB) are **not** committed; they live as a tarball on a GitHub
Release. Only the small manifest is committed, so test collection works offline
and the image download happens lazily the first time an `e2e` test runs.

## Running

Opt-in (marker `e2e`, skipped by default):

```bash
pytest -m e2e                       # fetches + verifies the dataset once, then runs
```

Requires the `cedar-detect-server` binary at `tetra3/bin/cedar-detect-server`
(symlink your built `cedar-detect/target/release/cedar-detect-server`; build it
per target architecture). The test skips with a clear message if it is missing.

Run against a locally generated corpus instead of the download:

```bash
python tools/gen_corpus.py --grid 100 --out-dir /tmp/grid
CEDAR_E2E_DATA_DIR=/tmp/grid pytest -m e2e
```

## Regenerating and publishing the dataset

Needs network to the Gaia archive (`pip install astropy astroquery`):

```bash
python tools/gen_corpus.py --grid 100 --out-dir /tmp/grid   # one Gaia query per field
tar -C /tmp/grid --exclude='*.fits' -czf cedar_e2e_synthetic_v1.tar.gz .
sha256sum cedar_e2e_synthetic_v1.tar.gz                      # update datasets.json
gh release create e2e-corpus-v1 cedar_e2e_synthetic_v1.tar.gz   # or upload to a new tag
cp /tmp/grid/manifest.csv tests/data/synthetic_v1/manifest.csv  # keep committed truth in sync
```

Then `tools/fetch_corpus.py` downloads that tarball, verifies its SHA256 against
`datasets.json`, and extracts it into `synthetic_large/`.

## Conventions (pinned empirically)

- **Handedness:** the WCS is generated with `flip=False` (default). `flip=True`
  mirrors the field and will NOT solve — tetra3 patterns are chirality-sensitive.
- **Roll:** solver `Roll == (180 + rotation_deg) mod 360`.
- **Brightness:** the flux zeropoint (`--zp`, default 12.5) is tuned so the
  Cedar Detect sigma=8 floor sits near the catalog magnitude limit, i.e. most
  in-frame stars are detected (a too-dim render starves the solver).
- **Pass tolerance:** center < 5 arcmin, |roll| < 1°, |FOV−FOV_gt|/FOV_gt < 2%.
- **Database:** `default_database` (HIP catalog, FOV 10–30°, mag ≤ 8) covers the
  12.71° field.
