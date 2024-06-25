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

blah
