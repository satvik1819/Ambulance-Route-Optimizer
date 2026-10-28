from pathlib import Path
import pandas as pd
from src.graph.loader import DatasetLoader
from src.optimization.hospital_selector import HospitalSelector
from src.optimization.rerouting import reroute
class AmbulanceOptimizer:
    def __init__(self,data_dir):
        self.data_dir=Path(data_dir);self.loader=DatasetLoader(self.data_dir);self.graph=self.loader.load_graph();self.hospitals=self.loader.load_hospitals();self.emergencies=self.loader.load_emergencies();self.selector=HospitalSelector();self.incidents=pd.read_csv(self.data_dir/'incidents.csv')
    def get_emergency(self,case_id):
        for e in self.emergencies:
            if e.case_id==case_id:return e
        raise ValueError(f"Emergency case not found: {case_id}")
    def optimize(self,case_id):
        e=self.get_emergency(case_id);return e,*self.selector.select(self.graph,e,self.hospitals)
    def reroute_for_incident(self,case_id,incident_id):
        e,selected,_=self.optimize(case_id)
        if selected is None:raise ValueError("No suitable hospital is available.")
        row=self.incidents[self.incidents.incident_id.astype(str)==str(incident_id)]
        if row.empty:raise ValueError(f"Incident not found: {incident_id}")
        r=reroute(self.graph,e.ambulance_node,selected.hospital.node_id,{str(row.iloc[0].road_id)})
        return e,selected,r
