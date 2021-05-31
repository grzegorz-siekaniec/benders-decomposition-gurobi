import logging
from typing import Optional, Dict, Tuple

import gurobi as grb

from input import InputData
from utils.model_build_utils import build_facility_columns
from .master_problem import MasterProblem


class MasterProblemBuilder:

    def __init__(self, data: InputData):
        self.data = data
        self.name_to_column = dict()
        self.model = grb.Model("facility_location_master_problem")
        self.aux_var_name = 'z'

    def build(self) -> Optional[MasterProblem]:
        try:
            self._build_model()
            self.model.Params.PreCrush = 1
            self.model.Params.lazyConstraints = 1
            # use bidict here!
            return MasterProblem(self.model, self.name_to_column, self.aux_var_name)
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

    def _build_aux_column(self) -> Tuple[str, grb.Var]:
        lb = 0.0
        ub = grb.GRB.INFINITY
        name = self.aux_var_name
        obj = 1.0
        var = self.model.addVar(
            lb=lb,
            ub=ub,
            obj=obj,
            vtype=grb.GRB.CONTINUOUS,
            name=name
        )
        return name, var
