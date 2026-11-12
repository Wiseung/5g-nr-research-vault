"""S2* arithmetic/storage planning and tiny QC algebra checks; standard library only.

This is not an NR encoder, a trained decoder, or a GPU benchmark.
Storage coefficients describe a planning ledger, not a framework peak guarantee.
"""
import json
import math
import random


def resources(z, batch=64, steps=20, layers=1, d=16, state=4, expand=1):
    rows, cols, base_edges = 42, 52, 197
    p, cond, row_embed, outputs = 12, 8, 4, 1
    inner = expand * d
    n, m, edges = cols * z, rows * z, base_edges * z
    params = (rows * row_embed + p * d + d
              + layers * (3*d*inner + inner*inner + 3*inner*state
                          + cond*inner + 2*d + 4*inner + 2*state)
              + d + d*outputs + outputs)
    # MAC=2 FLOPs. Biases, norms, activations, comparisons and indexing separate.
    row_step_poly = (2*p*d + layers*(6*d*inner + 2*inner*(inner+2*state)
                                   + 2*cond*inner + 8*inner*state)
                    + 2*d*outputs)
    ctrl_flops = steps * rows * row_step_poly
    # Explicit planning convention: 7E+N NMS + approximately 7E statistics.
    nms_stats_flops = steps * (14*edges + n)
    row_scratch = rows*(layers*inner*state + p
                       + layers*(5*d + 6*inner + 2*state) + outputs)
    inference_float_bytes = 4*batch*(5*edges + 3*n + row_scratch)
    inference_meta_bytes = batch*(4*n + m)
    graph_bytes = 8*edges  # Explicit flattened variable index per lifted edge.
    inference_plan = inference_float_bytes + inference_meta_bytes + graph_bytes + 4*params
    saved_per_step = (12*edges + 6*n
                      + rows*(p + layers*(inner*state + 6*d + 8*inner + 2*state)))
    saved_float_bytes = 4*batch*steps*saved_per_step
    saved_aux_bytes = batch*steps*(16*m + 2*edges + m)
    train_plan = inference_plan + saved_float_bytes + saved_aux_bytes + 12*params
    return {
        "Z": z, "B": batch, "N_graph": n, "M_checks": m, "E_edges": edges,
        "parameters": params, "state_floats_per_codeword": rows*layers*inner*state,
        "controller_poly_MFLOPs_per_codeword": ctrl_flops/1e6,
        "nms_stats_poly_MFLOPs_per_codeword": nms_stats_flops/1e6,
        "total_poly_MFLOPs_per_codeword": (ctrl_flops+nms_stats_flops)/1e6,
        "inference_planned_MiB": inference_plan/2**20,
        "training_planned_GiB": train_plan/2**30,
    }


Z = 4
EDGES = [(0,0,0), (0,1,1), (0,2,0),
         (1,0,2), (1,1,0), (1,3,0)]


def gather(x):
    return [[x[c*Z+(z+s)%Z] for z in range(Z)] for _,c,s in EDGES]


def scatter(x):
    out = [0.0]*(4*Z)
    for e,(_,c,s) in enumerate(EDGES):
        for z in range(Z):
            out[c*Z+(z+s)%Z] += x[e][z]
    return out


def syndrome_stats(post, masked):
    out = []
    for r in range(2):
        checks = []
        for z in range(Z):
            ids = [c*Z+(z+s)%Z for rr,c,s in EDGES if rr == r]
            resolved = all(abs(post[j]) > 1e-6 for j in ids)
            parity = sum(post[j] < 0 for j in ids) % 2
            if resolved or not masked:
                checks.append(parity)
        out.extend([sum(checks)/max(1,len(checks)), len(checks)/Z])
    return out


def codeword(rng):
    a = [rng.randrange(2) for _ in range(Z)]
    b = [rng.randrange(2) for _ in range(Z)]
    c = [a[z] ^ b[(z+1)%Z] for z in range(Z)]
    d = [a[(z+2)%Z] ^ b[z] for z in range(Z)]
    return a+b+c+d


def decode(ch):
    rmsg = [[0.0]*Z for _ in EDGES]
    post = list(ch)
    hist = [0.0, 0.0]
    for _ in range(5):
        stats = syndrome_stats(post, True)
        for rr in range(2):
            hist[rr] = 0.7*hist[rr] + 0.3*stats[2*rr]
        eta = [0.05+0.2*h for h in hist]
        g = gather(post)
        q = [[g[e][z]-rmsg[e][z] for z in range(Z)] for e in range(len(EDGES))]
        new = [[0.0]*Z for _ in EDGES]
        for e,(rr,_,_) in enumerate(EDGES):
            others = [j for j,(rj,_,_) in enumerate(EDGES) if rj==rr and j!=e]
            for z in range(Z):
                sign = math.prod(-1 if q[j][z]<0 else 1 for j in others)
                ms = 0.8*sign*min(abs(q[j][z]) for j in others)
                new[e][z] = (1-eta[rr])*ms + eta[rr]*rmsg[e][z]
        inc = scatter(new)
        post = [ch[v]+inc[v] for v in range(4*Z)]
        rmsg = new
    return post


def check_invariants():
    rng = random.Random(20261112)
    naive_failures = 0
    worst = 0.0
    for _ in range(200):
        x = [rng.uniform(-3,3) for _ in range(4*Z)]
        y = [[rng.uniform(-3,3) for _ in range(Z)] for _ in EDGES]
        gx, sy = gather(x), scatter(y)
        lhs = sum(gx[e][z]*y[e][z] for e in range(len(EDGES)) for z in range(Z))
        rhs = sum(x[v]*sy[v] for v in range(4*Z))
        assert abs(lhs-rhs) < 1e-10, "gather/scatter adjoint mismatch"
        c = codeword(rng)
        assert all(sum(c[cc*Z+(z+s)%Z] for rr,cc,s in EDGES if rr==r)%2==0
                   for r in range(2) for z in range(Z))
        ch0 = [0.0]*Z + [rng.uniform(-4,4) for _ in range(3*Z)]
        signs = [1-2*b for b in c]
        ch1 = [a*b for a,b in zip(ch0,signs)]
        assert syndrome_stats(ch0, True) == syndrome_stats(ch1, True)
        if syndrome_stats(ch0, False) != syndrome_stats(ch1, False):
            naive_failures += 1
        p0,p1 = decode(ch0),decode(ch1)
        err = max(abs(b-s*a) for a,b,s in zip(p0,p1,signs))
        worst = max(worst,err)
        assert err < 1e-10, "codeword sign symmetry mismatch"
    return {"toy_cases":200, "naive_hard_syndrome_counterexamples":naive_failures,
            "max_sign_symmetry_error":worst, "scope":"tiny_QC_algebra_only"}


if __name__ == '__main__':
    print(json.dumps({"checks":check_invariants(),
                      "budgets":[resources(z,b) for z,b in
                                 [(128,1),(128,64),(128,128),(256,64),(384,64)]]},
                     ensure_ascii=False, indent=2))
