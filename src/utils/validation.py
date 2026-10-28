from pathlib import Path
import pandas as pd
REQ=["nodes.csv","roads.csv","hospitals.csv","emergency_cases.csv","traffic_conditions.csv","incidents.csv"]
def validate_dataset(data_dir):
    p=Path(data_dir);errors=[];counts={}
    for f in REQ:
        q=p/f
        if not q.exists():errors.append(f"Missing file: {f}")
        else:counts[f]=len(pd.read_csv(q))
    if errors:return {"valid":False,"errors":errors,"counts":counts}
    n=pd.read_csv(p/'nodes.csv');r=pd.read_csv(p/'roads.csv');h=pd.read_csv(p/'hospitals.csv');e=pd.read_csv(p/'emergency_cases.csv');t=pd.read_csv(p/'traffic_conditions.csv');i=pd.read_csv(p/'incidents.csv')
    ids=set(n.node_id);rids=set(r.road_id)
    if (~r.source.isin(ids)|~r.target.isin(ids)).any():errors.append("Invalid road endpoint")
    if not h.node_id.isin(ids).all():errors.append("Invalid hospital node")
    if not e.ambulance_node.isin(ids).all():errors.append("Invalid emergency node")
    if not t.road_id.isin(rids).all():errors.append("Invalid traffic road")
    if not i.road_id.isin(rids).all():errors.append("Invalid incident road")
    if n.node_id.duplicated().any():errors.append("Duplicate node IDs")
    if r.road_id.duplicated().any():errors.append("Duplicate road IDs")
    return {"valid":not errors,"errors":errors,"counts":counts}
