from src.graph.graph import RoadGraph
from src.models import Emergency,Hospital
from src.optimization.hospital_selector import HospitalSelector
def test_full_hospital_excluded():
 g=RoadGraph();g.add_edge("A","H1",1,1,"R1");g.add_edge("A","H2",2,2,"R2");hs=[Hospital("H1","H1","Full",10,0,"high",True),Hospital("H2","H2","Available",10,5,"high",True)];s,_=HospitalSelector().select(g,Emergency("E","A","critical",10,"ICU"),hs);assert s.hospital.hospital_id=="H2"
