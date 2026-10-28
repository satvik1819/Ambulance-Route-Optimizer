from dataclasses import dataclass
from src.algorithms.dijkstra import dijkstra
@dataclass(frozen=True)
class HospitalCandidate:
    hospital:object; travel_time_min:float; distance_km:float; route:tuple[str,...]; score:float
class HospitalSelector:
    def __init__(self,weights=None):self.weights=weights or {"travel_time":.5,"capacity":.2,"availability":.2,"emergency_capability":.1}
    def select(self,graph,emergency,hospitals):
        out=[]
        for h in hospitals:
            if not h.operational or h.emergency_beds<=0:continue
            r=dijkstra(graph,emergency.ambulance_node,h.node_id)
            if not r.reachable:continue
            ts=1/(1+r.total_time_min/10); cs=min(h.available_beds/30,1); av=min(h.emergency_beds/10,1)
            cap=1 if h.emergency_capacity=="high" else .6 if h.emergency_capacity=="medium" else .4
            s=self.weights["travel_time"]*ts+self.weights["capacity"]*cs+self.weights["availability"]*av+self.weights["emergency_capability"]*cap
            out.append(HospitalCandidate(h,r.total_time_min,r.total_distance_km,r.path,round(s,6)))
        out.sort(key=lambda x:(-x.score,x.travel_time_min));return (out[0] if out else None,out)
