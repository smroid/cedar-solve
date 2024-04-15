import math
import numpy as np

def separation_for_density(fov, stars_per_fov):
    """Compute minimum separation, in same units as 'fov', for achieving the desired star
    density.
    fov: horizontal field of view.
    stars_per_fov: desired number of stars in field of view
    """
    return .6 * fov / np.sqrt(stars_per_fov)

def num_fields_for_sky(fov):
    """For a given square field of view (in radians), computes how many such
    fields of view are needed to cover the entire sky, by area.
    """
    return math.ceil(4 * math.pi / (fov * fov))

def fibonacci_sphere_lattice(n):
    """Yields the 2*n+1 points of a Fibonacci lattice of the sphere.
    Returned points are (x, y, z) unit vectors.
    See "Measurement of areas on a sphere using Fibonacci and
    latitude-longitude lattices" by Alvaro Gonzalez, at
    https://arxiv.org/pdf/0912.4540.pdf.
    """
    phi = (1 + math.sqrt(5)) / 2  # Golden ratio ~1.618
    golden_angle_incr = 2 * math.pi * (1 - 1 / phi)  # radians
    for i in range(-n, n+1):
        z = i / (n + 0.5)  # Ranges over (-1..1).
        radius = math.sqrt(1 - z * z)  # Distance from axis at z.
        theta = golden_angle_incr * i
        x = math.cos(theta) * radius
        y = math.sin(theta) * radius
        yield (x, y, z)
