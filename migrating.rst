Migrating from Tetra3 to Cedar-Solve
====================================

An existing application that uses Tetra3 can easily migrate to use Cedar Solve
instead, as the calling API is the same between the two.

Consider the program::

  from tetra3 import Tetra3

  ...
  t3 = Tetra3('default_database')
  ...
  solve_dict = t3.solve_from_image(img, fov_estimate=12.0)
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

