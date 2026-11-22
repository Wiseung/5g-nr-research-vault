"""Protocol-v1 fixed-N NMS-F20 pilot and alpha calibration (never trains)."""
import argparse
import gc
import hashlib
import json
from pathlib import Path
import sys
import time
import traceback

import numpy as np
import torch
from torch.nn import functional as F

from nr_link import NRLink, sha256
from run_local import ROOT, dump, emit, environment, rng_for
from protocol_checks import wilson, zero_error_upper, log_bler_crossing

CONFIGS = ("ldpc_B1024_R1-2_Q2", "ldpc_B4096_R1-2_Q2")
ALPHAS = [round(0.60 + 0.05 * i, 2) for i in range(9)]
GRID = [float(x) for x in np.arange(-2, 8.01, .5)]


def nms20(link, lch, alpha):
    """Identical eta=0 update; omit statistics used only by the controller."""
    u = lch
    r = lch.new_zeros((len(lch), link.p, link.z))
    for _ in range(20):
        q = (link.gather(u) - r).clamp(-20, 20)
        q = q.masked_fill(~link.edge_nonfiller.bool(), 20)
        r = (alpha * link.minsum(q)).clamp(-20, 20)
        u = (lch + link.scatter(r)).masked_fill(link.filler, 20)
    return u.clamp(-20, 20)


class GraphNMS:
    """Replay the same FP32 operators at a fixed batch shape, no early stop."""
    def __init__(self, link, batch):
        self.batch = batch
        self.input = torch.zeros((batch, link.n), device=link.device)
        self.input[:, link.filler] = 20
        self.alpha = torch.tensor(.8, device=link.device)
        stream = torch.cuda.Stream()
        stream.wait_stream(torch.cuda.current_stream())
        with torch.cuda.stream(stream), torch.no_grad():
            for _ in range(2):
                nms20(link, self.input, self.alpha)
        torch.cuda.current_stream().wait_stream(stream)
        torch.cuda.synchronize()
        self.graph = torch.cuda.CUDAGraph()
        with torch.no_grad(), torch.cuda.graph(self.graph):
            self.output = nms20(link, self.input, self.alpha)
        torch.cuda.synchronize()

    def __call__(self, lch, alpha):
        assert len(lch) <= self.batch and lch.dtype == torch.float32
        self.input[:len(lch)].copy_(lch)
        self.alpha.fill_(alpha)
        self.graph.replay()
        return self.output[:len(lch)]


def shard_samples(link, split, snr, shard, count):
    bits = rng_for(link.cfg["id"], split, snr, shard, "bits")
    noise = rng_for(link.cfg["id"], split, snr, shard, "noise")
    payload = bits.integers(0, 2, (count, link.a), dtype=np.uint8)
    cw, info = link.encode(payload)
    lch, _ = link.channel(cw, float(snr), noise)
    return payload, cw, info, lch


