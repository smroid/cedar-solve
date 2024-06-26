Migrating from Tetra3 to Cedar-Solve
====================================

An existing application that uses Tetra3 can easily migrate to use Cedar Solve
instead, as the calling API is the same between the two.

Consider the program::

  from tetra3 import Tetra3

  ...
  t3 = Tetra3('default_database')

  ... # obtain image
  solve_dict = t3.solve_from_image(image, fov_estimate=12.0)
  ...

To switch to Cedar-solve, update your PYTHONPATH. For example, if you
cloned the `cedar-solve repo <https://github.com/smroid/cedar-solve>`_
to /home/pi/projects/cedar-solve, then set::

  export PYTHONPATH=/home/pi/projects/cedar-solve/tetra3

Now when you run your program, you'll get the Cedar-solve variant of Tetra3.

Advantages of Cedar-Solve
-------------------------

Cedar-solve has many improvements:

* Faster solve times.

* More uniform solve times.

* Uniform sky coverage and pattern density in database. This reduces
  the occurrences of solve failures.

* Smaller database file and in-memory footprint.

* The 'pattern_checking_stars' argument to solve_from_image() is no
  longer needed.


Replacing Tetra's star detection/centroiding with Cedar-Detect
==============================================================

While migrating to Cedar-solve offers the advantages outlined above,
adopting Cedar-detect for star detection and centroiding can further
improve overall plate solving performance. Cedar-detect is:

* Much faster than Tetra3's build-in star detection/centroiding.

* More resistant to false positives. Tetra3 often finds lots of false
  stars in illuminated foreground clutter, but Cedar-detect generally
  finds only real stars in the sky.

As a first step to switching to Cedar-detect, we first update our
application to split out the star centroiding from the plate solving::

  from tetra3 import Tetra3

  ...
  t3 = Tetra3('default_database')

  ... # obtain image
  centroids = t3.get_centroids_from_image(image)
  solve_dict = t3.solve_from_centroids(centroids, fov_estimate=12.0)
  ...

Next, clone the `cedar-detect repo <https://github.com/smroid/cedar-detect>`_.

You will need to build the Cedar-detect executable, so first install Rust
using instructions at `https://www.rust-lang.org/tools/install`.

Go to your clone of the cedar-detect repo, and build optimized::

  cargo build --release

Now copy the executable into your cedar-solve directory::

  cp /home/pi/projects/cedar-detect/target/release/cedar-detect-server \
    /home/pi/projects/cedar-solve/tetra3/bin

Update your application::

  from tetra3 import Tetra3, cedar_detect_client

  ...
  t3 = Tetra3('default_database')
  cedar_detect = cedar_detect_client.CedarDetectClient()

  ... # obtain image
  centroids = cedar_detect.extract_centroids(
    image, sigma=8, max_size=10, use_binned=True)
  solve_dict = t3.solve_from_centroids(centroids, fov_estimate=12.0)
  ...

Done!
