from dataclasses import dataclass


@dataclass(frozen=True)
class Customer:
    name: str
    demand: float
