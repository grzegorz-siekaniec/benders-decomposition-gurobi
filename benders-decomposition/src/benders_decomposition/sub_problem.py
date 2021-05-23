import logging
from typing import Dict, Tuple

import gurobi as grb


class SubProblem(object):

    def __init__(self,
                 model: grb.Model,
                 facility_customer_pair_to_column: Dict[Tuple[str, str], grb.Var],
                 facility_to_supply_constraint: Dict[str, grb.Constr],
                 customer_to_demand_constraint: Dict[str, grb.Constr]):
        self.model = model
        self.facility_customer_pair_to_column = facility_customer_pair_to_column
        self.facility_to_supply_constraint = facility_to_supply_constraint
        self.customer_to_demand_constraint = customer_to_demand_constraint

        self.count = 1

    def set_supply_constraint_rhs(self, rhs_map):
        for location, val in rhs_map.items():
            self.facility_to_supply_constraint[location].setAttr(grb.GRB.Attr.RHS, val)

    def solve(self):
        logging.info("Solving subproblem")
        self.model.optimize()

    def status(self):
        return self.model.status

    def write(self):
        self.model.update()
        self.model.write(f'subproblem_{self.count}.lp')
        self.count += 1