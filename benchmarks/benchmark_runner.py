from pathlib import Path
import time,csv
from src.services.application import AmbulanceOptimizer
a=AmbulanceOptimizer(Path(__file__).parents[1]/'data/raw');rows=[]
for n in [10,50,100,250,500]:
 t=time.perf_counter();ok=0
 for e in a.emergencies[:n]:
  s,_=a.selector.select(a.graph,e,a.hospitals);ok+=s is not None
 sec=time.perf_counter()-t;rows.append((n,sec,ok))
out=Path(__file__).parent/'results/routing_benchmark.csv';out.parent.mkdir(parents=True,exist_ok=True)
with out.open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['cases','seconds','successful_cases']);w.writerows(rows)
print(out)
