"""Local first-stage experiments. Never starts the 50k-step training job."""
import argparse
from datetime import datetime
import hashlib
import importlib.metadata
import inspect
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback
from zoneinfo import ZoneInfo

import numpy as np
import torch
from sionna.phy.fec.ldpc import LDPC5GEncoder, LDPC5GDecoder

sys.dont_write_bytecode = True

from nr_link import NRLink, crc_attach, sha256
from ssm import RowSSM, training_loss

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))
sys.path.insert(0, str(ROOT.parent.parent))
from generate_manifest import build, stable_seed
from protocol_checks import self_check, wilson, zero_error_upper
from budget_and_invariants import check_invariants


def dump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def emit(out, event, **data):
    record = {"time": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(), "event": event, **data}
    with (out / "events.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(json.dumps(record, ensure_ascii=False), flush=True)


def environment(out, args):
    packages = {p: importlib.metadata.version(p) for p in
                ("torch", "numpy", "scipy", "sionna", "py3gpp")}
    source_paths = [ROOT / name for name in ("nr_link.py", "ssm.py", "run_local.py")]
    source_paths += [ROOT.parent / "experiment_manifest.json", ROOT.parent / "README.md",
                     ROOT.parent.parent / "README.md", Path(inspect.getfile(LDPC5GEncoder)),
                     Path(inspect.getfile(LDPC5GDecoder))]
    result = {"python": sys.version, "executable": sys.executable, "platform": platform.platform(),
              "packages": packages, "cuda": torch.version.cuda,
              "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
              "tf32": False, "amp": False, "dtype": "float32", "args": vars(args),
              "pid": os.getpid(), "rng": "NumPy PCG64; independent bits/noise subkeys",
              "source_sha256": {str(p): sha256(p) for p in source_paths},
              "gpu_rankings": "none; engineering validation on local GPU only"}
    result["nvidia_smi"] = subprocess.check_output(
        ["nvidia-smi", "--query-gpu=index,uuid,name,driver_version,memory.used,memory.total",
         "--format=csv,noheader"], text=True).strip()
    result["git_commit"] = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    result["git_status"] = subprocess.check_output(
        ["git", "status", "--short"], cwd=ROOT, text=True)
    dump(out / "environment.json", result)
    freeze = subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True)
    (out / "environment-freeze.txt").write_text(freeze, encoding="utf-8")
    dump(out / "dependency_sources.json", {
        "sionna": {"version": packages["sionna"], "url": "https://pypi.org/project/sionna/2.2.0/",
                   "usage": "PHY only; sionna-rt not installed; existing torch reused"},
        "table_origin": "Sionna packaged 3GPP 5G_bg1.csv / 5G_bg2.csv; hash per config",
        "curve_protocol_version": "2.1.0 notebook; exact curve reproduction remains pending",
        "cuda_scatter": "VN messages use fixed-order gather/reduce; repeated channel LLR index_add checked within 1e-5"})
    return result


def rng_for(config, split, snr=0.0, shard=0, stream="bits"):
    return np.random.default_rng(stable_seed(config, snr, shard, f"{split}/{stream}"))


def numpy_syndrome(link, cw):
    parity = np.zeros((len(cw), link.rows, link.z), dtype=np.uint8)
    for e, row in enumerate(link.rr):
        parity[:, row] ^= cw[:, link.var_np[e]]
    return parity


