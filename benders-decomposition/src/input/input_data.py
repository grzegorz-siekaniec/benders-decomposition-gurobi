import json
from typing import List

from .customer import Customer
from .facility import Facility


class InputData(object):

    def __init__(self, facilities: List[Facility], customers: List[Customer]):

        self.facilities = facilities
        self.customers = customers

    @staticmethod
    def read(fn: str):

        with open(fn) as f:
            data = json.load(f)

        facilities = []
        for facility_data in data["facilities"]:
            transport_cost_data = facility_data["transportCost"]
            transport_cost = {
                tc["customer"]: tc["cost"] for tc in transport_cost_data
            }

            facility = Facility(
                name=facility_data["name"],
                exists=facility_data.get("exists", False),
                build_cost=facility_data.get("buildCost"),
                supply=facility_data["supply"],
                transport_cost=transport_cost
            )

            facilities.append(facility)

        customers = [Customer(name=customer_data["name"],demand=customer_data["demand"])
                     for customer_data in data["customers"]]

        return InputData(facilities=facilities, customers=customers)
