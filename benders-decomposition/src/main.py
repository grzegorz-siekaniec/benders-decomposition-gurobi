import logging
import sys

import gurobi as grb

from input import InputData
from benders_decomposition.solver import solve_using_benders_decomposition
from standalone_facility_location_model import solve_using_standalone_model


def main():

    try:
        input_data = InputData.read(
            r'/home/gsiekaniec/git_repos/personal/operations-research/benders-decomposition-gurobi/benders-decomposition/data/rk_martin_ex_10_8.json')

        fm_with_date = '%(asctime)s %(levelname)s: %(message)s'
        fmt_basic = '%(message)s'
        logging.basicConfig(format=fmt_basic,
                            datefmt='%Y/%m/%d %I:%M:%S %p',
                            level=logging.INFO)
        # solving facility problem

        solve_using_standalone_model(input_data)
        solve_using_benders_decomposition(input_data)

    except grb.GurobiError:
        logging.exception("Gurobi exception thrown")
        sys.exit(1)
    except Exception:
        logging.exception("Exception occurred")
        sys.exit(1)


if __name__ == '__main__':
    main()
