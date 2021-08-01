import logging
import sys
import argparse

import gurobi as grb

from input import InputData
from benders_decomposition.solver import solve_using_benders_decomposition
from standalone_facility_location_model import solve_using_standalone_model


def main():
    try:
        fm_with_date = '%(asctime)s %(levelname)s: %(message)s'
        fmt_basic = '%(message)s'
        logging.basicConfig(format=fmt_basic,
                            datefmt='%Y/%m/%d %I:%M:%S %p',
                            level=logging.INFO)

        parser = argparse.ArgumentParser(description="Solves warehouse location problem.")
        parser.add_argument('input_data',
                            help='Path to JSON file containing input data.')

        parser.add_argument('--method',
                            choices=['standalone', 'benders_decomposition', 'both'],
                            default='both',
                            help='A method that should be used to solve a problem. default=both.')
        args = parser.parse_args()

        # solving facility problem
        input_data = InputData.read(args.input_data)
        use_standalone_model = args.method in {'standalone', 'both'}
        use_benders_decomposition = args.method in {'benders_decomposition', 'both'}

        if use_standalone_model:
            solve_using_standalone_model(input_data)
        if use_benders_decomposition:
            solve_using_benders_decomposition(input_data)

    except argparse.ArgumentError:
        logging.exception('Exception raised during parsing arguments')
        sys.exit(2)
    except grb.GurobiError:
        logging.exception("Gurobi exception thrown")
        sys.exit(1)
    except Exception:
        logging.exception("Exception occurred")
        sys.exit(1)


if __name__ == '__main__':
    main()
