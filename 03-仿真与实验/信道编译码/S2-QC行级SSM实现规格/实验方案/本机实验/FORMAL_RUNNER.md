# S2 协议 v1 正式训练入口

`train_formal.py` 独立于限 500 步的调试脚本。本轮授权：RTX 4090 GPU0，两主配置 seed17 / batch64 各先训练 1001 步，覆盖完整 warmup 与首个 cosine 步；两项验收通过后，仅 BG2 同一 run 续训到 50000 步。BG1 留在 1001 步。首次 1001 步计入 BG2 的 50000 步预算。未提交或推送 Git。

## 固定协议与输入

以父目录实验方案 README 第 5 节和 manifest 为准。T20，随机 payload 和真实 TB CRC，FP32，禁用 TF32/AMP；AdamW、clip1、warmup1000 / cosine 到50k、第5001步启用 syndrome 线性升权，均保持协议默认值。`ssm.py` 未修改。正式训练使用 `results/20261113-163414-pilot-alpha/training_inputs_frozen.json` 冻结的 alpha、训练区间与五个验证 SNR；不把此前常数 LR 的短优化对照用作正式设置。

每 optimizer step 使用 64 个新样本。每帧三个独立 PCG64 流，由 split/config/train_seed/step/sample_index/stream 的稳定哈希确定，microbatch 分块不改变数据。当前实际使用 microbatch64，无梯度累积。

每1000步，五个固定 SNR 各20k帧进行 checkpoint 选择验证。每点32个shard，保留逐帧BCE、payload bit错误数、reject、CRC状态及聚合指标。最终按平均信息位BCE、较早step排序，预先冻结top2，再各补到100k/点；同一625帧shard前缀延长到3125，NMS基线也延长。重复使用的验证帧不是新增独立样本。这些是选择验证，独立正式test和BLER收益结论仍须后续完成。

## 启动与续训

解释器为仓库 `.cache/s2qc/venv/bin/python`。运行前设置 `CUDA_VISIBLE_DEVICES` 为已确认空闲的卡、`NVIDIA_TF32_OVERRIDE=0`、`CUBLAS_WORKSPACE_CONFIG=:4096:8`。本轮 detached supervisor 在 `logs/20261113-214206-formal50k/runner.py`，stdout/stderr直接分开写文件，无 shell 管道。

先运行 `verify_formal.py --output 新空目录 --frozen 冻结输入路径`。训练通过 `--proof` 指向其成功的 summary，绑定正式源码及输入哈希。基本命令为：

```bash
python -B -u train_formal.py --output <新空目录> \
  --config-id ldpc_B1024_R1-2_Q2 --seed 17 --batch 64 --stop-after 1001 \
  --frozen results/20261113-163414-pilot-alpha/training_inputs_frozen.json \
  --proof results/20261113-214206-formal50k-verify-03/summary.json
```

续训用同一输出目录、`--resume --stop-after 50000`。每100步及暂停点原子保存不可覆盖的 checkpoint，含模型、完整AdamW状态、全局步数、下一步LR、RNG、数据/源码/环境合约及SHA256。续训创建新日志segment；最近checkpoint之后未提交的日志若存在，按segment保留，聚合时以后续重放结果为准。每1000步先保存checkpoint，再验证；重启会核对并复用已经完成的验证，或补完未完成部分。

## CUDA graph 的最小平台适配及验证

PyTorch2.9.1 的两个调用阻止原计算图捕获，失败日志保留在 verify-formal-01/02：

1. `features()` 每轮 `bincount(edge_row)`：行度数不变，在 `NRLink.__init__` 缓存同一结果，仅替换重复计算。
2. `ProdBackward` 的 `sum().item()`：原生实现按是否存在零值，在除法和双向 exclusive cumprod 两条求导分支中选择。`CapturableProduct` 保留原 `prod` 前向及两条反向算术，改成设备端选择，数学定义不变。PyTorch v2.9.1 对应源码片段已保存到本轮logs。

`verify_formal.py` 对无零/单零/多零/全零连乘，对原始loss（包括syndrome边界）的梯度，及两配置连续7次更新进行逐元素一致验证；还验证采样分块、原信道、625/3125验证前缀、推理输出、checkpoint重建后下一步参数/梯度/AdamW状态和RNG，以及更新后符号对称性、状态界、无噪声译码。验收成功后才启用图重放；优化器与正确性检查仍在图外。图重放会覆盖grad缓冲，不跨step意外累积。

本轮完整命令/PID/session/stdout/stderr/退出码见 `logs/20261113-214206-formal50k/*/{launch,exit}.json`；原始源码快照与哈希见 `source_snapshot/`。结果与checkpoint位于 `results/20261113-214206-formal50k-{bg1,bg2}-seed17/`。失败目录和以往实验全部保留。
