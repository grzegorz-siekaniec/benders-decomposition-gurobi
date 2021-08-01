import logging
from typing import Dict, Union
from timeit import default_timer as timer

import gurobi as grb

import utils
from benders_decomposition.master_problem import MasterProblem
from benders_decomposition.master_problem_builder import MasterProblemBuilder
from benders_decomposition.sub_problem import SubProblem
from benders_decomposition.sub_problem_builder import SubProblemBuilder
from input import InputData


def solve_using_benders_decomposition(input_data: InputData):
    s = timer()
    logging.info("[START] Solving warehouse location problem using Benders Decomposition.")

    master_problem = MasterProblemBuilder(input_data).build()
    sub_problem = SubProblemBuilder(input_data).build()

    mapping = create_sub_problem_constraint_to_master_column_or_value_map(master_problem, sub_problem, input_data)

    master_problem.register_callback(cb_benders(master_problem, sub_problem, mapping, input_data))
    master_problem.solve()
    master_problem.report_results()

    logging.info("[END] Solving warehouse location problem using Benders Decomposition."
                 "It took %f sec.", timer() - s)


def create_sub_problem_constraint_to_master_column_or_value_map(master: MasterProblem,
                                                                sub_problem: SubProblem,
                                                                data: InputData)\
        -> Dict[grb.Constr, Union[grb.Var, float]]:
    """
    Creates a mapping between sub-problem constraint and components of (b - By).
    :param master: instance of MasterProblem
    :param sub_problem: instance of Subproblem
    :param data: input data
    :return: dictionary with mapping
    """
    mapping = dict()
    for facility_name, row in sub_problem.facility_to_supply_constraint.items():
        mapping[row] = -data.supply(facility_name) * master.name_to_column[facility_name]

    for customer_name, row in sub_problem.customer_to_demand_constraint.items():
        mapping[row] = row.getAttr(grb.GRB.Attr.RHS)

    return mapping


def cb_benders(master: MasterProblem,
               sub_problem: SubProblem,
               mapping: Dict[grb.Constr, Union[grb.Var, float]],
               data: InputData):
    """
    Benders Decomposition callback
    :param master: instance of MasterProblem
    :param sub_problem: instance of SubProblem
    :param mapping: mapping between sub-problem constraint and and components of (b - By) vector.
    :param data: input data
    :return: inner callback function.
    """
    def callback_inner(model, where):

        if where == grb.GRB.Callback.MIPSOL:

            # Update sub-problem's RHS based on incumbent solution
            facility_cols = list(master.facility_to_column.values())
            mp_facility_values = model.cbGetSolution(facility_cols)
            facility_names = master.facility_to_column.keys()

            sub_problem_rhs = {facility_name: -data.supply(facility_name) if utils.is_non_zero(val) else 0.0
                               for facility_name, val in zip(facility_names, mp_facility_values)}

            sub_problem.set_supply_constraint_rhs(sub_problem_rhs)

            # Solve sub-problem
            sub_problem.solve()

            logging.debug(f'Subproblem status: {sub_problem.model.getAttr(grb.GRB.Attr.Status)}')

            # Add cuts (lazy constraints) based on sub-problem status
            if sub_problem.status() == grb.GRB.Status.INFEASIBLE:

                # Add feasibility cut
                cut = []
                for facility_name, row in sub_problem.facility_to_supply_constraint.items():
                    dual_farkas = row.getAttr(grb.GRB.Attr.FarkasDual)
                    logging.debug(f'{facility_name}: {dual_farkas}')
                    cut.append(dual_farkas * mapping[row])

                for customer_name, row in sub_problem.customer_to_demand_constraint.items():
                    dual_farkas = row.getAttr(grb.GRB.Attr.FarkasDual)
                    logging.debug(f'{customer_name}: {dual_farkas}')
                    cut.append(dual_farkas * mapping[row])

                logging.debug("Adding feasibility cut: ", grb.quicksum(cut) >= 0)
                model.cbLazy(grb.quicksum(cut) >= 0)

            elif sub_problem.status() == grb.GRB.Status.OPTIMAL:
                sub_problem_obj_val = sub_problem.model.getAttr(grb.GRB.Attr.ObjVal)
                z = master.name_to_column[master.aux_var_name]
                z_val = model.cbGetSolution(z)
                if utils.is_non_zero(sub_problem_obj_val - z_val):

                    # Add optimality cut
                    cut = []
                    for _, row in sub_problem.facility_to_supply_constraint.items():
                        dual_supply = row.getAttr(grb.GRB.Attr.Pi)
                        cut.append(dual_supply * mapping[row])
                    for _, row in sub_problem.customer_to_demand_constraint.items():
                        dual_demand = row.getAttr(grb.GRB.Attr.Pi)
                        cut.append(dual_demand * mapping[row])

                    cut.append(-z)
                    model.cbLazy(grb.quicksum(cut) <= 0)
                    logging.debug("Adding optimality cut: ", grb.quicksum(cut) <= 0)

    return callback_inner
