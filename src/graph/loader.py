from pathlib import Path
import pandas as pd
from .graph import RoadGraph
from src.models import Hospital,Emergency
class DatasetLoader:
    def __init__(self,data_dir):self.data_dir=Path(data_dir)
    def load_graph(self):
        nodes=pd.read_csv(self.data_dir/'nodes.csv'); roads=pd.read_csv(self.data_dir/'roads.csv'); g=RoadGraph()
        for n in nodes.node_id:g.add_node(str(n))
        for r in roads.itertuples(index=False):
            if str(r.status).lower()=="open":g.add_edge(str(r.source),str(r.target),float(r.distance_km),float(r.base_travel_time_min),str(r.road_id))
        return g
    def load_hospitals(self):
        d=pd.read_csv(self.data_dir/'hospitals.csv'); return [Hospital(str(r.hospital_id),str(r.node_id),str(r.hospital_name),int(r.available_beds),int(r.emergency_beds),str(r.emergency_capacity),bool(r.operational)) for r in d.itertuples(index=False)]
    def load_emergencies(self):
        d=pd.read_csv(self.data_dir/'emergency_cases.csv'); return [Emergency(str(r.case_id),str(r.ambulance_node),str(r.severity),int(r.severity_score),str(r.required_service)) for r in d.itertuples(index=False)]