def verify(out, manifest, batch):
    rows = []
    for cfg in [c for c in manifest["ldpc_configs"] if c["id"] in CONFIGS]:
        link = NRLink(cfg)
        payload, cw, info, random = shard_samples(link, "20261113-fast-nms-verification", 1.25, 0, 16)
        clean, _ = link.channel(cw, 0., np.random.default_rng(23), noiseless=True)
        zero = torch.zeros_like(random).masked_fill(link.filler, 20)
        saturated = (random * 8).clamp(-20, 20).masked_fill(link.filler, 20)
        worst = 0.
        for name, data in (("random", random), ("zero", zero), ("saturated", saturated), ("noiseless", clean)):
            for alpha in ALPHAS:
                expected = link.decode(data, alpha=alpha)[0]
                actual = nms20(link, data, alpha)
                error = float((actual - expected).abs().max())
                assert error == 0, (cfg["id"], name, alpha, error)
                assert torch.equal(actual < 0, expected < 0)
                worst = max(worst, error)
        graph = GraphNMS(link, batch)
        for alpha in ALPHAS:
            expected = link.decode(random, alpha=alpha)[0]
            actual = graph(random, alpha)
            error = float((actual - expected).abs().max())
            assert error == 0, (cfg["id"], "graph", alpha, error)
        chunked = torch.cat([nms20(link, random[i:i+4], .8) for i in range(0, 16, 4)])
        assert torch.equal(chunked, nms20(link, random, .8)), "batch shape changed NMS results"
        # Prefix identity is essential when top2 are extended from20k to100k.
        small = shard_samples(link, "20261113-prefix-verification", 1.25, 0, 625)
        large = shard_samples(link, "20261113-prefix-verification", 1.25, 0, 3125)
        assert all(np.array_equal(small[i], large[i][:625]) for i in range(3))
        assert torch.equal(small[3], large[3][:625]), "noise/sample prefix mismatch"
        start = time.perf_counter()
        data = large[3][:batch]
        for _ in range(3):
            graph(data, .8)
        torch.cuda.synchronize()
        seconds = (time.perf_counter() - start) / 3
        row = {"config_id": cfg["id"], "alphas": ALPHAS, "input_cases": 4,
               "original_vs_simplified_max_abs_error": worst,
               "CUDA_graph_max_abs_error": 0., "chunk_identity": True,
               "prefix_625_of_3125_identity": True, "batch": batch,
               "inference_seconds_per_batch": seconds,
               "peak_allocated_bytes": torch.cuda.max_memory_allocated(),
               "peak_reserved_bytes": torch.cuda.max_memory_reserved()}
        rows.append(row)
        emit(out, "verified", **row)
        del graph, link, small, large, random, clean, zero, saturated, chunked, data
        gc.collect()
        torch.cuda.empty_cache()
    dump(out / "summary.json", {"status": "passed", "checks": rows, "source_sha256": sha256(Path(__file__))})


def counts(wrong, bit_errors, rejected):
    n = wrong.size
    e = int(wrong.sum())
    result = {"frames": n, "payload_frame_errors": e, "payload_bit_errors": int(bit_errors.sum()),
              "rejected": int(rejected.sum()), "service_frame_errors": int((wrong | rejected).sum()),
              "accepted_wrong": int((wrong & ~rejected).sum()),
              "bler": e / n, "bler_ci95": wilson(e, n), "mean_iterations": 20}
    if e == 0:
        result["zero_error_one_sided95_upper"] = zero_error_upper(n)
    return result


def point(link, graph, out, split, snr, alphas, extension=False):
    stage = "extension" if extension else "initial"
    directory = out / split / link.cfg["id"]
    directory.mkdir(parents=True, exist_ok=True)
    stem = f"snr-{snr:+.4f}-{stage}-alphas-" + "_".join(f"{a:.2f}" for a in alphas)
    summary_path = directory / (stem + ".json")
    if summary_path.exists():
        saved = json.loads(summary_path.read_text())
        assert sha256(directory / saved["raw_npz"]) == saved["raw_sha256"]
        return saved
    per_shard = 2500 if extension else 625
    total_generated = 3125 if extension else 625
    shape = (len(alphas), 32, per_shard)
    wrong = np.zeros(shape, dtype=bool)
    rejected = np.zeros(shape, dtype=bool)
    bit_errors = np.zeros(shape, dtype=np.uint16)
    bce = np.zeros(shape, dtype=np.float32)
    sample_hash = []
    started = time.perf_counter()
    for shard in range(32):
        payload, cw, info, lch = shard_samples(link, split, snr, shard, total_generated)
        digest = hashlib.sha256(payload[:625].tobytes() + lch[:625].cpu().numpy().tobytes()).hexdigest()
        sample_hash.append(digest)
        offset = 625 if extension else 0
        for begin in range(offset, total_generated, graph.batch):
            end = min(total_generated, begin + graph.batch)
            a, b = begin-offset, end-offset
            labels = torch.tensor(info[begin:end], device=link.device, dtype=torch.float32)
            for ai, alpha in enumerate(alphas):
                u = graph(lch[begin:end], alpha)
                diff = (u[:, :link.a] < 0).cpu().numpy() != payload[begin:end]
                wrong[ai, shard, a:b] = diff.any(1)
                bit_errors[ai, shard, a:b] = diff.sum(1)
                rejected[ai, shard, a:b] = (~link.accepted(u)).cpu().numpy()
                bce[ai, shard, a:b] = F.binary_cross_entropy_with_logits(-u[:, :link.b], labels,
                                                                       reduction="none").mean(1).cpu().numpy()
        if (shard + 1) % 8 == 0:
            emit(out, "point_progress", config=link.cfg["id"], split=split, snr_db=snr,
                 alphas=alphas, completed_shards=shard+1, seconds=time.perf_counter()-started)
    npz_path = directory / (stem + ".npz")
    np.savez_compressed(npz_path, payload_frame_error=wrong, payload_bit_errors=bit_errors,
                        rejected=rejected, information_bce=bce)
    summaries = []
    for ai, alpha in enumerate(alphas):
        row = {"alpha": alpha, **counts(wrong[ai], bit_errors[ai], rejected[ai]),
               "information_bce": float(bce[ai].mean(dtype=np.float64)),
               "shards": [{"shard": sh, **counts(wrong[ai,sh], bit_errors[ai,sh], rejected[ai,sh])}
                          for sh in range(32)]}
        summaries.append(row)
    result = {"config_id": link.cfg["id"], "split": split, "snr_db": snr,
              "stage": stage, "alphas": alphas, "results": summaries,
              "sample_prefix625_sha256_per_shard": sample_hash,
              "sample_offset_per_shard": offset, "frames_per_shard": per_shard,
              "raw_npz": npz_path.name, "raw_sha256": sha256(npz_path),
              "seconds": time.perf_counter()-started, "index_sha256": link.index_hash,
              "shift_sha256": link.shift_hash}
    dump(summary_path, result)
    emit(out, "point_completed", config=link.cfg["id"], split=split, snr_db=snr,
         seconds=result["seconds"], counts=[{k:v for k,v in r.items() if k!="shards"} for r in summaries])
    return result


