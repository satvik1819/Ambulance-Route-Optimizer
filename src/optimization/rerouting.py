from src.algorithms.dijkstra import dijkstra
def reroute(graph,source,destination,blocked_roads):return dijkstra(graph.remove_roads(blocked_roads),source,destination)
