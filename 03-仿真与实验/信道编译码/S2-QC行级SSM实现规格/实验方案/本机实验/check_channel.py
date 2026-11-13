"""Noisy-channel and true repetition checks independent of SSM training."""
import argparse
from fractions import Fraction
from pathlib import Path
import sys
import traceback

import numpy as np
import torch
from py3gpp import nrRateMatchLDPC, nrRateRecoverLDPC
from sionna.phy.fec.ldpc import LDPC5GEncoder

sys.dont_write_bytecode = True
from nr_link import NRLink, sha256
from run_local import ROOT, dump, emit, environment, numpy_syndrome

sys.path.insert(0, str(ROOT.parent))
from generate_manifest import ldpc


def check(link):
    rng = np.random.default_rng(20261112)
    count = 128
    payload = rng.integers(0, 2, (count, link.a), dtype=np.uint8)
    cw, info = link.encode(payload)
    assert not numpy_syndrome(link, cw).any()
    snrs = np.linspace(-2, 4, count)
    _, actual = link.channel(cw, snrs, np.random.default_rng(392))
    # Independent NumPy QPSK mapper, AWGN and demapper, same Gaussian draws.
    n0 = (1 / (2 * (link.a / link.etx) * 10 ** (snrs / 10)))[:, None, None]
    signs = 1 - 2 * cw[:, link.tx_np].astype(np.float64)
    symbols = signs.reshape(count, -1, 2) / np.sqrt(2)
    noise = np.random.default_rng(392).standard_normal(symbols.shape)
    expected = (2 * np.sqrt(2) * (symbols + np.sqrt(n0 / 2) * noise) / n0).reshape(count, -1)
    max_error = float(np.max(np.abs(actual.cpu().numpy() - expected)))
    assert max_error < 1e-5, ("independent QPSK LLR", max_error)
    _, scalar = link.channel(cw, 1.0, np.random.default_rng(398))
    _, vector = link.channel(cw, np.full(count, 1.0), np.random.default_rng(398))
    vector_error = float((scalar - vector).abs().max())
    assert vector_error < 1e-5
    # Unit-energy QPSK: LLR * transmitted sign ~ N(2/N0,4/N0).
    standardized = (actual.cpu().numpy() * signs - 2 / n0.reshape(count, 1)) / np.sqrt(4 / n0.reshape(count, 1))
    mean, variance = float(standardized.mean()), float(standardized.var())
    assert abs(mean) < 0.015 and abs(variance - 1) < 0.025, (mean, variance)
    # BPSK with the same real Gaussian input gives the same bit LLR convention.
    sigma2 = 1 / (2 * (link.a / link.etx) * 10 ** (snrs[:, None] / 10))
    bpsk = 2 * (signs + np.sqrt(sigma2) * noise.reshape(count, -1)) / sigma2
    assert np.max(np.abs(expected - bpsk)) < 1e-10
    # Perfect complete codewords must pass; valid LDPC words with invalid CRC must fail.
    u = torch.tensor(20 * (1 - 2 * cw.astype(np.float32)), device=link.device)
    assert link.accepted(u).all()
    encoder = LDPC5GEncoder(link.b, link.etx, num_bits_per_symbol=2, bg=f"bg{link.bg}", device=str(link.device))
    corrupted_info = info[:4].copy()
    corrupted_info[:, -1] ^= 1
    padded = torch.zeros((4, link.k), device=link.device)
    padded[:, :link.b] = torch.tensor(corrupted_info, device=link.device)
    invalid_crc_cw = encoder._encode_fast(padded).squeeze(-1)
    invalid_crc_llr = 20 * (1 - 2 * invalid_crc_cw)
    parity, _ = link.syndrome(invalid_crc_llr)
    assert not parity.any() and not link.accepted(invalid_crc_llr).any()
    zeros = u.clone()
    zeros[:, 0] = 0
    assert not link.accepted(zeros).any(), "zero ambiguity accepted"
    # A valid LDPC word can violate the shortened-code filler constraint.
    # Retain valid information/CRC and encode one deliberately nonzero filler.
    padded[:, :link.b] = torch.tensor(info[:4], device=link.device)
    padded[:, link.b] = 1
    invalid_filler_cw = encoder._encode_fast(padded).squeeze(-1)
    invalid_filler_llr = 20 * (1 - 2 * invalid_filler_cw)
    parity, _ = link.syndrome(invalid_filler_llr)
    assert not parity.any(), "filler counterexample should remain LDPC-valid"
    assert not link.accepted(invalid_filler_llr).any(), "nonzero filler accepted despite valid LDPC/CRC"
    return {"config_id": link.cfg["id"], "frames": count, "numpy_qpsk_llr_max_error": max_error,
            "scalar_vector_SNR_max_error": vector_error, "standardized_noise_mean": mean,
            "standardized_noise_variance": variance, "BPSK_QPSK_same_bit_energy": "passed",
            "accept_valid_and_reject_invalid_CRC_filler_and_zero_ties": "passed",
            "index_sha256": link.index_hash, "shift_sha256": link.shift_hash}


def repetition_check():
    # Recompute BG/Z/filler legitimately; R=1/8 actually repeats for B=512.
    cfg = ldpc(512, Fraction(1, 8))
    link = NRLink(cfg)
    assert link.nu.max() > 1
    index_input = np.arange(2 * link.z, link.n, dtype=np.int64)
    index_input[(index_input >= link.b) & (index_input < link.k)] = -1
    assert np.array_equal(nrRateMatchLDPC(index_input[:, None], link.etx, 0, "QPSK", 1), link.tx_np)
    raw = np.random.default_rng(799).uniform(-30, 30, (4, link.etx)).astype(np.float32)
    recovered = link.recover(torch.tensor(raw, device=link.device)).cpu().numpy()
    worst = 0.0
    for i in range(4):
        reference = nrRateRecoverLDPC(raw[i], link.a, 1 / 8, 0, "QPSK", 1).flatten()
        reference = np.clip(np.concatenate((np.zeros(2 * link.z), reference)), -20, 20)
        worst = max(worst, float(np.abs(recovered[i] - reference).max()))
    assert worst < 1e-5, worst
    return {"config_id": cfg["id"], "repeat_count_max": int(link.nu.max()),
            "frames": 4, "py3gpp_recovery_max_error": worst, "index_sha256": link.index_hash}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    out = Path(args.output).resolve()
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        parser.error("output must be empty")
    torch.set_num_threads(4)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    try:
        env = environment(out, args)
        env["source_sha256"][str(Path(__file__).resolve())] = sha256(Path(__file__).resolve())
        dump(out / "environment.json", env)
        records = [check(NRLink(ldpc(b, Fraction(1, 2)))) for b in (1024, 4096)]
        repeated = repetition_check()
        result = {"status": "noisy_channel_checks_passed", "source_configs": records,
                  "true_repetition": repeated, "public_curve_gate": "pending", "formal_training": False}
        dump(out / "summary.json", result)
        emit(out, "completed", **result)
    except Exception as exc:
        dump(out / "failure.json", {"error": repr(exc), "traceback": traceback.format_exc()})
        emit(out, "failed", error=repr(exc))
        raise


if __name__ == "__main__":
    main()
