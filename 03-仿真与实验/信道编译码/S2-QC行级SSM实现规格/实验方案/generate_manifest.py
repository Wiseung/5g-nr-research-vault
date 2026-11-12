"""Generate the frozen experiment plan. Python standard library only.

This validates scalar NR coding parameters. It does not implement an NR
encoder/decoder, validate shift tables, train a model, or benchmark a GPU.
"""
import hashlib
import json
import math
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LIFTING = {
    i: tuple(base * 2**j for j in range(9) if base * 2**j <= 384)
    for i, base in enumerate((2, 3, 5, 7, 9, 11, 13, 15))
}
ALL_Z = sorted(z for values in LIFTING.values() for z in values)
BG = {1: (46, 68, 316, 22, 66), 2: (42, 52, 197, 10, 50)}
RATES = (Fraction(1, 3), Fraction(1, 2), Fraction(2, 3), Fraction(3, 4))


def ceil_fraction(x):
    return -(-x.numerator // x.denominator)


def select_bg(a, target_rate):
    return 2 if (a <= 292 or (a <= 3824 and target_rate <= Fraction(67, 100))
                 or target_rate <= Fraction(1, 4)) else 1


def stable_seed(config_id, snr_db, shard, split="test"):
    # Do not use Python hash(), which is process-randomized.
    key = f"S2-protocol-v1|{split}|{config_id}|{snr_db:.4f}|{shard}"
    return int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], "big") % (2**31-1)


def ldpc(b, rate, qm=2):
    crc = 16 if b <= 3840 else 24
    a = b - crc
    assert (16 if a <= 3824 else 24) == crc
    bg = select_bg(a, rate)
    rows, cols, base_edges, kcols, rmcols = BG[bg]
    kb = 22 if bg == 1 else (10 if b > 640 else 9 if b > 560 else 8 if b > 192 else 6)
    z = next(z for z in ALL_Z if kb*z >= b)
    ils = next(i for i, values in LIFTING.items() if z in values)
    kenc = kcols*z
    f = kenc-b
    etx = qm*ceil_fraction(Fraction(b, 1)/(rate*qm))
    cid = f"ldpc_B{b}_R{rate.numerator}-{rate.denominator}_Q{qm}"
    return {
        "id": cid, "family": "LDPC", "payload_bits_A": a,
        "tb_crc": "CRC16" if crc == 16 else "CRC24A",
        "B_including_tb_crc": b, "base_graph": bg, "Z": z, "i_LS": ils,
        "Kb_for_lifting_selection": kb, "K_encoder_including_filler": kenc,
        "filler_bits": f, "N_full_graph": cols*z, "M_checks": rows*z,
        "graph_edges": base_edges*z, "N_circular_buffer": rmcols*z,
        "mandatory_first_puncture_bits": 2*z, "E_tx_bits": etx,
        "target_rate_label": str(rate), "actual_B_over_E": b/etx,
        "actual_payload_rate_A_over_E": a/etx,
        "modulation_bits_Qm": qm, "rv": 0, "Nref_limit": None,
        "code_blocks": 1, "cb_crc_bits": 0,
        "status": "scalar_parameters_checked_full_chain_pending",
        "scope": "TS38.212_coding_kernel_not_TS38.214_TBS_MCS_validation",
    }


def polar_n(k, e, nmax):
    ce = (e-1).bit_length()
    n1 = ce
    if Fraction(e) <= Fraction(9, 8)*2**(ce-1) and Fraction(k, e) < Fraction(9, 16):
        n1 -= 1
    n2 = (8*k-1).bit_length()
    return 2**max(5, min(n1, n2, nmax))


