import numpy as np

from fractions import Fraction


def pretty_float_format(x):
    fraction = Fraction(x).limit_denominator(8)
    if not np.allclose(x, float(fraction)):
        x_str = f"{x:.3g}"
    else:
        x_str = str(fraction)
    return x_str
