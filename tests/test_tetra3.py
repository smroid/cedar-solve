from pathlib import Path

from PIL import Image

import tetra3


def test_solve_for_image_examples(test_data_dir: Path):
    """ this example test runs the solver on a few images """
    t3 = tetra3.Tetra3()

    for image_path in (test_data_dir / "example_images").glob("*"):
        with Image.open(image_path) as img:
            solution = t3.solve_from_image(img, distortion=[-0.2, 0.1])
            assert solution["Matches"] > 0