def polar(a, crc, e, expected_n, route, optional=False):
    k = a+crc
    nmax = 9 if route == "PDCCH" else 10
    n = polar_n(k, e, nmax)
    assert n == expected_n and k <= n and e % 2 == 0
    if route == "UCI_PUCCH":
        assert a >= 20 and k > 25
        assert not ((a >= 360 and e >= 1088) or a >= 1013)
    else:
        assert crc == 24 and k <= 164 and e % 108 == 0
    return {
        "id": f"polar_{route}_A{a}_E{e}", "family": "Polar", "route": route,
        "payload_bits_A": a, "crc": f"CRC{crc}" if crc == 11 else "CRC24C",
        "K_with_crc": k, "N_mother": n, "E_tx_bits": e, "n_max": nmax,
        "Qm": 2, "rate_payload": a/e, "rate_with_crc": k/e,
        "I_IL": int(route == "PDCCH"), "I_BIL": int(route == "UCI_PUCCH"),
        "n_PC": 0, "I_seg": 0,
        "RNTI_if_PDCCH": "0x1234" if route == "PDCCH" else None,
        "list_sizes": [8, 16, 32], "optional": optional,
        "status": "scalar_parameters_checked_reliability_interleaver_CRC_chain_pending",
        "purpose": "CA_SCL_chain_validation_not_a_baseline_for_LDPC_S2",
    }


def resources(bg, z, batch=64, t=20, layers=1, d=16, state=4, expand=1):
    rows, cols, be, _, _ = BG[bg]
    n, m, edges = cols*z, rows*z, be*z
    p, c, re, o, h = 12, 8, 4, 1, d*expand
    params = (rows*re+p*d+d
              + layers*(3*d*h+h*h+3*h*state+c*h+2*d+4*h+2*state)
              + d+d*o+o)
    fr = 2*p*d + layers*(6*d*h+2*h*(h+2*state)+2*c*h+8*h*state)+2*d*o
    fc = t*rows*fr
    fn = t*(14*edges+n)
    scratch = rows*(layers*h*state+p+layers*(5*d+6*h+2*state)+o)
    infer = 4*batch*(5*edges+3*n+scratch)+batch*(4*n+m)+8*edges+4*params
    saved = 12*edges+6*n+rows*(p+layers*(h*state+6*d+8*h+2*state))
    train = infer+4*batch*t*saved+batch*t*(17*m+2*edges)+12*params
    return {
        "base_graph": bg, "Z": z, "batch": batch, "iterations": t,
        "parameters": params, "controller_poly_flops": fc,
        "nms_and_stats_poly_flops": fn, "total_poly_flops": fc+fn,
        "inference_planning_bytes": infer, "training_planning_bytes": train,
        "state_bytes_per_codeword": 4*rows*layers*h*state,
        "unfused_tensor_traffic_estimate_bytes": 4*t*(4*edges+2*n),
        "status": "analytic_planning_ledger_not_measured_peak_or_total_instruction_count",
    }