def check_reference(link, frames):
    cfg = link.cfg
    rng = rng_for(cfg["id"], "reference")
    payload = rng.integers(0, 2, (frames, link.a), dtype=np.uint8)
    cw, info = link.encode(payload)
    encoder = LDPC5GEncoder(link.b, link.etx, num_bits_per_symbol=2,
                           bg=f"bg{link.bg}", precision="single", device=str(link.device))
    assert encoder.z == link.z, (cfg["id"], encoder.z, link.z)
    ref_tx = encoder(torch.tensor(info, device=link.device, dtype=torch.float32))
    assert np.array_equal(ref_tx.cpu().numpy(), cw[:, link.tx_np]), "encoded/interleaved bits differ"
    # Recover all systematic/parity positions from the independent sparse encoder.
    padded = np.zeros((frames, link.k), dtype=np.float32)
    padded[:, :link.b] = info
    ref_full = encoder._encode_fast(torch.tensor(padded, device=link.device))
    assert np.array_equal(ref_full.cpu().numpy().reshape(frames, -1), cw), "full mother codeword differs"
    # Sionna's independently constructed interleaver and compressed circular buffer.
    full_indices = np.concatenate((np.arange(link.b), np.arange(link.k, link.n)))
    ref_indices = full_indices[2 * link.z:][:link.etx]
    if len(ref_indices) < link.etx:
        ref_indices = np.resize(full_indices[2 * link.z:], link.etx)
    ref_indices = ref_indices[encoder.out_int.cpu().numpy()]
    assert np.array_equal(ref_indices, link.tx_np), "rate-selection indices differ"
    # A second public implementation independently builds the selection/recovery indices.
    from py3gpp import nrRateMatchLDPC, nrRateRecoverLDPC, nrCRCEncode
    index_input = np.arange(2 * link.z, link.n, dtype=np.int64)
    index_input[(index_input >= link.b) & (index_input < link.k)] = -1
    third_indices = nrRateMatchLDPC(index_input[:, None], link.etx, 0, "QPSK", 1)
    assert np.array_equal(third_indices, link.tx_np), "py3gpp rate-selection differs"
    for i in range(frames):
        crc_ref = nrCRCEncode(payload[i], cfg["tb_crc"].removeprefix("CRC")).flatten()
        assert np.array_equal(crc_ref, info[i]), "CRC differs"
    llr_rng = rng_for(cfg["id"], "reference", stream="noise")
    llr = llr_rng.uniform(-2, 2, (frames, link.etx)).astype(np.float32)
    ours = link.recover(torch.tensor(llr, device=link.device)).cpu().numpy()
    worst = 0.0
    for i in range(frames):
        ref = nrRateRecoverLDPC(llr[i], link.a, float(cfg["actual_B_over_E"]), 0,
                               "QPSK", 1).flatten()
        ref = np.concatenate((np.zeros(2 * link.z), ref))
        ref = np.clip(ref, -20, 20)
        worst = max(worst, float(np.max(np.abs(ours[i] - ref))))
    assert worst < 1e-5, (cfg["id"], "rate recovery", worst)
    # Different decoder, LLR convention log P1/P0 at the Sionna API.
    decoder = LDPC5GDecoder(encoder, cn_update="boxplus-phi", num_iter=50,
                           device=str(link.device), prune_pcm=False)
    decoded = decoder((ref_tx * 2 - 1) * 20).cpu().numpy()
    assert np.array_equal(decoded, info), "Sionna high-SNR/noiseless decoder fails"
    return {"frames": frames, "full_codeword_mismatches": 0, "tx_mismatches": 0,
            "index_mismatches": 0, "crc_mismatches": 0, "recovered_llr_max_error": worst,
            "independent_decoder": "Sionna boxplus-phi 50, positive logits favor bit 1"}


def check_algebra(link, frames):
    rng = rng_for(link.cfg["id"], "algebra")
    payload = rng.integers(0, 2, (frames, link.a), dtype=np.uint8)
    cw, info = link.encode(payload)
    assert not numpy_syndrome(link, cw).any(), "Hc != 0"
    assert not cw[:, link.b:link.k].any(), "filler nonzero"
    assert np.array_equal(info, crc_attach(payload, link.cfg["tb_crc"]))
    return {"frames": frames, "nonzero_syndromes": 0, "nonzero_filler": 0,
            "shift_sha256": link.shift_hash, "index_sha256": link.index_hash}


