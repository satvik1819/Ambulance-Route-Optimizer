from dataclasses import dataclass
from typing import Literal
Severity=Literal["low","medium","high","critical"]
@dataclass(frozen=True)
class Hospital:
    hospital_id:str; node_id:str; name:str; available_beds:int; emergency_beds:int; emergency_capacity:str; operational:bool
@dataclass(frozen=True)
class Emergency:
    case_id:str; ambulance_node:str; severity:Severity; severity_score:int; required_service:str
@dataclass(frozen=True)
class RouteResult:
    source:str; destination:str; path:tuple[str,...]; total_distance_km:float; total_time_min:float; nodes_explored:int; algorithm:str; reachable:bool=True; message:str=""
