import logging

import gurobi as grb

from .sub_problem import SubProblem

from input import InputData
from utils.model_build_utils import build_transport_columns, build_supply_constraints, build_demand_constraints


class SubProblemBuilder(object):

    def __init__(self, data: InputData):
        self.data = data

    def build(self):

        try:
            model = grb.Model("facility_location_sub_problem")

            facility_customer_pair_to_column \
                = build_transport_columns(self.data, model)

            facility_to_supply_constraint \
                = build_supply_constraints(self.data, model, facility_customer_pair_to_column, dict())

            customer_to_demand_constraint \
                = build_demand_constraints(self.data, model, facility_customer_pair_to_column)

            model.setParam(grb.GRB.Param.InfUnbdInfo, 1)
            model.update()
            return SubProblem(model,
                              facility_customer_pair_to_column,
                              facility_to_supply_constraint,
                              customer_to_demand_constraint)

        except grb.GurobiError as ex:
            logging.exception("Gurobi %r" % ex)
        except Exception as ex:
            logging.exception(ex)
        return None
