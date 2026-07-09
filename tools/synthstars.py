#!/usr/bin/env python3
"""Synthesize a realistic star-field image with a known WCS (ground truth).

Renders REAL Gaia DR3 star positions onto a TAN WCS you define, so both the
astrometry (RA/Dec/roll/FOV) and the pixels are ground-truthed. Emits three
artifacts per field:

  <out>.fits  float32 image + WCS header .......... ground-truth master
  <out>.png   8-bit grayscale ...................... prod-faithful, fed to solver
  <out>.json  ground truth + generation params ..... consumed by the e2e test

Defaults match the target finder-camera spec: 1920x1080, 12.71 deg horizontal
FOV (=> ~23.83 arcsec/px). See tests/data/README.md for how the corpus is used.

Rendering is deterministic for a fixed --seed. Requires network to the Gaia
archive (astroquery) at generation time only; the committed PNG+JSON are what
offline test runs use.

NOTE ON PSF SIZE: at ~24 arcsec/px a physical seeing FWHM is sub-pixel, so we
parameterize the PSF in PIXELS (--fwhm-px, default 1.6) rather than arcsec --
otherwise stars would be single-pixel and indistinguishable from hot pixels.
This is a deliberate deviation from the arcsec-based sketch in the task doc.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS


def build_wcs(ra, dec, nx, ny, pixscale_arcsec, rotation_deg=0.0, flip=False):
    """TAN WCS centered on (ra, dec). This is the astrometric ground truth."""
    w = WCS(naxis=2)
    w.wcs.crpix = [nx / 2 + 0.5, ny / 2 + 0.5]
    w.wcs.crval = [ra, dec]
    w.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    s = pixscale_arcsec / 3600.0
    t = np.deg2rad(rotation_deg)
    sx = -s if flip else s
    w.wcs.cd = np.array([[sx * np.cos(t), -sx * np.sin(t)],
                         [s * np.sin(t), s * np.cos(t)]])
    return w


def gaia_catalog(ra, dec, radius_deg, maglim):
    """Cone-search Gaia DR3. Returns (ra[], dec[], gmag[]) as numpy arrays."""
    from astroquery.gaia import Gaia

    adql = f"""
        SELECT ra, dec, phot_g_mean_mag
        FROM gaiadr3.gaia_source
        WHERE 1=CONTAINS(POINT('ICRS', ra, dec),
                         CIRCLE('ICRS', {ra}, {dec}, {radius_deg}))
          AND phot_g_mean_mag < {maglim}
    """
    t = Gaia.launch_job_async(adql).get_results()
    good = np.isfinite(t["phot_g_mean_mag"])
    return (np.asarray(t["ra"])[good],
            np.asarray(t["dec"])[good],
            np.asarray(t["phot_g_mean_mag"])[good])


def render(nx, ny, xs, ys, mags, *, fwhm_px, zp, sky, read_noise, gain,
           saturate, moon_amp, gradient, seed):
    """Deposit Gaussian PSFs (flux from Gaia G mag) and add sky + noise.

    Values are in ADU. Returns the float image (pre-clip, for FITS)."""
    rng = np.random.default_rng(seed)
    img = np.zeros((ny, nx), dtype=np.float64)

    sigma = fwhm_px / 2.3548200450309493  # FWHM -> Gaussian sigma
    norm = 1.0 / (2.0 * math.pi * sigma * sigma)
    half = max(3, int(math.ceil(4.0 * sigma)))
    oy, ox = np.mgrid[-half:half + 1, -half:half + 1]

    for x, y, m in zip(xs, ys, mags):
        ix, iy = int(round(x)), int(round(y))
        if ix < -half or ix >= nx + half or iy < -half or iy >= ny + half:
            continue
        flux = 10.0 ** (-0.4 * (m - zp))            # total ADU in the star
        dx, dy = ox - (x - ix), oy - (y - iy)       # sub-pixel offset
        stamp = flux * norm * np.exp(-(dx * dx + dy * dy) / (2.0 * sigma * sigma))
        x0, x1 = ix - half, ix + half + 1
        y0, y1 = iy - half, iy + half + 1
        sx0, sy0 = max(0, -x0), max(0, -y0)
        sx1 = stamp.shape[1] - max(0, x1 - nx)
        sy1 = stamp.shape[0] - max(0, y1 - ny)
        if sx0 >= sx1 or sy0 >= sy1:
            continue
        img[max(0, y0):min(ny, y1), max(0, x0):min(nx, x1)] += stamp[sy0:sy1, sx0:sx1]

    # Sky pedestal, optional light-pollution gradient and radial moonglow.
    img += sky
    if gradient:
        gx = np.linspace(0.0, gradient, nx)[None, :]
        img += gx
    if moon_amp:
        cy, cx = ny * 0.15, nx * 0.15
        r = np.hypot(np.arange(ny)[:, None] - cy, np.arange(nx)[None, :] - cx)
        img += moon_amp * np.exp(-r / (0.4 * nx))

    # Poisson shot noise (via electrons) + Gaussian read noise.
    electrons = np.clip(img * gain, 0, None)
    noisy = rng.poisson(electrons).astype(np.float64) / gain
    noisy += rng.normal(0.0, read_noise, size=noisy.shape)
    noisy = np.clip(noisy, 0.0, saturate)
    return noisy


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ra", type=float, required=True, help="field center RA (deg)")
    ap.add_argument("--dec", type=float, required=True, help="field center Dec (deg)")
    ap.add_argument("--nx", type=int, default=1920)
    ap.add_argument("--ny", type=int, default=1080)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--fov", type=float, default=12.71,
                   help="horizontal FOV in deg (box spec 12.71); sets pixscale")
    g.add_argument("--pixscale", type=float, default=None,
                   help="arcsec/px; overrides --fov if given")
    ap.add_argument("--rotation", type=float, default=0.0, help="field rotation (deg)")
    # flip=False is the handedness tetra3 (and thus the production camera) expects;
    # flip=True mirrors the field and will NOT solve (patterns are chirality-sensitive).
    ap.add_argument("--flip", dest="flip", action="store_true", default=False,
                    help="mirror handedness (default off; on will not solve)")
    ap.add_argument("--no-flip", dest="flip", action="store_false")
    ap.add_argument("--maglim", type=float, default=7.5, help="Gaia G limit")
    ap.add_argument("--fwhm-px", type=float, default=1.6, help="PSF FWHM in pixels")
    ap.add_argument("--zp", type=float, default=12.5,
                    help="magnitude zeropoint (mag giving 1 ADU total flux); tuned so "
                         "the sigma=8 detection floor sits near the catalog limit")
    ap.add_argument("--sky", type=float, default=10.0, help="sky pedestal (ADU)")
    ap.add_argument("--read-noise", type=float, default=1.5, help="read noise (ADU)")
    ap.add_argument("--gain", type=float, default=1.0, help="electrons per ADU")
    ap.add_argument("--saturate", type=float, default=255.0)
    ap.add_argument("--moon", type=float, default=0.0, help="moonglow amplitude (ADU)")
    ap.add_argument("--gradient", type=float, default=0.0, help="LP gradient (ADU across x)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", type=str, required=True, help="output path prefix")
    args = ap.parse_args()

    pixscale = args.pixscale if args.pixscale else args.fov * 3600.0 / args.nx
    fov_x = args.nx * pixscale / 3600.0
    fov_y = args.ny * pixscale / 3600.0
    radius = 0.5 * math.hypot(fov_x, fov_y) * 1.15  # cone covers corners + margin

    w = build_wcs(args.ra, args.dec, args.nx, args.ny, pixscale, args.rotation, args.flip)

    cat_ra, cat_dec, cat_mag = gaia_catalog(args.ra, args.dec, radius, args.maglim)
    px, py = w.wcs_world2pix(cat_ra, cat_dec, 0)  # 0-based pixel coords
    inb = (px > -5) & (px < args.nx + 5) & (py > -5) & (py < args.ny + 5)
    px, py, mg = px[inb], py[inb], cat_mag[inb]

    img = render(args.nx, args.ny, px, py, mg,
                 fwhm_px=args.fwhm_px, zp=args.zp, sky=args.sky,
                 read_noise=args.read_noise, gain=args.gain, saturate=args.saturate,
                 moon_amp=args.moon, gradient=args.gradient, seed=args.seed)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    # FITS master (float32) with WCS header = astrometric ground truth.
    hdr = w.to_header()
    hdr["BUNIT"] = "ADU"
    hdr["HISTORY"] = "synthstars.py Gaia DR3 synthetic field"
    fits.PrimaryHDU(data=img.astype(np.float32), header=hdr).writeto(
        out.with_suffix(".fits"), overwrite=True)

    # 8-bit grayscale PNG = prod-faithful image actually fed to the solver.
    from PIL import Image
    png8 = np.clip(np.round(img), 0, 255).astype(np.uint8)
    Image.fromarray(png8, mode="L").save(out.with_suffix(".png"))

    # Ground-truth + params sidecar.
    truth = {
        "ra": args.ra, "dec": args.dec,
        "rotation_deg": args.rotation, "flip": args.flip,
        "fov_x_deg": fov_x, "fov_y_deg": fov_y,
        "pixscale_arcsec": pixscale, "nx": args.nx, "ny": args.ny,
        "maglim": args.maglim, "fwhm_px": args.fwhm_px, "zp": args.zp,
        "sky_adu": args.sky, "read_noise_adu": args.read_noise, "gain": args.gain,
        "moon": args.moon, "gradient": args.gradient, "seed": args.seed,
        "n_catalog": int(cat_ra.size), "n_rendered": int(px.size),
        "generator": "synthstars.py",
    }
    with open(out.with_suffix(".json"), "w") as f:
        json.dump(truth, f, indent=2)

    p99 = float(np.percentile(png8, 99.9))
    print(f"{out.name}: fov={fov_x:.2f}x{fov_y:.2f} deg pixscale={pixscale:.2f}\"/px "
          f"catalog={cat_ra.size} rendered={px.size} "
          f"png[min={png8.min()} med={np.median(png8):.0f} p99.9={p99:.0f} max={png8.max()}]")


if __name__ == "__main__":
    main()
