from dataclasses import dataclass
from datetime import date

@dataclass
class Experiment:
    name       : str
    researcher : str
    parameter  : str
    result     : float
    date       : date
