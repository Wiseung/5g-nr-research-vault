"""RV0, single-CB NR LDPC/QPSK reference implementation for protocol v1."""
import hashlib
from importlib.resources import files

import numpy as np
import torch


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def crc_attach(payload, name):
    width, poly = (16, 0x1021) if name == "CRC16" else (24, 0x864CFB)
    reg = np.zeros(len(payload), dtype=np.uint32)
    for bit in payload.T:
        feedback = ((reg >> (width - 1)) ^ bit) & 1
        reg = ((reg << 1) ^ (feedback * poly)) & ((1 << width) - 1)
    crc = ((reg[:, None] >> np.arange(width - 1, -1, -1)) & 1).astype(np.uint8)
    return np.concatenate((payload, crc), axis=1)


class NRLink:
    def __init__(self, config, device="cuda"):
        self.cfg = config
        self.device = torch.device("cuda:0" if device == "cuda" else device)
        self.z = config["Z"]
        self.bg = config["base_graph"]
        self.b = config["B_including_tb_crc"]
        self.a = config["payload_bits_A"]
        self.k = config["K_encoder_including_filler"]
        self.n = config["N_full_graph"]
        self.etx = config["E_tx_bits"]
        self.rows, self.cols = (46, 68) if self.bg == 1 else (42, 52)
        self.kcols = self.cols - self.rows
        # Standard table only; the encoder and index builder below are independent.
        table = files("sionna.phy.fec.ldpc.codes").joinpath(f"5G_bg{self.bg}.csv")
        raw = table.read_bytes()
        self.shift_hash = hashlib.sha256(raw).hexdigest()
        from io import BytesIO
        csv = np.genfromtxt(BytesIO(raw), delimiter=";")
        self.base = np.full((self.rows, self.cols), -1, dtype=np.int64)
        row = 0
        for line in csv[2:]:
            if not np.isnan(line[0]):
                row = int(line[0])
            self.base[row, int(line[1])] = int(line[2 + config["i_LS"]]) % self.z
        rr, cc = np.where(self.base >= 0)
        self.rr, self.cc = rr, cc
        self.p = len(rr)
        assert self.p * self.z == config["graph_edges"]
        self.edge_row = torch.tensor(rr, device=self.device)
        self.var_np = cc[:, None] * self.z + (np.arange(self.z) + self.base[rr, cc, None]) % self.z
        self.var = torch.tensor(self.var_np, device=self.device)
        self.flat_var = self.var.flatten()
        degrees = np.bincount(rr, minlength=self.rows)
        self.buckets = []
        for degree in np.unique(degrees):
            row_ids = np.where(degrees == degree)[0]
            edge_ids = np.array([np.where(rr == r)[0] for r in row_ids])
            self.buckets.append((torch.tensor(row_ids, device=self.device),
                                 torch.tensor(edge_ids, device=self.device)))
        # Fixed-order VN gather/reduction avoids nondeterministic CUDA atomic sums.
        # Group by base-column degree; no global padded edge tensor is retained.
        self.variable_buckets = []
        column_degrees = np.bincount(cc, minlength=self.cols)
        for degree in np.unique(column_degrees):
            columns = np.where(column_degrees == degree)[0]
            edge_ids = np.array([np.where(cc == c)[0] for c in columns])
            shifts = self.base[rr[edge_ids], cc[edge_ids]]
            indices = edge_ids[:, :, None] * self.z + (np.arange(self.z) - shifts[:, :, None]) % self.z
            self.variable_buckets.append((torch.tensor(columns, device=self.device),
                                          torch.tensor(indices, device=self.device)))
        filler = np.zeros(self.n, dtype=bool)
        filler[self.b:self.k] = True
        self.filler = torch.tensor(filler, device=self.device)
        self.edge_nonfiller = (~self.filler[self.var]).float()
        # RV0 starts at zero in the circular buffer AFTER mandatory 2Z puncture.
        available = np.arange(2 * self.z, self.n)[~filler[2 * self.z:]]
        selected = np.resize(available, self.etx)
        self.tx_np = selected.reshape(2, -1).T.flatten()  # QPSK bit interleaver
        self.tx = torch.tensor(self.tx_np, device=self.device)
        self.index_hash = hashlib.sha256(self.tx_np.astype("<i8").tobytes()).hexdigest()
        self.nu = torch.bincount(self.tx, minlength=self.n)
        assert not self.filler[self.tx].any() and int(self.tx.min()) >= 2 * self.z

    def encode(self, payload):
        info = crc_attach(payload, self.cfg["tb_crc"])
        cw = np.zeros((len(payload), self.cols, self.z), dtype=np.uint8)
        cw.reshape(len(payload), -1)[:, :self.b] = info

        def parity(row, end):
            acc = np.zeros((len(payload), self.z), dtype=np.uint8)
            for col in np.where(self.base[row, :end] >= 0)[0]:
                acc ^= np.roll(cw[:, col], -int(self.base[row, col]), axis=1)
            return acc

        total = np.bitwise_xor.reduce([parity(r, self.kcols) for r in range(4)])
        pivot = 1 if self.bg == 1 else 2
        cw[:, self.kcols] = np.roll(total, int(self.base[pivot, self.kcols]), axis=1)
        for r in range(3):
            cw[:, self.kcols + r + 1] = parity(r, self.kcols + r + 1)
        for r in range(4, self.rows):
            cw[:, self.kcols + r] = parity(r, self.kcols + 4)
        return cw.reshape(len(payload), -1), info

    def recover(self, llr):
        out = torch.zeros((len(llr), self.n), device=self.device, dtype=llr.dtype)
        out.index_add_(1, self.tx, llr)
        return out.clamp(-20, 20).masked_fill(self.filler, 20)

    def channel(self, codeword, ebn0_db, rng, noiseless=False):
        bits = torch.tensor(codeword[:, self.tx_np], device=self.device, dtype=torch.float32)
        symbols = (1 - 2 * bits).reshape(len(bits), -1, 2) / np.sqrt(2)
        n0 = 1 / (self.a / self.etx * 2 * 10 ** (ebn0_db / 10))
        n0 = torch.as_tensor(n0, device=self.device, dtype=bits.dtype)
        if n0.ndim == 1:
            n0 = n0[:, None, None]  # independent Eb/N0 for each codeword
        if noiseless:
            llr = (1 - 2 * bits) * 20
        else:
            noise = torch.tensor(rng.standard_normal(tuple(symbols.shape)).astype(np.float32),
                                 device=self.device) * torch.sqrt(n0 / 2)
            llr = (2 * np.sqrt(2) * (symbols + noise) / n0).flatten(1)
        return self.recover(llr), llr

    def gather(self, values):
        return values[:, self.var]

    def scatter(self, edges):
        out = edges.new_zeros((len(edges), self.cols, self.z))
        flat = edges.flatten(1)
        for columns, indices in self.variable_buckets:
            out[:, columns] = flat[:, indices].sum(2)
        return out.flatten(1)

    def syndrome(self, values):
        aligned = self.gather(values)
        parity = torch.zeros((len(values), self.rows, self.z), device=self.device, dtype=torch.int64)
        unresolved = torch.zeros_like(parity)
        parity.index_add_(1, self.edge_row, (aligned < 0).long())
        unresolved.index_add_(1, self.edge_row, (aligned.abs() <= 1e-6).long())
        return parity.remainder(2), unresolved == 0

    def accepted(self, values):
        parity, resolved = self.syndrome(values)
        bits = (values[:, :self.b] < 0).cpu().numpy().astype(np.uint8)
        expected = crc_attach(bits[:, :self.a], self.cfg["tb_crc"])
        crc_ok = torch.tensor((bits == expected).all(1), device=self.device)
        filler_ok = (values[:, self.filler] > 1e-6).all(1)
        return (parity == 0).flatten(1).all(1) & resolved.flatten(1).all(1) & crc_ok & filler_ok

    def minsum(self, q):
        result = torch.empty_like(q)
        for _, edges in self.buckets:
            v = q[:, edges, :]
            mins, indices = v.abs().topk(2, dim=2, largest=False, sorted=True)
            positions = torch.arange(v.shape[2], device=self.device)[None, None, :, None]
            magnitude = torch.where(positions == indices[:, :, :1], mins[:, :, 1:2], mins[:, :, :1])
            negative = v < 0
            sign = 1 - 2 * (negative.long().sum(2, keepdim=True) - negative.long()).remainder(2)
            result[:, edges, :] = (magnitude * sign).to(q.dtype)
        return result

    def row_mean(self, edges):
        weighted = edges * self.edge_nonfiller
        total = edges.new_zeros((len(edges), self.rows))
        for rows, indices in self.buckets:
            denom = self.edge_nonfiller[indices].sum((-1, -2)).clamp_min(1)
            total[:, rows] = weighted[:, indices].sum((-1, -2)) / denom
        return total

    def masked_violation(self, values):
        parity, resolved = self.syndrome(values)
        return (parity * resolved).sum(-1) / resolved.sum(-1).clamp_min(1), resolved.float().mean(-1)

    def features(self, u, q, r, dr, prev_violation, t):
        violation, coverage = self.masked_violation(u)
        f = torch.stack((violation, violation - prev_violation, self.row_mean(q.abs()) / 20,
                         self.row_mean(r.abs()) / 20, dr / 40,
                         self.row_mean((1 - self.gather(u.clamp(-20, 20)).abs() / 2).clamp_min(0)),
                         torch.full_like(violation, t / 20), coverage), dim=-1)
        # Condition fractions use ALL row-neighbor slots, including filler.
        cond = []
        counts = self.nu[self.var]
        for val in ((counts == 0) & ~self.filler[self.var], self.filler[self.var],
                    (counts >= 2) & ~self.filler[self.var],
                    torch.log1p(counts.clamp_max(4).float()) / np.log(5)):
            total = u.new_zeros(self.rows)
            total.index_add_(0, self.edge_row, val.float().mean(-1))
            degree = torch.bincount(self.edge_row, minlength=self.rows)
            cond.append((total / degree)[None].expand(len(u), -1))
        zero = torch.zeros_like(violation)
        c = torch.stack((violation, violation - prev_violation, zero, zero, *cond), dim=-1)
        return f.detach(), c.detach(), violation.detach()

    def decode(self, lch, iterations=20, alpha=0.8, controller=None, eta=0.0, history=False):
        u = lch
        r = lch.new_zeros((len(lch), self.p, self.z))
        state = None
        prev, _ = self.masked_violation(u)
        dr = lch.new_zeros((len(lch), self.rows))
        outputs = []
        state_max = lch.new_zeros(())
        for t in range(iterations):
            q = (self.gather(u) - r).clamp(-20, 20)
            q = q.masked_fill(~self.edge_nonfiller.bool(), 20)
            damping = eta
            if controller is not None:
                f, c, now = self.features(u, q, r, dr, prev, t)
                damping, state = controller(f, c, state)
                state_max = torch.maximum(state_max, state.detach().abs().max())
                prev = now
                damping = damping[:, self.edge_row]
            new = ((1 - damping) * alpha * self.minsum(q) + damping * r).clamp(-20, 20)
            dr = self.row_mean((new - r).abs()).detach()
            r = new
            u = (lch + self.scatter(r)).masked_fill(self.filler, 20)
            if history and t >= iterations - 4:
                outputs.append(u.clamp(-20, 20))
        return u.clamp(-20, 20), outputs, state_max
