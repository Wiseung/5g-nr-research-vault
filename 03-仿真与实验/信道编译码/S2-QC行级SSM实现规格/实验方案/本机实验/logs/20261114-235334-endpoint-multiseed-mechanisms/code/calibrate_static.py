"""Validation-only static damping calibration, frozen before static test."""
import gc,json
import numpy as np
import torch
from endpoint import (PLAN,OUT,LOG,load,Engine,evaluate_point,save_json,immutable,emit,
                      frozen_config,NRLink,configure,assert_sources)
configure();assert_sources()
gate=load(LOG/"mechanism_verification.json");assert gate["status"]=="passed"
registry={"cohort":"static-controls","configs":{}}
for c in PLAN["configs"]:
    cid=c["config_id"];f,cfg=frozen_config(PLAN["frozen_inputs"],cid);link=NRLink(cfg)
    root=OUT/"static-calibration"/cid;ranking=[]
    for i in range(11):
        eta=i/20
        spec={"name":f"eta-{eta:.2f}","kind":"static","alpha":c["alpha"],"eta":eta}
        engine=Engine(link,None,c["alpha"],eta)
        points=[evaluate_point(root/"20k"/spec["name"],link,[spec],[engine],"S2-formal-validation-v1",snr,20000) for snr in f["validation_snr_db"]]
        ranking.append({"eta":eta,"mean_bler":float(np.mean([p["methods"][0]["payload_bler"] for p in points]))})
        del engine;gc.collect();torch.cuda.empty_cache()
    ranking.sort(key=lambda r:(r["mean_bler"],r["eta"]))
    immutable(root/"top2_frozen.json",{"top2":ranking[:2],"ranking":ranking,"rule":"mean payloadBLER then eta ascending;T20 fixed"})
    expanded=[]
    for row in ranking[:2]:
        spec={"name":f"eta-{row['eta']:.2f}","kind":"static","alpha":c["alpha"],"eta":row["eta"]}
        engine=Engine(link,None,c["alpha"],row["eta"])
        points=[evaluate_point(root/"100k"/spec["name"],link,[spec],[engine],"S2-formal-validation-v1",snr,100000) for snr in f["validation_snr_db"]]
        # Every extension retains exactly the prefix used for candidate ranking.
        for snr in f["validation_snr_db"]:
            for sh in range(32):
                a=root/"20k"/spec["name"]/f"snr-{snr:.4f}"/f"shard-{sh:02d}.npz"
                b=root/"100k"/spec["name"]/f"snr-{snr:.4f}"/f"shard-{sh:02d}.npz"
                with np.load(a,allow_pickle=False) as x,np.load(b,allow_pickle=False) as y:
                    for key in ["bit_errors","rejected","crc_ok","bce"]:assert np.array_equal(x[key],y[key][:,:625])
        expanded.append({"eta":row["eta"],"mean_bler":float(np.mean([p["methods"][0]["payload_bler"] for p in points]))})
        del engine;gc.collect();torch.cuda.empty_cache()
    expanded.sort(key=lambda r:(r["mean_bler"],r["eta"]))
    immutable(root/"selection.json",{"status":"passed","selected":expanded[0],"candidates":expanded,"test_access":False})
    registry["configs"][cid]=[{"name":"NMS","kind":"nms","alpha":c["alpha"]},
        {"name":"static-tuned","kind":"static","alpha":c["alpha"],"eta":expanded[0]["eta"]},
        {"name":"static-initial-eta005","kind":"static","alpha":c["alpha"],"eta":.05}]
    emit("static_selected",config=cid,selected=expanded[0])
    del link;gc.collect();torch.cuda.empty_cache()
immutable(OUT/"static_registry.json",registry)
save_json(OUT/"static-calibration/summary.json",{"status":"passed","registry":registry})

