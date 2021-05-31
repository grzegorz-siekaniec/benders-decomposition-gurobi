import logging
from timeit import default_timer as timer

from input import InputData
from standalone_facility_location_model import SingleModelBuilder


def solve_using_standalone_model(input_data: InputData):
    s = timer()
    logging.info("[START] solving warehouse location problem using standalone model.")

    single_model = SingleModelBuilder(input_data).build()
    single_model.write()
    single_model.solve()
    single_model.report_results()

    e = timer()
    logging.info("[END] solving warehouse location problem using standalone model."
                 "It took %f sec.", e - s)
