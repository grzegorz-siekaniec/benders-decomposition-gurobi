from typing import Dict, Tuple

import gurobi as grb

from input import InputData


def build_transport_columns(data: InputData, model: grb.Model) -> Dict[Tuple[str, str], grb.Var]:
    facility_customer_to_column: Dict[Tuple[str, str], grb.Var] = dict()

    lb = 0.0
    ub = grb.GRB.INFINITY

    for facility in data.facilities:
        for customer_name, unit_transport_cost in facility.transport_cost.items():
            name = f'x_{facility.name}_{customer_name}'
            var = model.addVar(
                lb=lb,
                ub=ub,
                obj=unit_transport_cost,
                vtype=grb.GRB.CONTINUOUS,
                name=name,
                column=None
            )
            facility_customer_to_column[(facility.name, customer_name)] = var

    return facility_customer_to_column


def build_facility_columns(data: InputData, model: grb.Model) -> Dict[str, grb.Var]:
    facility_name_to_column: Dict[str, grb.Var] = dict()

    for facility in data.facilities:

        name = f'facility_{facility.name}'
        lb, obj = (0.0, facility.build_cost) if not facility.exists else (1.0, 0)
        var = model.addVar(
            lb=lb,
            ub=1.0,
            obj=obj,
            vtype=grb.GRB.BINARY,
            name=name
        )

        facility_name_to_column[facility.name] = var

    return facility_name_to_column


def build_supply_constraints(data: InputData,
                             model: grb.Model,
                             facility_customer_to_column: Dict[Tuple[str, str], grb.Var],
                             facility_name_to_column: Dict[str, grb.Var]) -> None:

    for facility in data.facilities:
        lhs = [
            facility_customer_to_column[(facility.name, customer_name)]
            for customer_name in facility.transport_cost.keys()
        ]
        lhs.append(-1 * facility.supply * facility_name_to_column[facility.name])
        lhs = grb.quicksum(lhs)
        name = f'supply_{facility.name}'

        model.addConstr(lhs <= 0.0, name=name)


def build_demand_constraints(data: InputData,
                             model: grb.Model,
                             facility_customer_to_column: Dict[Tuple[str, str], grb.Var]) -> None:

    for customer in data.customers:
        lhs = grb.quicksum([
            facility_customer_to_column[(facility.name, customer.name)]
            for facility in data.facilities]
        )
        rhs = customer.demand
        name = f'demand_{customer.name}'
        _row = model.addConstr(lhs >= rhs, name=name)