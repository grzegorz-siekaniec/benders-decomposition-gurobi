from typing import Tuple, Dict

from input import InputData
import gurobi as grb
from bidict import bidict

from .single_model import SingleModel


class SingleModelBuilder(object):

    def __init__(self, data: InputData):
        self.data = data

        self.model = grb.Model("facility_location_single_model")
        #self.facility_name_to_column: bidict[str, grb.Var] = bidict()
        self.facility_name_to_column: Dict[str, grb.Var] = dict()
        self.facility_customer_to_column: Dict[Tuple[str, str], grb.Var] = dict()

    def build(self):

        self._build_columns()
        self._build_constraints()
        self.model.update()

        facility_name_to_column = bidict(self.facility_name_to_column)
        facility_customer_to_column = bidict(self.facility_customer_to_column)

        return SingleModel(self.model, facility_name_to_column, facility_customer_to_column)

    def _build_facility_columns(self):

        for facility in self.data.facilities:

            # facility already exists
            name = f'facility_{facility.name}'
            lb, obj = (0.0, facility.build_cost) if not facility.exists else (1.0, 0)
            var = self.model.addVar(
                lb=lb,
                ub=1.0,
                obj=obj,
                vtype=grb.GRB.BINARY,
                name=name
            )

            self.facility_name_to_column[facility.name] = var

    def _build_transport_columns(self):

        lb = 0.0
        ub = grb.GRB.INFINITY

        for facility in self.data.facilities:
            for customer_name, unit_transport_cost in facility.transport_cost.items():
                name = f'x_{facility.name}_{customer_name}'
                var = self.model.addVar(
                    lb=lb,
                    ub=ub,
                    obj=unit_transport_cost,
                    vtype=grb.GRB.CONTINUOUS,
                    name=name,
                    column=None
                )
                self.facility_customer_to_column[(facility.name, customer_name)] = var

    def _build_constraints(self):
        # supply
        for facility in self.data.facilities:
            lhs = [
                self.facility_customer_to_column[(facility.name, customer_name)]
                for customer_name in facility.transport_cost.keys()
            ]
            lhs.append(-1 * facility.supply * self.facility_name_to_column[facility.name])
            lhs = grb.quicksum(lhs)
            name = f'supply_{facility.name}'

            self.model.addConstr(lhs <= 0.0, name=name)

        # demand
        for customer in self.data.customers:
            lhs = grb.quicksum([
                self.facility_customer_to_column[(facility.name, customer.name)]
                for facility in self.data.facilities]
            )
            rhs = customer.demand
            name = f'demand_{customer.name}'
            _row = self.model.addConstr(lhs >= rhs, name=name)

    def _build_columns(self):
        self._build_facility_columns()
        self._build_transport_columns()