def check_noiseless(link, frames, batch):
    rng = rng_for(link.cfg["id"], "noiseless")
    payload_errors = rejected = bit_errors = 0
    started = time.perf_counter()
    with torch.no_grad():
        for begin in range(0, frames, batch):
            count = min(batch, frames - begin)
            payload = rng.integers(0, 2, (count, link.a), dtype=np.uint8)
            cw, _ = link.encode(payload)
            lch, _ = link.channel(cw, 0, rng, noiseless=True)
            u, _, _ = link.decode(lch, iterations=50)
            errors = (u[:, :link.a] < 0).cpu().numpy() != payload
            payload_errors += int(errors.any(1).sum())
            bit_errors += int(errors.sum())
            rejected += int((~link.accepted(u)).sum())
    assert payload_errors == rejected == 0, (link.cfg["id"], payload_errors, rejected)
    return {"frames": frames, "payload_frame_errors": payload_errors,
            "payload_bit_errors": bit_errors, "rejected": rejected,
            "max_T": 50, "alpha": 0.8, "alpha_status": "uncalibrated_engineering_default",
            "seconds": time.perf_counter() - started}


def check_ssm(link):
    torch.manual_seed(17)
    model = RowSSM(link.rows).to(link.device)
    parameters = sum(p.numel() for p in model.parameters())
    assert parameters == (1873 if link.bg == 1 else 1857), parameters
    rng = rng_for(link.cfg["id"], "symmetry")
    payload = rng.integers(0, 2, (4, link.a), dtype=np.uint8)
    cw, info = link.encode(payload)
    sign = torch.tensor(1 - 2 * cw.astype(np.float32), device=link.device)
    # Exact puncture zeros and filler priors, plus saturated repeated observations.
    obs = torch.tensor(rng.uniform(-30, 30, (4, link.etx)).astype(np.float32), device=link.device)
    base = link.recover(obs)
    shifted = base * sign
    errors = []
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
    for phase in range(2):
        with torch.no_grad():
            u0, _, max_state = link.decode(base, controller=model)
            u1, _, _ = link.decode(shifted, controller=model)
            error = float((u1 - sign * u0).abs().max())
            assert error < 2e-4, ("SSM sign symmetry", error)
            assert float(max_state) <= 1.00001
            errors.append(error)
        if phase == 0:
            optimizer.zero_grad()
            lch, _ = link.channel(cw, 0, rng)
            _, history, _ = link.decode(lch, controller=model, history=True)
            loss = training_loss(link, history, info, step=10000)
            assert torch.isfinite(loss)
            loss.backward()
            grads = [p.grad for p in model.parameters()]
            assert all(g is not None and torch.isfinite(g).all() for g in grads)
            gradient_norm = float(torch.nn.utils.clip_grad_norm_(model.parameters(), 1))
            assert gradient_norm > 1e-8
            head_before = model.head.weight.detach().clone()
            optimizer.step()
            head_change = float((model.head.weight.detach() - head_before).abs().max())
            assert head_change > 1e-8, "optimizer did not change controller head"
    # This disposable step is a gradient gate, not a trained/checkpoint-selected model.
    return {"frames": 4, "iterations": 20, "parameters": parameters,
            "symmetry_max_error_before_after_update": errors, "state_max": float(max_state),
            "loss": float(loss.detach()), "gradient_norm": gradient_norm,
            "head_weight_max_update": head_change,
            "disposable_optimizer_steps": 1, "checkpoint_saved": False,
            "formal_training": False}