def build():
    configs = [ldpc(b, r) for b in (512, 1024, 2048, 4096, 8448) for r in RATES]
    polar_configs = [polar(a, 24, e, n, "PDCCH")
                     for a, e, n in ((40, 108, 128), (80, 216, 256), (128, 432, 512))]
    polar_configs += [polar(a, 11, e, n, "UCI_PUCCH", n == 1024)
                      for a, e, n in ((53, 128, 128), (117, 256, 256),
                                      (245, 512, 512), (501, 1024, 1024))]
    budgets = [
        (1, "链路与标准参数", 6), (2, "经典基线与校验", 24),
        (3, "主模型与神经基线首轮", 45), (4, "三种子与记忆对照", 45),
        (5, "必做消融与短码ECCT", 45), (6, "零样本与目标配置专家模型", 65),
        (7, "GPU时延吞吐显存功耗", 20), (8, "低BLER固定帧数仿真", 120),
        (9, "写作与Plan_B整合", 10), (10, "锁版本复跑与修正", 20),
    ]
    return {
        "protocol": "S2-QC-row-iteration-SSM-experiments-v1",
        "created_date": "2026-11-12", "status": "PLAN_NO_TRAINING_OR_GPU_RESULTS",
        "standard": "TS 38.212 V18.5.0, fixed for reproducibility",
        "K_naming": "User requested K values interpreted as B including TB CRC, excluding filler",
        "llr_convention": "log(P(bit=0|y)/P(bit=1|y)); hard_bit=(LLR<0)",
        "ebn0_convention": "energy per payload bit A, excluding CRC/filler; rate=A/E_tx",
        "ldpc_configs": configs, "polar_configs": polar_configs,
        "source_training_configs": {
            "BG2": "ldpc_B1024_R1-2_Q2", "BG1": "ldpc_B4096_R1-2_Q2",
        },
        "controller": {"axis": "iteration", "schedule": "flooding",
                       "name": "custom_normalized_ZOH_selective_diagonal_SSM",
                       "layers": 1, "d_model": 16, "d_state": 4, "expand": 1,
                       "condition_target": "delta_only", "snr_condition": False,
                       "T_train": 20, "T_neural": 20, "fallback_extra_T": 10},
        "training": {
            "seeds": [17, 29, 43], "optimizer_steps": 50000,
            "effective_batch": 64, "observations_per_run": 3200000,
            "pilot_grid_ebn0_db": [-2+0.5*i for i in range(21)],
            "pilot_frames_per_snr": 20000, "gamma_reference": "NMS-F20 BLER=1e-2 log interpolation",
            "snr_range": "uniform Eb/N0 in [gamma_reference-1.5, gamma_reference+1.0] dB",
            "optimizer": "AdamW", "lr_peak": 0.001, "lr_final": 0.0001,
            "warmup_steps": 1000, "weight_decay": 0.0001, "grad_clip_norm": 1.0,
            "lambda_syndrome": {"start": 5000, "ramp_end": 10000, "final": 0.02},
            "teacher": False, "final_validation_frames_per_snr": 100000,
            "checkpoint_selection": "lowest mean BCE on B information bits including CRC excluding filler over 5 frozen SNR values",
        },
        "testing": {
            "sweep_T": [5, 10, 20, 50], "additional_total_T_fallback_control": 30,
            "train_seeds": [17, 29, 43], "test_shards": 32,
            "seed_rule": "SHA256(S2-protocol-v1|split|config|snr_4decimals|shard)",
            "frame_budget": {"1e-2": 20000, "1e-3": 200000,
                             "1e-4": 2000000, "1e-5": 20000000},
            "final_sampling": "fixed N per point, frozen after an independent pilot",
            "ci": "Wilson two-sided 95%; zero errors one-sided exact 95% upper bound",
            "deep_bler": {"configs": ["ldpc_B1024_R1-2_Q2", "ldpc_B4096_R1-2_Q2"],
                          "decoders": ["S2", "best_validated_classical", "unrolled_NMS"],
                          "points_per_config_at_1e-5_scale": 2,
                          "frames_per_point_per_decoder": 20000000,
                          "first_seed_fixed_before_tests": 17,
                          "qualification": "all-seed screening first; other seeds deep-run if budget permits"},
        },
        "baseline_tracks": {
            "balanced_primary_four": ["SPA_F", "NMS_L", "unrolled_NMS_F", "GNN_F"],
            "mandatory_additional_controls": ["NMS_F", "OMS_L", "EMA_row", "MLP_row", "GRU_row"],
            "short_ECCT_track": {"config": "ldpc_B512_R1-2_Q2", "steps": 5000,
                                 "effective_batch": 64, "seeds": [17, 29, 43],
                                 "matched_models": ["ECCT_adapter", "S2", "GNN_F", "unrolled_NMS_F"],
                                 "parameters": "native and +/-10% feasible budget tracks kept separate",
                                 "adapter": "GF(2) H_tx from rank-checked rate-matched generator, includes filler elimination, CRC kept external",
                                 "implementation_status": "待核实"},
            "four_fairness_tracks": ["same_observations_and_optimizer_steps",
                                     "matched_neural_parameters_plus_native_strong_baseline",
                                     "matched_analytic_FLOPs_plus_special_ops_and_bytes",
                                     "matched_measured_latency_with_deadline_violation_rate"],
        },
        "generalization": {
            "mandatory_zero_shot": ["same_BG_other_Z_B", "same_B_other_rate_same_BG",
                                    "outside_training_SNR", "AWGN_to_coherent_iid_symbol_Rayleigh"],
            "source_BG2_other_rates": ["1/3", "2/3"],
            "source_BG1_other_rates": ["1/3", "2/3", "3/4"],
            "specialists_three_seeds": ["BG2_B512_R1/2", "BG1_B8448_R1/2",
                                        "BG2_B1024_R2/3", "BG1_B4096_R3/4",
                                        "BG2_B1024_R1/2_Rayleigh", "BG2_B1024_R1/2_wide_SNR"],
            "cross_BG_zero_shot_claim": False, "TDL": "optional_full_OFDM_chain",
        },
        "measurement": {
            "batches": [1, 2, 4, 8, 16, 32, 64, 128, 256],
            "warmup_calls_min": 200, "latency_calls_per_round": 10000,
            "rounds": 5, "sustained_throughput_seconds_per_round_min": 1,
            "power_seconds_per_round": 30, "power_poll_interval_ms": 100,
            "timing_scopes": ["GPU_events_device_only", "host_wall_device_resident", "host_wall_with_H2D_D2H"],
            "precision_primary": "FP32", "precision_optional": ["BF16", "INT8_QAT"],
            "software_versions_driver_and_backend_support": "待核实",
            "device_4090_or_5090": "待目标机确认，所有排名必须同卡",
            "actual_power_sensor_support_and_window": "待核实",
        },
        "planned_gpu_hours": [{"week": w, "task": s, "cap_hours": h}
                              for w, s, h in budgets],
        "total_planned_gpu_hour_cap": sum(h for _, _, h in budgets),
        "analytical_resource_examples": [resources(bg, z, b)
                                         for bg, z in ((2, 104), (1, 192), (1, 384))
                                         for b in (1, 64, 256)],
        "sources": {
            "standard": "https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/18.05.00_60/ts_138212v180500p.pdf",
            "sionna_validation": "https://nvlabs.github.io/sionna/v2.1.0/phy/tutorials/notebooks/5G_Channel_Coding_Polar_vs_LDPC_Codes.html",
            "GNN": "https://arxiv.org/abs/2207.14742", "ECCT": "https://arxiv.org/abs/2203.14966",
            "NVML": "https://docs.nvidia.com/deploy/nvml-api/620/api/group__nvmlDeviceQueries.html",
            "PyTorch_timing": "https://docs.pytorch.org/docs/stable/notes/cuda.html",
        },
    }


