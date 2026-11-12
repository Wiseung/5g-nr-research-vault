"""Executable statistical and unit checks, not a channel simulation."""
import argparse
import json
import math


def wilson(errors, frames, z=1.959963984540054):
    if frames <= 0 or not 0 <= errors <= frames:
        raise ValueError("Require N>0 and 0<=errors<=N")
    p = errors/frames
    den = 1+z*z/frames
    center = (p+z*z/(2*frames))/den
    half = z*math.sqrt(p*(1-p)/frames+z*z/(4*frames*frames))/den
    return max(0, center-half), min(1, center+half)


def zero_error_upper(frames, alpha=0.05):
    if frames <= 0:
        raise ValueError("Require N>0")
    return -math.expm1(math.log(alpha)/frames)


def esn0_db(ebn0_db, payload_bits, transmitted_bits, qm):
    return ebn0_db+10*math.log10(payload_bits/transmitted_bits*qm)


def n0_unit_es(ebn0_db, payload_bits, transmitted_bits, qm):
    return 10**(-esn0_db(ebn0_db, payload_bits, transmitted_bits, qm)/10)


def log_bler_crossing(points, target):
    # Only bracketed, monotone adjacent observations. No extrapolation.
    points = sorted(points)
    for (x0, p0), (x1, p1) in zip(points, points[1:]):
        if p0 >= target >= p1 and p0 > p1 > 0:
            w = (math.log10(target)-math.log10(p0))/(math.log10(p1)-math.log10(p0))
            return x0+w*(x1-x0)
    return None


def self_check():
    lo, hi = wilson(200, 2000000)
    assert lo < 1e-4 < hi and 8e-5 < lo and hi < 1.2e-4
    assert abs(zero_error_upper(1000000)*1000000-2.995728) < 1e-5
    assert abs(esn0_db(0, 1008, 2048, 2)-10*math.log10(1008/1024)) < 1e-12
    # QPSK energy Es=1, complex noise variance N0; each real noise variance N0/2.
    eb = 2.0
    n0_qpsk = n0_unit_es(eb, 1008, 2048, 2)
    n0_bpsk = n0_unit_es(eb, 1008, 2048, 1)
    assert abs(n0_bpsk-2*n0_qpsk) < 1e-12
    # Throughput in payload Mbps, not Gbps: the factor 1e6 is essential.
    traffic_bytes = 4*20*(4*(197*104)+2*(52*104))
    assert traffic_bytes == 7421440
    ideal_cw_per_s = 1e12/traffic_bytes
    payload_mbps = 1008*ideal_cw_per_s/1e6
    assert 135 < payload_mbps < 136
    assert log_bler_crossing([(1, 1e-2), (2, 1e-4)], 1e-3) == 1.5
    assert log_bler_crossing([(1, 1e-2), (2, 1e-4)], 1e-5) is None
    return {"status": "analytic_checks_passed_not_a_decoder_test",
            "example_200_errors_in_2M_frames": {"estimate": 1e-4, "Wilson95": [lo, hi]},
            "zero_errors_in_1M_one_sided95_upper": zero_error_upper(1000000),
            "illustrative_traffic_ceiling_payload_Mbps": payload_mbps,
            "runtime_example_240M_cw_at_10k_cw_s_hours": 240000000/10000/3600}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--frames", type=int)
    p.add_argument("--errors", type=int)
    args = p.parse_args()
    if args.frames is None and args.errors is None:
        result = self_check()
    elif args.frames is not None and args.errors is not None:
        result = {"bler": args.errors/args.frames, "Wilson95": wilson(args.errors, args.frames)}
        if args.errors == 0:
            result["one_sided_exact95_upper"] = zero_error_upper(args.frames)
    else:
        p.error("Supply both --frames and --errors, or neither for self checks")
    print(json.dumps(result, ensure_ascii=False, indent=2))
