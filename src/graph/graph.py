from dataclasses import dataclass
@dataclass(frozen=True)
class Edge:
    target:str; distance_km:float; travel_time_min:float; road_id:str
class RoadGraph:
    def __init__(self): self._adj={}
    def add_node(self,n): self._adj.setdefault(n,[])
    @property
    def nodes(self): return tuple(self._adj)
    def neighbors(self,n): return tuple(self._adj.get(n,()))
    def add_edge(self,a,b,d,t,r,bidirectional=True):
        self.add_node(a); self.add_node(b); self._adj[a].append(Edge(b,d,t,r))
        if bidirectional:self._adj[b].append(Edge(a,d,t,r))
    def remove_roads(self,blocked):
        g=RoadGraph()
        for n in self.nodes:g.add_node(n)
        for a in self.nodes:
            for e in self.neighbors(a):
                if e.road_id not in blocked:g.add_edge(a,e.target,e.distance_km,e.travel_time_min,e.road_id,False)
        return g
