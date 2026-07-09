#!/usr/bin/env python3
"""Generate the synthetic e2e plate-solve corpus by driving synthstars.py.

Writes <name>.{fits,png,json} for each field into tests/data/synthetic/ and
aggregates the JSON ground-truth sidecars into manifest.csv. FITS masters are
git-ignored (regenerable); PNG+JSON are committed and consumed by the test.

Needs Gaia network access (one cone-search per field). Deterministic per field
via a fixed seed. See tests/data/README.md.

Usage:
    python tools/gen_corpus.py [--out-dir tests/data/synthetic] [--only name,name]
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SYNTH = HERE / "synthstars.py"

# name, ra, dec, rotation_deg, maglim -- chosen to span density (dense Milky-Way
# to sparse high-galactic-latitude), declination, and field rotation.
FIELDS = [
    ("orion_eq",     83.8,  -5.4,    0.0, 7.5),   # equatorial, moderate density
    ("cygnus_mw",   305.0,  40.0,   30.0, 7.5),   # dense Milky Way
    ("ngp_sparse",  192.0,  27.0,   15.0, 7.5),   # near N galactic pole, sparse
    ("high_dec",    150.0,  75.0,   60.0, 7.5),   # high declination
    ("south_mid",   100.0, -40.0,  -30.0, 7.5),   # southern mid-latitude
    ("eq_rot90",     45.0,   0.0,   90.0, 7.5),   # equator, 90 deg roll
    ("scutum_mw",   280.0, -10.0,  -60.0, 7.5),   # dense Milky Way
    ("highlat2",    200.0,  60.0,  -45.0, 7.5),   # sparse high galactic latitude
    ("faint_edge",   30.0,  10.0,   45.0, 7.0),   # thinner field, brighter limit
    ("sag_dense",   270.0, -30.0,  120.0, 7.5),   # dense toward galactic center
]

MANIFEST_COLS = ["name", "ra", "dec", "rotation_deg", "fov_x_deg", "fov_y_deg",
                 "pixscale_arcsec", "nx", "ny", "maglim", "n_catalog", "n_rendered", "seed"]


def build_grid(n, maglim=7.5):
    """Deterministic all-sky grid of n fields (dec-major), varied rotation."""
    import math
    decs = [-60.0, -30.0, 0.0, 30.0, 60.0]
    n_ra = math.ceil(n / len(decs))
    fields = []
    for d in decs:
        for i in range(n_ra):
            ra = (i * 360.0 / n_ra) % 360.0
            idx = len(fields)
            rot = (idx * 37) % 360 - 180  # spread rolls across [-180,180)
            fields.append((f"grid_{idx:03d}", round(ra, 3), d, float(rot), maglim))
    return fields[:n]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out-dir", default=str(HERE.parent / "tests" / "data" / "synthetic"))
    ap.add_argument("--only", default=None, help="comma-separated subset of field names")
    ap.add_argument("--grid", type=int, default=None,
                    help="generate an N-field all-sky grid instead of the curated set")
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    only = set(args.only.split(",")) if args.only else None
    fields = build_grid(args.grid) if args.grid else FIELDS

    rows = []
    for seed, (name, ra, dec, rot, maglim) in enumerate(fields):
        if only and name not in only:
            continue
        out = out_dir / name
        cmd = [sys.executable, str(SYNTH),
               "--ra", str(ra), "--dec", str(dec), "--rotation", str(rot),
               "--maglim", str(maglim), "--seed", str(seed), "--out", str(out)]
        print("+", name, flush=True)
        subprocess.run(cmd, check=True)
        gt = json.loads((out.with_suffix(".json")).read_text())
        gt["name"] = name
        rows.append({k: gt.get(k) for k in MANIFEST_COLS})

    # Merge (don't clobber) with any existing manifest rows for fields not regenerated.
    manifest = out_dir / "manifest.csv"
    existing = {}
    if manifest.exists() and only:
        with open(manifest) as f:
            for r in csv.DictReader(f):
                existing[r["name"]] = r
    for r in rows:
        existing[r["name"]] = {k: r[k] for k in MANIFEST_COLS}
    ordered = [existing[n] for n, *_ in fields if n in existing]

    with open(manifest, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=MANIFEST_COLS)
        writer.writeheader()
        writer.writerows(ordered)
    print(f"wrote {manifest} ({len(ordered)} fields)")


if __name__ == "__main__":
    main()
