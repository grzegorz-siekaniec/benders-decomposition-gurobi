import numpy as np
from . import model_build_utils
import gurobi as grb


def is_non_zero(var):
    return np.abs(var) > 0.0001


sc = grb.StatusConstClass
status_code_to_string = {
    sc.__dict__[k]: k
    for k in sc.__dict__.keys()
    if k[0] >= 'A' and k[0] <= 'Z'
}


def get_status(status: int) -> str:
    return status_code_to_string[status]