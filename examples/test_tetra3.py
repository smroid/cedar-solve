"""
This example loads the tetra3 default database and solves for every image in the
tetra3/examples/data/medium_fov directory.
"""

import os
import sys
sys.path.append('..')

import numpy as np
from PIL import Image, ImageDraw
from pathlib import Path
from time import perf_counter as precision_timestamp
EXAMPLES_DIR = Path(__file__).parent

import cedar_detect_client
import tetra3

def draw_circle(img_draw, centre, radius, **kwargs):
    bbox = [centre[1] - radius, centre[0] - radius, centre[1] + radius, centre[0] + radius]
    img_draw.ellipse(bbox, **kwargs)

def draw_box(img_draw, centre, radius, **kwargs):
    bbox = [centre[1] - radius, centre[0] - radius, centre[1] + radius, centre[0] + radius]
    img_draw.rectangle(bbox, **kwargs)

# Create instance and load the default database, built for 30 to 10 degree field of view.
# Pass `load_database=None` to not load a database (e.g. to build your own; see
# generate_database.py example script).
t3 = tetra3.Tetra3(load_database='default_database')

# Select method used for star detection and centroiding. True for cedar-detect,
# False for Tetra3.
USE_CEDAR_DETECT = True

if USE_CEDAR_DETECT:
    cedar_detect = cedar_detect_client.CedarDetectClient(
        binary_path='../tetra3/bin/cedar-detect-server')

# Path where images are
path = EXAMPLES_DIR / 'data' / 'medium_fov'
try:
    for impath in path.glob('*'):
        try:
            with Image.open(str(impath)) as img:
                img = img.convert(mode='L')
                np_image = np.asarray(img, dtype=np.uint8)

                t0 = precision_timestamp()
                if USE_CEDAR_DETECT:
                    centroids = cedar_detect.extract_centroids(np_image, sigma=8, max_size=8, use_binned=True)
                else:
                    centroids = tetra3.get_centroids_from_image(np_image)
                t_extract = (precision_timestamp() - t0)*1000

                basename = os.path.basename(impath)
                print('File %s, extracted %d centroids in %.2fms' % (basename, len(centroids), t_extract))

                # Draw a small blue circle around each centroid.
                (width, height) = img.size[:2]
                out_img = Image.new('RGB', (width, height))
                out_img.paste(img)
                img_draw = ImageDraw.Draw(out_img)
                for cent in centroids:
                    draw_circle(img_draw, cent, 3, outline=(64, 64, 255))

                # Here you can add e.g. `fov_estimate`/`fov_max_error` to improve speed or a
                # `distortion` range to search (default assumes undistorted image). There
                # are many optional returns, e.g. `return_matches` or `return_visual`.
                if len(centroids) == 0:
                    print('No stars found, skipping')
                else:
                    solution = t3.solve_from_centroids(
                        centroids, (height, width), fov_estimate=None, match_max_error=.005,
                        return_matches=True, solve_timeout=1000)

                    if 'matched_centroids' in solution:
                        # Draw a green box around each matched star.
                        for cent in solution['matched_centroids']:
                            draw_box(img_draw, cent, 5, outline=(32, 128, 32))
                        # Overdraw a red box around each pattern star.
                        for cent in solution['pattern_centroids']:
                            draw_box(img_draw, cent, 5, outline=(128, 32, 32))

                        # Don't clutter printed solution with these fields.
                        del solution['matched_centroids']
                        del solution['matched_stars']
                        del solution['matched_catID']
                        del solution['pattern_centroids']
                        del solution['pattern_stars']
                        del solution['pattern_catID']
                        del solution['epoch_equinox']
                        del solution['epoch_proper_motion']
                        del solution['cache_hit_fraction']

                    print('Solution %s' % solution)

                name, ext = os.path.splitext(basename)
                out_img.save(os.path.join(path, "output", name + ".bmp"))

        except IsADirectoryError:
            pass  # Skip the output directory.
finally:
    if USE_CEDAR_DETECT:
        del cedar_detect
