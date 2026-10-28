import heapq
from math import inf
from src.models import RouteResult
def dijkstra(graph,source,destination):
    if source not in graph.nodes or destination not in graph.nodes:return RouteResult(source,destination,(),0,0,0,"Dijkstra",False,"Unknown node.")
    dist={source:0.0}; prev={}; heap=[(0.0,source)]; explored=0
    while heap:
        cur,node=heapq.heappop(heap)
        if cur!=dist.get(node,inf):continue
        explored+=1
        if node==destination:break
        for e in graph.neighbors(node):
            nd=cur+e.travel_time_min
            if nd<dist.get(e.target,inf):dist[e.target]=nd;prev[e.target]=(node,e);heapq.heappush(heap,(nd,e.target))
    if destination not in dist:return RouteResult(source,destination,(),0,0,explored,"Dijkstra",False,"Destination is unreachable.")
    path=[];distance=0.0;n=destination
    while n!=source:path.append(n);p,e=prev[n];distance+=e.distance_km;n=p
    path.append(source);path.reverse()
    return RouteResult(source,destination,tuple(path),round(distance,3),round(dist[destination],3),explored,"Dijkstra")
