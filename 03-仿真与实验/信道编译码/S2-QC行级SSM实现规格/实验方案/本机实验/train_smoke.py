"""Bounded FP32 training/debugging; does not launch protocol-v1 formal training."""
import argparse
import json
from pathlib import Path
import sys
import time
import traceback

import numpy as np
import torch
from torch.nn import functional as F

sys.dont_write_bytecode = True
from nr_link import NRLink, sha256
from run_local import ROOT, dump, emit, environment, rng_for
from ssm import RowSSM, training_loss

sys.path.insert(0, str(ROOT.parent))
from generate_manifest import build
from protocol_checks import wilson, zero_error_upper


def samples(link, split, count, snr, seed=17, step=0):
    key = f"{split}/seed-{seed}/step-{step}"
    bits_rng = rng_for(link.cfg["id"], key, stream="bits")
    noise_rng = rng_for(link.cfg["id"], key, stream="noise")
    payload = bits_rng.integers(0, 2, (count, link.a), dtype=np.uint8)
    cw, info = link.encode(payload)
    lch, _ = link.channel(cw, snr, noise_rng)
    return payload, cw, info, lch


def evaluate(link, model, frames, batch):
    """Identical frozen inputs for NMS, initial SSM and every later checkpoint."""
    result = []
    with torch.no_grad():
        for snr in (0.5, 1.0, 1.5):
            payload, _, info, lch = samples(link, f"smoke-validation/{snr:.4f}", frames, snr)
            errors = rejected = bits = 0
            total_bce = 0.0
            for begin in range(0, frames, batch):
                end = min(frames, begin + batch)
                u, _, _ = link.decode(lch[begin:end], controller=model)
                labels = torch.tensor(info[begin:end], device=link.device, dtype=torch.float32)
                total_bce += float(F.binary_cross_entropy_with_logits(-u[:, :link.b], labels,
                                                                     reduction="sum"))
                wrong = (u[:, :link.a] < 0).cpu().numpy() != payload[begin:end]
                errors += int(wrong.any(1).sum())
                bits += int(wrong.sum())
                rejected += int((~link.accepted(u)).sum())
            row = {"snr_db": snr, "frames": frames, "information_bce": total_bce / (frames * link.b),
                   "payload_frame_errors": errors, "payload_bit_errors": bits, "rejected": rejected,
                   "bler_ci95": wilson(errors, frames)}
            if errors == 0:
                row["zero_error_one_sided95_upper"] = zero_error_upper(frames)
            result.append(row)
    return result