def extra_checks(link):
    # Compare min1/min2 to literal exclusion, including ties and zeros.
    rng = np.random.default_rng(981)
    q = torch.tensor(rng.integers(-2, 3, (2, link.p, link.z)), device=link.device).float()
    fast = link.minsum(q)
    expected = torch.empty_like(q)
    for _, edges in link.buckets:
        for j in range(edges.shape[1]):
            remaining = torch.cat((edges[:, :j], edges[:, j + 1:]), dim=1)
            v = q[:, remaining]
            sign = 1 - 2 * (v < 0).long().sum(2).remainder(2)
            expected[:, edges[:, j]] = v.abs().amin(2) * sign
    assert torch.equal(fast, expected), "minsum tie/zero exclusion differs"
    # Saturated posterior must be subtracted BEFORE clipping, per the spec.
    # Recovery repeated terms must accumulate before clipping.
    stress = dict(link.cfg)
    stress["E_tx_bits"] = 2 * link.n
    repeated = NRLink(stress, str(link.device))
    values = torch.tensor(rng.uniform(-25, 25, (2, repeated.etx)).astype(np.float32), device=link.device)
    actual = repeated.recover(values).cpu().numpy()
    expected = np.zeros((2, repeated.n), dtype=np.float64)
    for i in range(2):
        np.add.at(expected[i], repeated.tx_np, values[i].cpu().numpy())
    expected = np.clip(expected, -20, 20)
    expected[:, repeated.b:repeated.k] = 20
    error = float(np.max(np.abs(actual - expected)))
    assert error < 1e-5
    # Independent NumPy implementation of fixed-damping flooding NMS, using
    # literal edge exclusion and scatter, also stresses unsaturated posteriors.
    lch_np = rng.uniform(-20, 20, (2, link.n)).astype(np.float64)
    lch_np[:, link.b:link.k] = 20
    posterior = lch_np.copy()
    messages = np.zeros((2, link.p, link.z), dtype=np.float64)
    for _ in range(3):
        extrinsic = np.clip(posterior[:, link.var_np] - messages, -20, 20)
        extrinsic[:, ~link.edge_nonfiller.bool().cpu().numpy()] = 20
        candidate = np.empty_like(messages)
        for r in range(link.rows):
            ids = np.where(link.rr == r)[0]
            for edge in ids:
                others = extrinsic[:, ids[ids != edge]]
                signs = np.where(others < 0, -1, 1).prod(axis=1)
                candidate[:, edge] = signs * np.abs(others).min(axis=1)
        messages = np.clip(0.9 * 0.8 * candidate + 0.1 * messages, -20, 20)
        posterior = lch_np.copy()
        for i in range(2):
            np.add.at(posterior[i], link.var_np.flatten(), messages[i].flatten())
        posterior[:, link.b:link.k] = 20
    actual, _, _ = link.decode(torch.tensor(lch_np, device=link.device).float(), iterations=3, eta=0.1)
    nms_error = float(np.max(np.abs(actual.cpu().numpy() - np.clip(posterior, -20, 20))))
    assert nms_error < 5e-5, ("NumPy flooding NMS mismatch", nms_error)
    return {"minsum_ties_and_zeros": "passed", "repeat_recovery_max_error": error,
            "repeat_count_max": int(repeated.nu.max()), "numpy_fixed_damping_nms_max_error": nms_error}


