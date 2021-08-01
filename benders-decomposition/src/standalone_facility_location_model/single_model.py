import logging
from typing import Tuple

import gurobi as grb
from bidict import bidict

from utils import is_non_zero


class SingleModel:

    def __init__(self,
                 model: grb.Model,
                 facility_name_to_column: bidict[str, grb.Var],
                 facility_customer_to_column: bidict[Tuple[str, str], grb.Var]):

        self.model = model
        self.facility_name_to_column = facility_name_to_column
        self.facility_customer_to_column = facility_customer_to_column

    def solve(self):
        self.model.optimize()

    def write(self):
        self.model.update()
        model_name = self.model.getAttr(grb.GRB.Attr.ModelName)
        self.model.write(f'{model_name}.lp')

    def report_results(self):
        obj_val = self.model.getAttr(grb.GRB.Attr.ObjVal)

        logging.info("** Final results using standalone model! **")
        logging.info("Objective value: %f", obj_val)
        logging.info("The facilities at the following locations should be built:")
        for var in self.model.getVars():
            if is_non_zero(var.x):
                facility_name = self.facility_name_to_column.inverse.get(var)
                if facility_name:
                    logging.info("    %s", facility_name)