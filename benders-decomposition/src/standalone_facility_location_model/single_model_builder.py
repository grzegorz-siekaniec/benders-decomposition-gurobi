from typing import Tuple, Dict

from input import InputData
import gurobi as grb
from bidict import bidict

from utils.model_build_utils import build_facility_columns, build_transport_columns, build_supply_constraints, \
    build_demand_constraints
from .single_model import SingleModel


class SingleModelBuilder(object):

    def __init__(self, data: InputData):
        self.data = data

        self.model = grb.Model("facility_location_single_model")

        self.facility_name_to_column: Dict[str, grb.Var] = None
        self.facility_customer_to_column: Dict[Tuple[str, str], grb.Var] = None

    def build(self):

        self._build_columns()
        self._build_constraints()
        self.model.update()

        facility_name_to_column = bidict(self.facility_name_to_column)
        facility_customer_to_column = bidict(self.facility_customer_to_column)

        return SingleModel(self.model, facility_name_to_column, facility_customer_to_column)

    def _build_constraints(self):
        build_supply_constraints(self.data, self.model, self.facility_customer_to_column, self.facility_name_to_column)
        build_demand_constraints(self.data, self.model, self.facility_customer_to_column)

    def _build_columns(self):
        self.facility_name_to_column = build_facility_columns(self.data, self.model)
        self.facility_customer_to_column = build_transport_columns(self.data, self.model)
