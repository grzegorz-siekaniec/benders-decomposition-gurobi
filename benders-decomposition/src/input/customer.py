from dataclasses import dataclass


@dataclass
class Customer:
    name: str
    demand: float