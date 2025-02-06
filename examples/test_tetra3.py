"""
This example loads the tetra3 default database and solves for every image in the
tetra3/examples/data/medium_fov directory.
"""

import os
import sys

print("path %s" % sys.path)

import numpy as np
from PIL import Image, ImageDraw
from pathlib import Path
from time import perf_counter as precision_timestamp
EXAMPLES_DIR = Path(__file__).parent

import tetra3

# centre is (y, x).
def draw_circle(img_draw, centre, radius, **kwargs):
    bbox = [centre[1] - radius, centre[0] - radius, centre[1] + radius, centre[0] + radius]
    img_draw.ellipse(bbox, **kwargs)

def draw_box(img_draw, centre, radius, **kwargs):
    bbox = [centre[1] - radius, centre[0] - radius, centre[1] + radius, centre[0] + radius]
    img_draw.rectangle(bbox, **kwargs)

# Use cedar_detect if we are able to load it.
try:
    from tetra3 import cedar_detect_client
    cedar_detect = cedar_detect_client.CedarDetectClient()
    USE_CEDAR_DETECT = True
except Exception as e:
    print("WARNING: could not setup Cedar Detect client: %s" % e);
    USE_CEDAR_DETECT = False

# Create instance and load the default database, built for 30 to 10 degree field of view.
# Pass `load_database=None` to not load a database (e.g. to build your own; see
# generate_database.py example script).
t3 = tetra3.Tetra3(load_database='default_database')

# Path where images are
path = EXAMPLES_DIR / 'data' / 'medium_fov'
# path = EXAMPLES_DIR / 'data' / 'large_fov'
try:
    for impath in path.glob('*'):
        try:
            with Image.open(str(impath)) as img:
                img = img.convert(mode='L')
                np_image = np.asarray(img, dtype=np.uint8)

                t0 = precision_timestamp()
                if USE_CEDAR_DETECT:
                    centroids = cedar_detect.extract_centroids(
                        np_image, sigma=8, max_size=10, use_binned=True)
                else:
                    centroids = tetra3.get_centroids_from_image(np_image)
                t_extract = (precision_timestamp() - t0)*1000

                basename = os.path.basename(impath)
                print('File %s, extracted %d centroids in %.2fms' %
                      (basename, len(centroids), t_extract))

                # Draw a small blue circle around each centroid.
                (width, height) = img.size[:2]
                out_img = Image.new('RGB', (width, height))
                out_img.paste(img)
                img_draw = ImageDraw.Draw(out_img)
                for cent in centroids:
                    draw_circle(img_draw, cent, 4, outline=(64, 64, 255))

                # Here you can add e.g. `fov_estimate`/`fov_max_error` to improve speed or a
                # `distortion` range to search (default assumes undistorted image). There
                # are many optional returns, e.g. `return_matches` or `return_visual`.
                if len(centroids) == 0:
                    print('No stars found, skipping')
                else:
                    # Generally 30 centroids is more than enough for Tetra3 to find a
                    # solution. Passing additional centroids just slows solve_from_centroids()
                    # down somewhat.
                    trimmed_centroids = centroids[:30]
                    solution = t3.solve_from_centroids(
                        trimmed_centroids, (height, width),
                        return_matches=False, return_catalog=False,
                        solve_timeout=5000, distortion=0)

                    if 'matched_centroids' in solution:
                        # Draw a green box around each matched star.
                        for cent in solution['matched_centroids']:
                            draw_box(img_draw, cent, 7, outline=(32, 192, 32))
                        # Draw a red box around each pattern star.
                        for cent in solution['pattern_centroids']:
                            draw_box(img_draw, cent, 7, outline=(192, 32, 32))

                    if 'catalog_stars' in solution:
                        # Draw a yellow box around each catalog star.
                        for star in solution['catalog_stars']:
                            # star is (RA, Dec, mag, y, x).
                            draw_box(img_draw, [star[3], star[4]], 5, outline=(192, 192, 32))

                    # Don't clutter printed solution with these fields.
                    solution.pop('matched_centroids', None)
                    solution.pop('catalog_stars', None)
                    solution.pop('matched_stars', None)
                    solution.pop('matched_catID', None)
                    solution.pop('pattern_centroids', None)
                    solution.pop('epoch_equinox', None)
                    solution.pop('epoch_proper_motion', None)
                    print('Solution %s' % solution)

                name, ext = os.path.splitext(basename)
                out_img.save(os.path.join(path, "output", name + ".bmp"))

        except IsADirectoryError:
            pass  # Skip the output directory.
finally:
    if USE_CEDAR_DETECT:
        del cedar_detect
