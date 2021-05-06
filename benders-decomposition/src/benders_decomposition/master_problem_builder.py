import logging
from typing import Optional, Dict, Tuple

import gurobi as grb

from input import InputData
from utils.model_build_utils import build_facility_columns
from .master_problem import MasterProblem


class MasterProblemBuilder(object):

    def __init__(self, data: InputData):
        self.data = data
        self.columns = {}
        self.name_to_column = dict()
        self.model = grb.Model("facility_location_master_problem")
        self.facility_columns = []

    def build(self) -> Optional[MasterProblem]:
        try:
            self._build_model()
            self.model.Params.PreCrush = 1
            self.model.Params.lazyConstraints = 1
            return MasterProblem(self.model, self.columns, self.facility_columns)
        except grb.GurobiError as ex:
            logging.exception("Gurobi %r" % ex)
        except Exception as ex:
            logging.exception(ex)
        return None

    def _build_model(self) -> None:
        self._build_columns()

    def _build_columns(self) -> None:

        facility_to_column = build_facility_columns(self.data, self.model)
        name, var = self._build_aux_column()

        self.name_to_column.update(facility_to_column)
        self.name_to_column[name] = var

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

            self.columns[facility.name] = var
            self.facility_columns.append(var)

    def _build_aux_column(self) -> Tuple[str, grb.Var]:
        lb = 0.0
        ub = grb.GRB.INFINITY
        name = 'z'
        obj = 1.0
        var = self.model.addVar(
            lb=lb,
            ub=ub,
            obj=obj,
            vtype=grb.GRB.CONTINUOUS,
            name=name
        )
        return name, var
