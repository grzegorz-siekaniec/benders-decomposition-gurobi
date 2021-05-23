import logging
from typing import Dict, Callable, List

import gurobi as grb

import utils


class MasterProblem:

    def __init__(self, model: grb.Model, name_to_column: Dict[str, grb.Var], aux_var_name: str):
        self.model = model
        self.name_to_column = name_to_column
        self.facility_to_column = dict(name_to_column)
        self.facility_to_column.pop(aux_var_name)

        self.cb: Callable = None
        self.aux_var_name = aux_var_name
        self.count = 1

    def register_callback(self, cb: Callable):
        self.cb = cb

    def solve(self):
        self.model.optimize(self.cb)

    def write(self):
        self.model.update()
        self.model.write(f'master_{self.count}.lp')
        self.count += 1

    def report_results(self):

        obj_val = self.model.getAttr(grb.GRB.Attr.ObjVal)
        logging.info("Final results using Benders!")
        logging.info("--------------")
        logging.info(f"Objective value: {obj_val}")
        logging.info("The facilities at the following locations should be built:")
        for var in self.model.getVars():
            if utils.is_non_zero(var.x):
                facility_name = var.varName
                if facility_name:
                    logging.info(f"   {facility_name} ... {var.x}")