def crossing(points):
    pairs = [(p["snr_db"], p["results"][0]["bler"]) for p in points]
    gamma = log_bler_crossing(pairs, .01)
    if gamma is None:
        return None
    rng = np.random.default_rng(21261113)
    boots = []
    for _ in range(2000):
        sampled = []
        for p in points:
            ids = rng.integers(0,32,32)
            shards = p["results"][0]["shards"]
            sampled.append((p["snr_db"], sum(shards[int(i)]["payload_frame_errors"] for i in ids)/20000))
        value = log_bler_crossing(sampled,.01)
        if value is not None:
            boots.append(value)
    return {"gamma_ref_db": gamma, "training_snr_range_db": [gamma-1.5,gamma+1.],
            "validation_snr_db": [round(float(x),4) for x in np.linspace(gamma-1.5,gamma+1.,5)],
            "descriptive_shard_bootstrap95_db": np.quantile(boots,[.025,.975]).tolist(),
            "bootstrap_valid": len(boots), "bootstrap_total": 2000, "target_BLER": .01}


def run_pilot(link, graph, out, split, alpha):
    points = [point(link,graph,out,split,snr,[alpha]) for snr in GRID]
    while crossing(points) is None:
        lower,upper = min(p["snr_db"] for p in points),max(p["snr_db"] for p in points)
        # A zero-error upper point cannot enter log(BLER). Refine its bracket,
        # rather than adding ever-higher zero points or inserting pseudocounts.
        zero_bracket=next(((a,b) for a,b in zip(points,points[1:])
                          if a['results'][0]['bler']>=.01 and b['results'][0]['bler']==0),None)
        if zero_bracket is not None:
            a,b=zero_bracket
            snr=round((a['snr_db']+b['snr_db'])/2,4)
            assert a['snr_db']<snr<b['snr_db'],'pilot grid refinement exhausted4-decimal key resolution'
        elif points[0]["results"][0]["bler"] < .01:
            snr=lower-.5
        else:
            snr=upper+.5
        points.append(point(link,graph,out,split,snr,[alpha]))
        points.sort(key=lambda p:p["snr_db"])
        assert len(points)<80,"pilot expansion failed to bracket crossing"
    result={"alpha":alpha,"split":split,"points":points,**crossing(points)}
    dump(out/split/link.cfg["id"]/"pilot_summary.json",result)
    emit(out,"pilot_completed",config=link.cfg["id"],alpha=alpha,split=split,**crossing(points))
    return result


