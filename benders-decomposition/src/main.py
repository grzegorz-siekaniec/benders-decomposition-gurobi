import logging
import sys

import gurobi as grb

from benders_decomposition.solver import solve_facility_problem_benders
from input import InputData
from standalone_facility_location_model import SingleModelBuilder

# http://people.brunel.ac.uk/~mastjjb/jeb/orlib/files/cap41.txt


def main(argv=None):

    try:
        input = InputData.read(
            r'/home/gsiekaniec/git_repos/personal/operations-research/benders-decomposition-gurobi/benders-decomposition/data/rk_martin_ex_10_8.json')

        fm_with_date = '%(asctime)s %(levelname)s: %(message)s'
        fmt_basic = '%(message)s'
        logging.basicConfig(format=fmt_basic,
                            datefmt='%Y/%m/%d %I:%M:%S %p',
                            level=logging.INFO)

        single_model = SingleModelBuilder(input).build()
        single_model.write()
        single_model.solve()
        single_model.report_results()

        solve_facility_problem_benders(input)

    except grb.GurobiError as ex:
        logging.exception("Gurobi exception thrown")
    except Exception as ex:
        logging.exception("Exception occurred")
        sys.exit(1)


if __name__ == '__main__':
    main()