def post_checks(link, model):
    payload, cw, info, lch = samples(link, "smoke-postcheck", 8, 1.0)
    sign = torch.tensor(1 - 2 * cw.astype(np.float32), device=link.device)
    with torch.no_grad():
        # Preserve exact puncture zeros/filler and force additional clipping.
        base = (lch * 4).clamp(-20, 20).masked_fill(link.filler, 20)
        u, _, state = link.decode(base, controller=model)
        signed, _, _ = link.decode(base * sign, controller=model)
        symmetry = float((signed - u * sign).abs().max())
        assert symmetry < 2e-4 and float(state) <= 1.00001, (symmetry, state)
        clean, _ = link.channel(cw, 0.0, np.random.default_rng(19), noiseless=True)
        decoded, _, _ = link.decode(clean, iterations=20, controller=model)
        errors = int(np.any((decoded[:, :link.a] < 0).cpu().numpy() != payload, axis=1).sum())
        rejected = int((~link.accepted(decoded)).sum())
        assert errors == rejected == 0, (errors, rejected)
    return {"frames": len(payload), "symmetry_max_abs_error": symmetry, "state_abs_max": float(state),
            "trained_controller_noiseless_payload_errors": errors, "noiseless_rejected": rejected}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--config-id", choices=("ldpc_B1024_R1-2_Q2", "ldpc_B4096_R1-2_Q2"),
                        default="ldpc_B1024_R1-2_Q2")
    parser.add_argument("--steps", type=int, default=100)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--validation-frames", type=int, default=64)
    parser.add_argument("--seed", type=int, default=17)
    args = parser.parse_args()
    if not 1 <= args.steps <= 500 or not 1 <= args.batch <= 64 or args.validation_frames < 1:
        parser.error("smoke bounds: steps 1..500, batch 1..64, validation-frames >=1")
    out = Path(args.output).resolve()
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        parser.error("output must be a new empty directory")
    torch.set_num_threads(4)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.manual_seed(args.seed)
    records = []
    started = time.perf_counter()
    try:
        env = environment(out, args)
        env["source_sha256"][str(Path(__file__).resolve())] = sha256(Path(__file__).resolve())
        dump(out / "environment.json", env)
        manifest = json.loads((ROOT.parent / "experiment_manifest.json").read_text(encoding="utf-8"))
        assert manifest == build()
        cfg = next(c for c in manifest["ldpc_configs"] if c["id"] == args.config_id)
        link = NRLink(cfg)
        model = RowSSM(link.rows).to(link.device)
        decay, no_decay = [], []
        for name, parameter in model.named_parameters():
            (no_decay if name.endswith("bias") or "norm" in name or name == "theta" else decay).append(parameter)
        optimizer = torch.optim.AdamW([{"params": decay, "weight_decay": 1e-4},
                                       {"params": no_decay, "weight_decay": 0.0}], lr=1e-3)
        run_spec = {"formal_training": False, "T": 20, "alpha": 0.8, "alpha_calibrated": False,
                    "debug_SNR_per_codeword_uniform_dB": [0.0, 2.0], "seed": args.seed,
                    "steps": args.steps, "batch": args.batch, "lr": 1e-3,
                    "lr_schedule": "constant_debug_only; no protocol warmup/cosine",
                    "syndrome_loss": "zero for first 5000 steps, as protocol",
                    "validation": "fixed random payload/noise at 0.5/1/1.5 dB, last checkpoint only",
                    "index_sha256": link.index_hash, "shift_sha256": link.shift_hash,
                    "formal_gates": "public curve, pilot and alpha calibration still pending"}
        dump(out / "run_spec.json", run_spec)
        emit(out, "started", gpu=env["gpu"], **run_spec)
        baseline = evaluate(link, None, args.validation_frames, args.batch)
        initial = evaluate(link, model, args.validation_frames, args.batch)
        dump(out / "initial_validation.json", {"NMS_F20": baseline, "initial_SSM": initial})
        emit(out, "initial_validation", NMS_F20=baseline, initial_SSM=initial)
        torch.cuda.reset_peak_memory_stats()
        for step in range(1, args.steps + 1):
            torch.cuda.synchronize()
            step_start = time.perf_counter()
            snr_rng = rng_for(args.config_id, f"smoke-train/seed-{args.seed}/step-{step}", stream="snr")
            snrs = snr_rng.uniform(0.0, 2.0, args.batch)
            _, _, info, lch = samples(link, "smoke-train", args.batch, snrs, args.seed, step)
            optimizer.zero_grad(set_to_none=True)
            _, history, state = link.decode(lch, controller=model, history=True)
            loss = training_loss(link, history, info, step)
            assert torch.isfinite(loss), (step, "loss")
            loss.backward()
            assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in model.parameters()), (step, "gradient")
            grad = float(torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0))
            assert np.isfinite(grad) and float(state) <= 1.00001, (step, grad, state)
            optimizer.step()
            assert all(torch.isfinite(p).all() for p in model.parameters()), (step, "parameters")
            torch.cuda.synchronize()
            row = {"step": step, "loss": float(loss.detach()), "gradient_norm_before_clip": grad,
                   "state_abs_max": float(state), "seconds": time.perf_counter() - step_start,
                   "peak_allocated_bytes": torch.cuda.max_memory_allocated(),
                   "snr_min_db": float(snrs.min()), "snr_max_db": float(snrs.max())}
            records.append(row)
            with (out / "train_history.jsonl").open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row) + "\n")
            if step == 1 or step % 10 == 0 or step == args.steps:
                emit(out, "train_step", **row)
            if step % 20 == 0 or step == args.steps:
                validation = evaluate(link, model, args.validation_frames, args.batch)
                emit(out, "validation", step=step, points=validation)
        post = post_checks(link, model)
        checkpoint = out / "smoke_checkpoint.pt"
        torch.save({"model": model.state_dict(), "optimizer": optimizer.state_dict(),
                    "step": args.steps, "run_spec": run_spec}, checkpoint)
        reloaded = RowSSM(link.rows).to(link.device)
        reloaded.load_state_dict(torch.load(checkpoint, weights_only=True)["model"])
        _, _, _, replay = samples(link, "checkpoint-replay", 4, 1.0)
        with torch.no_grad():
            before, _, _ = link.decode(replay, controller=model)
            after, _, _ = link.decode(replay, controller=reloaded)
            replay_error = float((before - after).abs().max())
            assert replay_error == 0
        summary = {"status": "smoke_training_completed", "formal_training": False,
                   "config_id": args.config_id, "steps": args.steps, "batch": args.batch,
                   "observations": args.steps * args.batch,
                   "parameters": sum(p.numel() for p in model.parameters()),
                   "elapsed_seconds": time.perf_counter() - started,
                   "mean_step_seconds": float(np.mean([r["seconds"] for r in records])),
                   "mean_step_seconds_after_first_10": float(np.mean([r["seconds"] for r in records[10:] or records])),
                   "peak_allocated_bytes": torch.cuda.max_memory_allocated(),
                   "peak_reserved_bytes": torch.cuda.max_memory_reserved(),
                   "initial_validation": initial, "final_validation": validation,
                   "post_checks": post, "checkpoint_replay_max_error": replay_error,
                   "checkpoint_sha256": sha256(checkpoint),
                   "limitations": ["bounded debugging run is not formal model training",
                                   "uncalibrated alpha and debugging SNR; no BLER improvement claim",
                                   "no protocol speed benchmark or full-batch64 runtime extrapolation"]}
        dump(out / "summary.json", summary)
        emit(out, "completed", **summary)
    except Exception as exc:
        dump(out / "failure.json", {"error": repr(exc), "traceback": traceback.format_exc(),
                                    "completed_steps": len(records)})
        emit(out, "failed", error=repr(exc), completed_steps=len(records))
        raise


if __name__ == "__main__":
    main()
