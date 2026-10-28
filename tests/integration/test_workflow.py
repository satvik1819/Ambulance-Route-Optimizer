from src.services.application import AmbulanceOptimizer
def test_workflow():
 a=AmbulanceOptimizer("data/raw");e,s,c=a.optimize("E000001");assert e.case_id=="E000001" and s is not None and len(c)>0
