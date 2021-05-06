import numpy as np
from . import model_build_utils


def is_non_zero(var):
    return np.abs(var) > 0.0001
