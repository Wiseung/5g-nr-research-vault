"""Protocol priority-1 controls; definitions fixed before endpoint test access."""
import math
import torch
from torch import nn

SPECS = {
    "mlp": {"width":24, "history":False, "definition":"x=W_in[features,embedding]; z=RMSNorm(x); h=tanh(W_drive z+W_condition c); eta=.5sigmoid(head(RMSNorm(x+W_out h)))"},
    "ema": {"width":24, "history":True, "definition":"Same current drive as MLP; h_t=a*h_prev+(1-a)*drive, learned constant per-channel a=sigmoid(theta), initial a=.5; zero initial state."},
    "gru": {"width":14, "history":True, "definition":"x=W_in[features,embedding]; z=RMSNorm(x)+W_condition c; h_t=GRUCell(z,h_prev), zero initial state; eta=.5sigmoid(head(RMSNorm(x+W_out h_t)))."},
}
class RowControl(nn.Module):
    def __init__(self, rows, kind):
        super().__init__()
        self.kind=kind
        d=SPECS[kind]["width"]
        self.embedding=nn.Parameter(torch.empty(rows,4))
        self.input=nn.Linear(12,d)
        self.norm=nn.RMSNorm(d,eps=1e-6)
        self.condition=nn.Linear(8,d,bias=False)
        if kind=="gru":
            self.cell=nn.GRUCell(d,d)
        else:
            self.drive=nn.Linear(d,d)
        if kind=="ema":
            self.theta=nn.Parameter(torch.zeros(d))
        self.out=nn.Linear(d,d)
        self.head_norm=nn.RMSNorm(d,eps=1e-6)
        self.head=nn.Linear(d,1)
        for mod in self.modules():
            if isinstance(mod,nn.Linear):
                nn.init.xavier_uniform_(mod.weight)
                if mod.bias is not None:nn.init.zeros_(mod.bias)
        if kind=="gru":
            for name,p in self.cell.named_parameters():
                if "weight" in name:nn.init.xavier_uniform_(p)
                else:nn.init.zeros_(p)
        nn.init.normal_(self.embedding,std=.02)
        nn.init.normal_(self.head.weight,std=1e-6)
        nn.init.constant_(self.head.bias,math.log(1/9))
    def forward(self,features,condition,state):
        embed=self.embedding[None].expand(len(features),-1,-1)
        x=self.input(torch.cat((features,embed),-1))
        z=self.norm(x)
        if self.kind=="gru":
            z=z+self.condition(condition)
            if state is None:state=torch.zeros_like(z)
            state=self.cell(z.flatten(0,1),state.flatten(0,1)).view_as(z)
        else:
            drive=torch.tanh(self.drive(z)+self.condition(condition))
            if self.kind=="ema":
                if state is None:state=torch.zeros_like(drive)
                a=torch.sigmoid(self.theta)
                state=a*state+(1-a)*drive
            else:state=drive
        y=x+self.out(state)
        return .5*torch.sigmoid(self.head(self.head_norm(y))),state

class StaticEta(nn.Module):
    """Nontrainable global eta, no state or condition use."""
    def __init__(self,eta):
        super().__init__();self.eta=float(eta)
    def forward(self,features,condition,state):
        return features[:,:,:1]*0+self.eta, features[:,:,:1]*0

