from typing import Dict

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

    master_problem.write()
    sub_problem.write()

    rhs = create_rhs_map(master_problem, sub_problem, data)
    master_problem.register_callback(cb_benders(master_problem, sub_problem, rhs, data))
    master_problem.solve()
    master_problem.write()
    master_problem.report_results()


def cb_benders(master: MasterProblem,
               subproblem: SubProblem,
               subproblem_constraints_to_master_columns: Dict,
               data: InputData):

    def callback_inner(model, where):

        if where == grb.GRB.Callback.MIPSOL:

            vals = model.cbGetSolution(master.facility_columns)
            names = list(subproblem.supply_constraints.keys())
            assert(len(vals) == len(names))
            subproblem_rhs = {name: data.supply(name) if is_non_zero(val) else 0.0 for name, val in zip(names, vals)}
            print(dict(zip(names, vals)))
            subproblem.set_supply_constraint_rhs(subproblem_rhs)
            #subproblem.write()
            subproblem.solve()
            print(f'Subproblem status: {subproblem.model.getAttr("status")}')
            cut = []
            if subproblem.status() == grb.GRB.Status.INFEASIBLE:
                for name, row in subproblem.supply_constraints.items():
                    dual_farkas = row.getAttr("FarkasDual")
                    print(f'{name}: {dual_farkas}')
                    cut.append(dual_farkas * subproblem_constraints_to_master_columns[row])

                for name, row in subproblem.demand_constraints.items():
                    dual_farkas = row.getAttr("FarkasDual")
                    print(f'{name}: {dual_farkas}')
                    cut.append(dual_farkas * subproblem_constraints_to_master_columns[row])

                logging.info("Adding lazy constraint: ", grb.quicksum(cut) >= 0)
                model.cbLazy(grb.quicksum(cut) >= 0)

            elif subproblem.status() == grb.GRB.Status.OPTIMAL:
                subproblem_objval = subproblem.model.getAttr("ObjVal")
                z = master.columns['z']
                z_val = model.cbGetSolution(z)
                if utils.is_non_zero(subproblem_objval - z_val):
                    # add optimality cut

                    cut = []
                    for name, row in subproblem.supply_constraints.items():
                        dual_supply = row.getAttr("Pi")
                        cut.append(dual_supply * subproblem_constraints_to_master_columns[row])
                    for name, row in subproblem.demand_constraints.items():
                        dual_demand = row.getAttr("Pi")
                        cut.append(dual_demand * subproblem_constraints_to_master_columns[row])

                    cut.append(-z)
                    model.cbLazy(grb.quicksum(cut) <= 0)
                    print("Adding lazy constraint: ", grb.quicksum(cut) >= 0)

    return callback_inner