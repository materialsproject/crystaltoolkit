import numpy as np

from fractions import Fraction


def pretty_frac_format(x):
    x = x % 1
    fraction = Fraction(x).limit_denominator(8)
    if np.allclose(x, 1):
        x_str = "0"
    elif not np.allclose(x, float(fraction)):
        x = np.around(x, decimals=3)
        x_str = f"{x:.3g}"
    else:
        x_str = str(fraction)
    return x_str
