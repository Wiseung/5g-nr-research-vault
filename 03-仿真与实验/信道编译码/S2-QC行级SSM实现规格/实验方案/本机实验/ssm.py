"""Default J=1,d=16,s=4 normalized-ZOH controller; not official Mamba."""
import math

import torch
from torch import nn
from torch.nn import functional as F


class RowSSM(nn.Module):
    def __init__(self, rows):
        super().__init__()
        self.embedding = nn.Parameter(torch.empty(rows, 4))
        self.input = nn.Linear(12, 16)
        self.norm = nn.RMSNorm(16, eps=1e-6)
        self.drive = nn.Linear(16, 16)
        self.gate = nn.Linear(16, 16)
        self.delta = nn.Linear(16, 16)
        self.condition_delta = nn.Linear(8, 16, bias=False)
        self.bsel = nn.Linear(16, 4)
        self.csel = nn.Linear(16, 4)
        self.theta = nn.Parameter(torch.empty(16, 4))
        self.skip = nn.Parameter(torch.ones(16))
        self.out = nn.Linear(16, 16)
        self.head_norm = nn.RMSNorm(16, eps=1e-6)
        self.head = nn.Linear(16, 1)
        for mod in self.modules():
            if isinstance(mod, nn.Linear):
                nn.init.xavier_uniform_(mod.weight)
                if mod.bias is not None:
                    nn.init.zeros_(mod.bias)
        nn.init.normal_(self.embedding, std=0.02)
        nn.init.zeros_(self.delta.weight)
        nn.init.zeros_(self.condition_delta.weight)
        nn.init.constant_(self.delta.bias, math.log(3 / 4))
        rates = 1 / torch.tensor([1., 2., 4., 8.])
        with torch.no_grad():
            self.theta.copy_(torch.logit((rates - 1 / 32) / (2 - 1 / 32)).expand(16, -1))
        nn.init.normal_(self.head.weight, std=1e-6)
        nn.init.constant_(self.head.bias, math.log(1 / 9))

    def forward(self, features, condition, state):
        embedding = self.embedding[None].expand(len(features), -1, -1)
        x = self.input(torch.cat((features, embedding), -1))
        z = self.norm(x)
        drive, gate = torch.tanh(self.drive(z)), torch.sigmoid(self.gate(z))
        delta = 0.25 + 1.75 * torch.sigmoid(self.delta(drive) + self.condition_delta(condition))
        b, c = torch.tanh(self.bsel(drive)), torch.tanh(self.csel(drive))
        rate = 1 / 32 + (2 - 1 / 32) * torch.sigmoid(self.theta)
        decay = torch.exp(-delta[..., None] * rate)
        if state is None:
            state = torch.zeros_like(decay)
        state = decay * state + (1 - decay) * b[..., None, :] * drive[..., None]
        y = (c[..., None, :] * state).sum(-1) + self.skip * drive
        x = x + self.out(gate * y)
        return 0.5 * torch.sigmoid(self.head(self.head_norm(x))), state


def training_loss(link, history, info, step):
    labels = torch.tensor(info, dtype=torch.float32, device=link.device)
    bce = sum(weight / 15 * F.binary_cross_entropy_with_logits(-llr[:, :link.b], labels)
              for weight, llr in zip((1, 2, 4, 8), history))
    soft = torch.tanh(link.gather(history[-1]) / 2)
    products = []
    for _, edges in link.buckets:
        products.append(soft[:, edges].prod(2).flatten(1))
    syndrome = (1 - torch.cat(products, dim=1)).mean() / 2
    coefficient = 0.02 * min(1, max(0, (step - 5000) / 5000))
    return bce + coefficient * syndrome