def calibrate(link,graph,out,pilot):
    split="20261113-alpha-validation"
    snrs=pilot["validation_snr_db"]
    initial=[point(link,graph,out,split,snr,ALPHAS) for snr in snrs]
    ranking=sorted([{"alpha":alpha,"mean_bler":float(np.mean([p["results"][ai]["bler"] for p in initial])),
                     "mean_iterations":20} for ai,alpha in enumerate(ALPHAS)],
                   key=lambda r:(r["mean_bler"],r["mean_iterations"],r["alpha"]))
    top=[r["alpha"] for r in ranking[:2]]
    dump(out/split/link.cfg["id"]/"top2_frozen.json",{"initial_ranking":ranking,"top2":top})
    extension=[point(link,graph,out,split,snr,top,True) for snr in snrs]
    combined=[]
    for ai,alpha in enumerate(top):
        pi=ALPHAS.index(alpha)
        points=[]
        for p,e in zip(initial,extension):
            assert p["sample_prefix625_sha256_per_shard"]==e["sample_prefix625_sha256_per_shard"]
            a,b=p["results"][pi],e["results"][ai]
            keys=("frames","payload_frame_errors","payload_bit_errors","rejected","service_frame_errors","accepted_wrong")
            row={k:a[k]+b[k] for k in keys}
            row.update(snr_db=p["snr_db"],bler=row["payload_frame_errors"]/row["frames"],
                       bler_ci95=wilson(row["payload_frame_errors"],row["frames"]),mean_iterations=20)
            if row["payload_frame_errors"]==0:row["zero_error_one_sided95_upper"]=zero_error_upper(row["frames"])
            points.append(row)
        combined.append({"alpha":alpha,"points":points,"mean_bler":float(np.mean([r["bler"] for r in points])),"mean_iterations":20})
    combined.sort(key=lambda r:(r["mean_bler"],r["mean_iterations"],r["alpha"]))
    result={"split":split,"snr_db":snrs,"initial_ranking":ranking,"top2_100k":combined,
            "frozen_alpha":combined[0]["alpha"],"not_test_set":True}
    dump(out/split/link.cfg["id"]/"calibration_summary.json",result)
    emit(out,"alpha_frozen",config=link.cfg["id"],**result)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode",choices=("verify","run"),required=True)
    parser.add_argument("--output",required=True)
    parser.add_argument("--verification")
    parser.add_argument("--batch",type=int,default=625)
    parser.add_argument("--resume",action="store_true")
    args=parser.parse_args()
    assert args.batch>0 and 625%args.batch==0
    out=Path(args.output).resolve()
    out.mkdir(parents=True,exist_ok=True)
    if any(out.iterdir()) and not args.resume:parser.error("output must be empty (or explicit --resume)")
    torch.set_num_threads(4)
    torch.backends.cuda.matmul.allow_tf32=False
    torch.backends.cudnn.allow_tf32=False
    torch.manual_seed(17)
    manifest=json.loads((ROOT.parent/"experiment_manifest.json").read_text())
    try:
        env=environment(out,args)
        env["source_sha256"][str(Path(__file__).resolve())]=sha256(Path(__file__))
        dump(out/"environment.json",env)
        with torch.no_grad():
            if args.mode=="verify":
                verify(out,manifest,args.batch)
                return
            gate=json.loads(Path(args.verification).read_text())
            assert gate["status"]=="passed" and gate["source_sha256"]==sha256(Path(__file__)),"verification missing or source changed"
            frozen=[]
            for cid in CONFIGS:
                link=NRLink(next(c for c in manifest["ldpc_configs"] if c["id"]==cid))
                graph=GraphNMS(link,args.batch)
                pilot=run_pilot(link,graph,out,"20261113-pilot-initial",.8)
                alpha=calibrate(link,graph,out,pilot)
                final=(pilot if alpha["frozen_alpha"]==.8 else
                       run_pilot(link,graph,out,"20261113-pilot-final",alpha["frozen_alpha"]))
                frozen.append({"config_id":cid,"alpha":alpha["frozen_alpha"],
                               "alpha_calibration":alpha,"initial_pilot":pilot,"final_pilot":final})
                dump(out/"frozen_configs.json",frozen)
                del graph,link
                gc.collect();torch.cuda.empty_cache()
            dump(out/"summary.json",{"status":"completed","formal_training":False,"configs":frozen})
            emit(out,"completed",configs=[{k:v for k,v in c.items() if k in ("config_id","alpha")} for c in frozen])
    except Exception as exc:
        dump(out/"failure.json",{"error":repr(exc),"traceback":traceback.format_exc()})
        raise


if __name__=="__main__":
    main()
