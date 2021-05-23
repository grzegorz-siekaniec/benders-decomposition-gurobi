import logging
from typing import Dict, Union

import gurobi as grb

import utils
from benders_decomposition.master_problem import MasterProblem
from benders_decomposition.master_problem_builder import MasterProblemBuilder
from benders_decomposition.sub_problem import SubProblem
from benders_decomposition.sub_problem_builder import SubProblemBuilder
from input import InputData


def solve_facility_problem_benders(data: InputData):
    grb.setParam(grb.GRB.Param.OutputFlag, 0)
    master_problem = MasterProblemBuilder(data).build()
    sub_problem = SubProblemBuilder(data).build()

    rhs = create_sub_problem_constraint_to_master_column_map(master_problem, sub_problem, data)

    master_problem.register_callback(cb_benders(master_problem, sub_problem, rhs, data))
    master_problem.solve()
    master_problem.report_results()


def create_sub_problem_constraint_to_master_column_map(master: MasterProblem,
                                                       sub_problem: SubProblem,
                                                       data: InputData)\
        -> Dict[grb.Constr, Union[grb.Var, float]]:
    rhs = dict()
    for facility_name, row in sub_problem.facility_to_supply_constraint.items():
        rhs[row] = data.supply(facility_name) * master.name_to_column[facility_name]

    for customer_name, row in sub_problem.customer_to_demand_constraint.items():
        rhs[row] = row.getAttr(grb.GRB.Attr.RHS)

    return rhs


def cb_benders(master: MasterProblem,
               subproblem: SubProblem,
               subproblem_constraints_to_master_columns: Dict[grb.Constr, Union[grb.Var, float]],
               data: InputData):
    """
    Benders Decomposition callback
    :param master:
    :param subproblem:
    :param subproblem_constraints_to_master_columns: holds (b - By) mapping
    :param data: input data
    :return:
    """
    def callback_inner(model, where):

        if where == grb.GRB.Callback.MIPSOL:

            # Update sub-problem's RHS based on incumbent solution
            facility_cols = list(master.facility_to_column.values())
            mp_facility_values = model.cbGetSolution(facility_cols)
            facility_names = master.facility_to_column.keys()

            sub_problem_rhs = {facility_name: data.supply(facility_name) if utils.is_non_zero(val) else 0.0
                               for facility_name, val in zip(facility_names, mp_facility_values)}

            subproblem.set_supply_constraint_rhs(sub_problem_rhs)

            # Solve sub-problem
            subproblem.solve()

            logging.info(f'Subproblem status: {subproblem.model.getAttr(grb.GRB.Attr.Status)}')

            # Add cuts (lazy constraints) based on sub-problem status
            if subproblem.status() == grb.GRB.Status.INFEASIBLE:

                # Add feasibility cut
                cut = []
                for facility_name, row in subproblem.facility_to_supply_constraint.items():
                    dual_farkas = row.getAttr(grb.GRB.Attr.FarkasDual)
                    logging.debug(f'{facility_name}: {dual_farkas}')
                    cut.append(dual_farkas * subproblem_constraints_to_master_columns[row])

                for customer_name, row in subproblem.customer_to_demand_constraint.items():
                    dual_farkas = row.getAttr(grb.GRB.Attr.FarkasDual)
                    logging.debug(f'{customer_name}: {dual_farkas}')
                    cut.append(dual_farkas * subproblem_constraints_to_master_columns[row])

                logging.debug("Adding lazy constraint: ", grb.quicksum(cut) >= 0)
                model.cbLazy(grb.quicksum(cut) >= 0)

            elif subproblem.status() == grb.GRB.Status.OPTIMAL:
                sub_problem_obj_val = subproblem.model.getAttr(grb.GRB.Attr.ObjVal)
                z = master.name_to_column[master.aux_var_name]
                z_val = model.cbGetSolution(z)
                if utils.is_non_zero(sub_problem_obj_val - z_val):

                    # Add optimality cut
                    cut = []
                    for _, row in subproblem.facility_to_supply_constraint.items():
                        dual_supply = row.getAttr(grb.GRB.Attr.Pi)
                        cut.append(dual_supply * subproblem_constraints_to_master_columns[row])
                    for _, row in subproblem.customer_to_demand_constraint.items():
                        dual_demand = row.getAttr(grb.GRB.Attr.Pi)
                        cut.append(dual_demand * subproblem_constraints_to_master_columns[row])

                    cut.append(-z)
                    model.cbLazy(grb.quicksum(cut) <= 0)
                    logging.debug("Adding lazy constraint: ", grb.quicksum(cut) <= 0)

    return callback_inner
