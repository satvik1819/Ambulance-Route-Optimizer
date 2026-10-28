from src.graph.graph import RoadGraph
from src.algorithms.dijkstra import dijkstra
def test_shortest_path():
 g=RoadGraph();g.add_edge("A","B",1,1,"R1");g.add_edge("B","C",1,1,"R2");g.add_edge("A","C",5,5,"R3");r=dijkstra(g,"A","C");assert r.path==("A","B","C") and r.total_time_min==2