def diagnostic(link, out, frames, batch):
    # Fixed small N for engineering only; never substitutes for the 20k/point pilot.
    rows = []
    for snr in (-2., 0., 2., 4., 6., 8.):
        bits_rng = rng_for(link.cfg["id"], "diagnostic", snr, stream="bits")
        noise_rng = rng_for(link.cfg["id"], "diagnostic", snr, stream="noise")
        frame_errors = bit_errors = rejected = 0
        started = time.perf_counter()
        with torch.no_grad():
            for begin in range(0, frames, batch):
                count = min(batch, frames - begin)
                payload = bits_rng.integers(0, 2, (count, link.a), dtype=np.uint8)
                cw, _ = link.encode(payload)
                lch, _ = link.channel(cw, snr, noise_rng)
                u, _, _ = link.decode(lch, iterations=20)
                errors = (u[:, :link.a] < 0).cpu().numpy() != payload
                frame_errors += int(errors.any(1).sum())
                bit_errors += int(errors.sum())
                rejected += int((~link.accepted(u)).sum())
        row = {"config_id": link.cfg["id"], "decoder": "NMS_F20", "alpha": 0.8,
               "alpha_status": "uncalibrated", "channel": "QPSK_AWGN", "split": "diagnostic",
               "ebn0_db": snr, "R_payload": link.a / link.etx, "frames": frames,
               "frame_errors_payload": frame_errors, "payload_bit_errors": bit_errors,
               "rejected": rejected, "bler": frame_errors / frames,
               "bler_ci95": wilson(frame_errors, frames), "sampling": "fixed_N_engineering_only",
               "early_stop": False, "fallback": False, "seconds": time.perf_counter() - started,
               "index_sha256": link.index_hash, "shift_sha256": link.shift_hash}
        if frame_errors == 0:
            row["zero_error_one_sided95_upper"] = zero_error_upper(frames)
        rows.append(row)
        dump(out / f"diagnostic_{link.bg}.json", rows)
        emit(out, "diagnostic_point", **row)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("quick", "stage1"), default="quick")
    parser.add_argument("--output", required=True)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--batch", type=int, default=32)
    parser.add_argument("--diagnostic-frames", type=int, default=256)
    args = parser.parse_args()
    if args.batch <= 0 or args.diagnostic_frames <= 0:
        parser.error("batch and diagnostic-frames must be positive")
    out = Path(args.output).resolve()
    out.mkdir(parents=True, exist_ok=True)
    if (out / "environment.json").exists():
        parser.error("output already contains a run; choose a new directory")
    torch.set_num_threads(4)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.use_deterministic_algorithms(False)
    try:
        env = environment(out, args)
        emit(out, "started", gpu=env["gpu"], mode=args.mode, pid=os.getpid())
        frozen = json.loads((ROOT.parent / "experiment_manifest.json").read_text(encoding="utf-8"))
        generated = build()
        assert frozen == generated, "frozen manifest differs from scalar generator"
        dump(out / "analytic_checks.json", {"protocol": self_check(), "toy": check_invariants()})
        emit(out, "scalar_gate_passed", manifest_sha256=sha256(ROOT.parent / "experiment_manifest.json"))
        configs = frozen["ldpc_configs"]
        if args.mode == "quick":
            configs = [c for c in configs if c["id"] in
                       ("ldpc_B1024_R1-2_Q2", "ldpc_B4096_R1-2_Q2")]
        records = []
        for cfg in configs:
            link = NRLink(cfg, args.device)
            emit(out, "config_started", config_id=cfg["id"])
            record = {"config_id": cfg["id"], "algebra": check_algebra(link, 1000 if args.mode == "stage1" else 16)}
            record["reference"] = check_reference(link, 100 if args.mode == "stage1" else 4)
            emit(out, "reference_gate_passed", config_id=cfg["id"], **record["reference"])
            count = (10000 if link.b <= 2048 else 1000) if args.mode == "stage1" else 16
            record["noiseless"] = check_noiseless(link, count, args.batch)
            records.append(record)
            dump(out / "chain_checks.json", records)
            emit(out, "noiseless_gate_passed", config_id=cfg["id"], **record["noiseless"])
            del link
        ssms = []
        for cid in ("ldpc_B1024_R1-2_Q2", "ldpc_B4096_R1-2_Q2"):
            link = NRLink(next(c for c in configs if c["id"] == cid), args.device)
            ssms.append({"config_id": cid, "extra": extra_checks(link), "ssm": check_ssm(link)})
            dump(out / "ssm_checks.json", ssms)
            emit(out, "ssm_gradient_symmetry_passed", **ssms[-1])
            diagnostic(link, out, args.diagnostic_frames, args.batch)
        summary = {"status": "stage1_completed" if args.mode == "stage1" else "quick_smoke_completed",
                   "configs_checked": len(records), "gates": {
                       "1_scalar": "passed", "2_QC_algebra": "passed" if args.mode == "stage1" else "smoke_only",
                       "3_independent_reference": "passed" if args.mode == "stage1" else "smoke_only",
                       "4_noiseless": "passed" if args.mode == "stage1" else "smoke_only",
                       "5_public_curve": "pending_exact_2.1.0_notebook_reproduction",
                       "6_SSM_symmetry_gradient": "passed_for_two_source_configs"},
                   "formal_training_authorized_by_gates": False,
                   "formal_training_steps": 0, "pilot_20k_per_point": "pending",
                   "alpha_calibration": "pending", "polar_validation": "pending",
                   "limitations": ["diagnostic is not formal BLER or public-curve reproduction",
                                   "fixed-shape fixed-iteration decoder; no early stop or fallback implementation yet",
                                   "RTX 4060 engineering data does not establish 4090/5090 ranking"]}
        dump(out / "summary.json", summary)
        emit(out, "completed", **summary)
    except Exception as exc:
        dump(out / "failure.json", {"error": repr(exc), "traceback": traceback.format_exc()})
        emit(out, "failed", error=repr(exc))
        raise


if __name__ == "__main__":
    main()
