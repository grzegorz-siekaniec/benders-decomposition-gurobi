from dataclasses import dataclass
from typing import Dict


@dataclass
class Facility:
    name: str
    exists: bool
    build_cost: float
    supply: float
    transport_cost: Dict[str, float]