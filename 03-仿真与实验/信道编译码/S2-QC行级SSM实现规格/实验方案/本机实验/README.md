# 本机第一阶段实验

本目录执行实验协议 v1 的链路校验和工程诊断。训练配置以 `../experiment_manifest.json` 为准，覆盖父目录旧 `train_Z` 草案。不会自动启动 50k 步训练。

## 小规模训练与噪声链路调试

第一阶段已于 2026-11-12 完成全部 20 配置校验。后续本机试跑使用独立入口：

```powershell
# 两主配置的独立 QPSK/LLR 数值核对、逐码字 SNR、真实低率重复恢复、CRC/零值拒收。
& .venv/Scripts/python.exe -B -u check_channel.py --output results/my-channel-check

# BG2 主配置，seed17、100步、batch8，每20步验证固定的随机码字/噪声。
& .venv/Scripts/python.exe -B -u train_smoke.py --output results/my-bg2-smoke

# BG1 主配置，另训一份控制器。
& .venv/Scripts/python.exe -B -u train_smoke.py --output results/my-bg1-smoke --config-id ldpc_B4096_R1-2_Q2
```

`train_smoke.py` 限制最多 500 步、batch<=64。默认每码字独立采样 0–2 dB 调试 SNR，常数 LR=1e-3、随机 payload/真实 CRC、T20、FP32、alpha=0.8。bias/norm/theta 不做 weight decay，梯度裁剪1，统计 detach、状态不 detach，syndrome 辅助损失按协议在前5000步为0。SNR 区间、步数和 LR 日程明确属于调试设置，不是正式训练配置。

`run_spec.json` 保存全部偏离正式训练的设置；`train_history.jsonl` 保存每步 loss、裁剪前梯度范数、状态界、含数据生成及反传/更新的同步耗时和 PyTorch 峰值分配显存。每次验证都重用固定码字/噪声，在0.5/1/1.5dB记录信息位BCE、载荷误帧/误比特和拒收，起始同时记录 NMS-F20 与未训练 SSM。仅保存最后一个 `smoke_checkpoint.pt`（`run_spec.formal_training=false`），不挑验证集最优检查点。结束时检查训练后符号对称性、控制器无噪声输出和保存/重载一致性。显存字段属于 PyTorch allocator，不是 NVML 进程显存；速度是工程试跑，不是协议正式基准。

`check_channel.py` 额外使用合法重算的 BG2 B512/R1/8 配置触发真实重复发送，并与 py3gpp 独立恢复逐值对拍，不修改主实验矩阵。QPSK 使用单位符号能量，检查 `L*sign` 的均值为 `2/N0`、方差为 `4/N0`；同载荷Eb/N0下与BPSK的bit LLR应一致。首轮 `20261112-noisy-channel` 失败来自检查脚本误用了BPSK的均值/方差，修正检查公式后的 `20261112-noisy-channel-02` 通过，原始失败日志保留。

调试又发现完整 LDPC 校验与 CRC 通过并不蕴含 filler=0：`20261112-noisy-channel-filler-repro` 保存了反例。`NRLink.accepted` 已增加显式 filler 一致性检查；修正后的完整噪声/重复/接收边界结果在 `results/20261112-noisy-channel-final/summary.json`。两份 100 步训练记录及结论见 [本机试跑报告](./20261112-本机试跑报告.md)。

实测环境：Windows、RTX 4060 Laptop 8GB、驱动 560.94、Python 3.14.2、PyTorch 2.10.0+cu126、Sionna 2.2.0、py3gpp 0.6.0。均使用 FP32，关闭 TF32/AMP。这里的性能数据仅属于本机。

## 环境与启动

在本目录 PowerShell 中执行：

```powershell
# 已建立的 .venv 复用本机既有 torch/numpy/scipy/py3gpp。
# 重建时先检查这些包版本，不能将以下两条视作独立环境的完整安装清单。
python -m venv --system-site-packages .venv
uv pip install --python .venv/Scripts/python.exe --no-deps sionna==2.2.0

# 两主配置快速检查，输出目录必须是新的。
& .venv/Scripts/python.exe -B -u run_local.py --mode quick --output results/my-quick

# 全 20 配置第一阶段，以隐藏后台进程运行，保存 PID 和 stdout/stderr。
./start_stage1.ps1
```

`results/<run_id>/launch.json` 保存 PID。`events.jsonl` 逐配置更新；成功结束生成 `summary.json`，失败生成 `failure.json` 并退出，不继续后续实验。`environment.json` 保存软件版本、源文件/manifest hash、运行参数与 Git 状态；`environment-freeze.txt` 是当次实际 Python 包快照。环境使用系统包继承，后续重跑必须核对快照。

## 实际执行内容

1. 校验冻结 manifest 与生成器一致，执行原有统计及 toy 代数检查。
2. 每配置 1000 个随机 payload 编码，验证完整图 Hc=0、filler=0。
3. 每配置 100 帧与 Sionna 对照完整母码字和发送位；与 py3gpp 对照 CRC、发送索引和恢复 LLR；Sionna SPA50 独立译码检查。LLR 正号代表 0，传给 Sionna 译码器时取负。
4. 每个 B<=2048 配置 10k 帧，B>=4096 配置 1k 帧，无噪声 NMS-F50。alpha=0.8 仅作未校准工程初值；若失败立即保留配置与日志并停止。
5. 两主配置检验 min1/min2 的 tie/zero、重复 LLR 先累加后截断、独立 NumPy 固定阻尼 NMS 对拍、SSM 状态界与一次有效优化更新前后的码字符号对称性。此更新是丢弃权重的梯度自检。
6. 两主配置各在 -2/0/2/4/6/8 dB 做固定 256 帧 NMS-F20 诊断，随机 payload、真实 CRC、QPSK/AWGN，保存错误计数和 CI。**它不代替协议的 -2:0.5:8、20k 帧/点 pilot，不据此冻结训练 SNR。**

`nr_link.py` 独立实现 Thangaraj 式 QC 编码、RV0 selection/交织、rate recovery、flooding NMS；仅标准移位表取自 Sionna 包，逐配置记录 hash。SSM 在 `ssm.py`，BG2/BG1 参数数目为 1857/1873，固定 T20、统计 detach、状态跨迭代保留梯度。消息 scatter 采用固定顺序的按列度分组 gather/reduce，避免 CUDA 原子加法的顺序差异被反馈放大。这是正确性参考实现，未作融合内核性能优化。

尚未完成：协议第5道公开曲线门（需冻结并复跑 2.1.0 notebook 原参数和参考图）、正式 pilot 与 alpha 校准、50k步三种子训练、其余神经/经典基线、早停/fallback、Polar。任一校验失败先排查；公开曲线门 pending 时不进入正式训练。

早期失败的 quick run 也保留：`quick-01` 是 Sionna 要求显式 `cuda:0` 的设备字符串适配问题，`quick-02` 暴露 CUDA 原子消息累加导致的对称性误差，`quick-03` 记录修正后的首轮成功检查。后续 run 的源文件 hash 才代表各自执行版本。
