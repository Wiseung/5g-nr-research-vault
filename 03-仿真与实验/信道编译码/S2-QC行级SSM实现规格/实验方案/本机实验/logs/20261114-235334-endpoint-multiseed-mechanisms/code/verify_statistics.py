"""CPU checks: known paired log crossing, strict zero-error boundary, interval numerics."""
import math,json
from scipy.stats import binomtest
from endpoint import PLAN,LOG,statistics,save_json
from protocol_checks import log_bler_crossing,wilson,zero_error_upper
methods=[{"name":"NMS"},{"name":"S2"}]
points=[]
for snr,counts in [(1.,[20,10]),(2.,[2,1])]:
    points.append({"identity":{"snr_db":snr},"methods":[{"payload_bler":n/6250} for n in counts],
                   "shards":[{"methods":[{"payload_frame_errors":n,"frames":6250} for n in counts]} for _ in range(32)]})
s=statistics(points,methods)
expected_nms=1+math.log10(3.2)
assert abs(s["methods"][0]["crossing_db"]-expected_nms)<1e-12
assert abs(s["methods"][1]["gain_vs_NMS_db"]-math.log10(2))<1e-12
assert all(abs(x-math.log10(2))<1e-12 for x in s["methods"][1]["gain_ci95_db"])
for p in points:
    if p["identity"]["snr_db"]==2:
        p["methods"][1]["payload_bler"]=0.
        for sh in p["shards"]:sh["methods"][1]["payload_frame_errors"]=0
z=statistics(points,methods)
assert z["methods"][1]["crossing_db"] is None and z["methods"][1]["bootstrap_valid"]==0 and z["methods"][1]["gain_ci95_db"] is None
for n,e in [(20000,20),(200000,200),(200000,0),(200000,200000)]:
    ref=binomtest(e,n).proportion_ci(method="wilson");a,b=wilson(e,n)
    assert abs(a-ref.low)<2e-12 and abs(b-ref.high)<2e-12
assert abs(zero_error_upper(200000)-(1-.05**(1/200000)))<1e-15
result={"status":"passed","paired_known_gain_db":math.log10(2),"zero_upper_crossing":"N/A without pseudocount","Wilson_independent_Scipy":"passed","bootstrap_replicates":PLAN["test"]["bootstrap_replicates"]}
save_json(LOG/"statistics_verification.json",result);print(json.dumps(result))

