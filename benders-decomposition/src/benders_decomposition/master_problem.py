from typing import Dict, Callable, List

import gurobi as grb


class MasterProblem(object):

    def __init__(self, model: grb.Model, name_to_column: Dict[str, grb.Var], facility_columns: List):
        self.model = model
        self.name_to_column = name_to_column
        self.facility_columns = facility_columns
        self.cb: Callable = None
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
        pass