def validate(m):
    assert len(m["ldpc_configs"]) == 20
    assert len({x["id"] for x in m["ldpc_configs"]}) == 20
    expected = {512: (2, 64), 1024: (2, 104), 2048: (2, 208),
                4096: (1, 192), 8448: (1, 384)}
    for x in m["ldpc_configs"]:
        b, bg, z = x["B_including_tb_crc"], x["base_graph"], x["Z"]
        r = Fraction(x["target_rate_label"])
        assert x["E_tx_bits"] % x["modulation_bits_Qm"] == 0
        assert x["K_encoder_including_filler"]-b == x["filler_bits"] >= 0
        assert b <= (8448 if bg == 1 else 3840)
        if r != Fraction(3, 4):
            assert (bg, z) == expected[b]
        elif b <= 2048:
            assert bg == 1
        assert abs(x["actual_B_over_E"]-float(r)) < 0.002
    assert select_bg(2032, Fraction(1, 2)) == 2  # reject requested BG1 low-rate short block
    assert select_bg(496, Fraction(3, 4)) == 1   # reject BG2 high-rate short block
    assert len(m["polar_configs"]) == 7
    assert m["total_planned_gpu_hour_cap"] == 400
    assert resources(2, 104)["total_poly_flops"] == 8774720
    assert resources(1, 192)["total_poly_flops"] == 20458240
    assert stable_seed("x", 1.0, 0) == stable_seed("x", 1.0, 0)
    return "20 LDPC + 7 Polar scalar configurations checked; no decoder/GPU claim"


if __name__ == "__main__":
    manifest = build()
    validation = validate(manifest)
    path = ROOT/"experiment_manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(validation)
    print(f"Manifest: {path}")
    for x in manifest["ldpc_configs"]:
        print(f'{x["id"]:28s} BG{x["base_graph"]} Z={x["Z"]:3d} '
              f'Kenc={x["K_encoder_including_filler"]:4d} F={x["filler_bits"]:3d} '
              f'Etx={x["E_tx_bits"]:5d} Rpayload={x["actual_payload_rate_A_over_E"]:.6f}')
