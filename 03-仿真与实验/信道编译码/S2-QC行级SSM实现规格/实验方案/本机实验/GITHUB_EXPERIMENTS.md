# 2026-11-22 S2-QC 实验关键交付

本页是已完成的 RTX 4090 实验入口。根实验 commit 为 `606439166812f97fb42e30ae3dcfec58ec2b35f9`；本次提交归档此后已实际执行的代码、结果和审计，不代表另一次训练。协议以父目录的协议 v1 与 manifest 为准。

## 已完成内容

| 内容 | 结果 |
|---|---|
| 两主配置 | BG2 B1024 R1/2 QPSK；BG1 B4096 R1/2 QPSK |
| 正式训练 | SSM、MLP、EMA、GRU，各两配置、seed17/29/43，合计24次50k×batch64 |
| 队列范围 | 22次训练；另外2次SSM seed17来自队列前已完成训练，不能重复计数 |
| 配对测试 | SSM/MLP/EMA/GRU三种子各一组，静态阻尼一组，合计13组，全部独立审计通过 |
| 测试预算 | 每组9个SNR点，每点200k帧；共用同一180万帧信道观测，不能累计为13倍独立样本 |
| 完成时间 | 2026-11-22 08:05 +08:00；监督进程08:06退出0 |

固定T20、FP32、TF32/AMP关闭，无早停/fallback。NMS alpha在独立验证集标定后冻结（BG2=0.75，BG1=0.70），选模型依据验证BCE，未以test改选checkpoint。固定测试网格：BG2 1.8/1.9/2.0/2.1/2.2 dB；BG1 1.5/1.6/1.7/1.8 dB。

结果表：

- [逐训练指标与选定模型](exports/20261122-key-results/training.csv)：24行，包含验证BCE、裁剪比例、平均秒/步、峰值allocated/reserved显存及checkpoint哈希。
- [各方法、种子的1e-3门限与配对区间](exports/20261122-key-results/thresholds.csv)。
- [各测试点的原始计数与聚合指标](exports/20261122-key-results/test_points.csv)。
- [选定模型索引](exports/20261122-key-results/selected_models.json)：保留实验规格，同时提供仓库相对checkpoint路径，24个checkpoint均随本次交付保存。
- [完整终点实验报告](20261114-235334-endpoint-multiseed-mechanisms-独立终点测试与多种子机制对照进展.md)。
- [完成审计](logs/20261114-235334-endpoint-multiseed-mechanisms/completion_audit.json)。

当前结果支持这些控制器在指定NR配置、固定T20、1e-3附近相对父NMS的改善；BG2不同控制器收益接近，BG1有明显训练种子差异。尚不能仅据此主张SSM时间记忆独立优于MLP/EMA/GRU。配对bootstrap区间是固定模型的采样不确定性，不包含训练种子不确定性或插值模型误差。正式方法间配对差异、全部论文基线、泛化及低BLER深测仍待完成。

## 数学与可执行代码

- [本地链路入口](README.md) 与 [协议v1](../README.md)；旧文档中的“尚未训练”等内容是其编写时状态，应结合本页及最终报告阅读。
- [正式训练核心](formal_core.py)、[50k runner](train_formal.py)、[正式正确性校验](verify_formal.py)。`train_smoke.py`仍保持500步调试上限。
- [pilot/alpha标定](pilot_alpha.py)、[入口说明](PILOT_ALPHA_RUNNER.md)、[早期独立优化对照](compare_optimization.py)。
- [正式runner适配说明](FORMAL_RUNNER.md)：常量行度数缓存与等价的可捕获连乘反向分支。
- [机制模型](logs/20261114-235334-endpoint-multiseed-mechanisms/code/mechanisms.py)、[机制训练](logs/20261114-235334-endpoint-multiseed-mechanisms/code/train_mechanism.py)、[终点测试](logs/20261114-235334-endpoint-multiseed-mechanisms/code/endpoint.py)、[独立审计](logs/20261114-235334-endpoint-multiseed-mechanisms/code/audit.py)。

实际环境：Python3.12.16、PyTorch2.9.1+cu128、CUDA12.8 runtime、驱动535.183.01、Sionna2.2.0、py3gpp0.6.0、NumPy2.2.6、SciPy1.15.3。完整依赖快照在 campaign logs 的 `environment-freeze.txt`。这是RTX4090实测，不属于RTX5090实验，也不与4060混合排名。

2026-11-18发现GPU0显存读写数据损坏，迁移到空闲GPU3，完成80GiB显存对照、失败分片、链路及模型验收，再恢复队列。旧BG1异常分片隔离后重算。见 [硬件故障与恢复报告](20261118-GPU0显存异常定位与GPU3恢复报告.md)。外部guard、实际runner、stage命令/退出码和原冻结源码一并保存。历史训练只做了报告中披露范围的验证重放，不能由此证明所有历史GPU0运算均无污染。

## 获取后如何校验

在仓库根目录运行（此项仅需Python标准库，不使用GPU）：

```bash
python3 -B "03-仿真与实验/信道编译码/S2-QC行级SSM实现规格/实验方案/本机实验/exports/20261122-key-results/verify_export.py"
```

它核对发布文件的SHA256、24个选定checkpoint、24个训练汇总和13组测试审计，并核对关键核心源码与实验冻结哈希。详细清单见 [files.sha256.json](exports/20261122-key-results/files.sha256.json)，范围说明见 [scope.json](exports/20261122-key-results/scope.json)。

## 原始记录与复跑边界

本次是关键材料归档：逐帧test/validation npz、完整train_history.jsonl、非选中checkpoint、大型故障数组与完整原始哈希索引继续保留在原服务器，不纳入Git。论文下载文件也不在本交付范围。发布的各点JSON保留32分片统计与原始npz哈希，但克隆后没有这些npz，不能将上述轻量校验称为重新执行完整逐帧独立审计。

历史JSON和checkpoint保留原机绝对路径、源码哈希字典和环境身份，没有为了发布重写实验记录。克隆到其他路径后，可使用模型索引的 `checkpoint_repository_path` 定位权重；直接运行历史runner/endpoint需要显式配置新的输出目录、设备、冻结输入和路径映射，重新执行环境与源码proof。不能将历史`completion_audit`当作新机器已通过的proof。旧报告中“本轮没有Git提交或推送”描述当时的实验执行，本次用户授权的归档推送发生在全部实验完成之后。

后续训练使用独立输出目录；已有记录保持原样。`export_key_results.py`是本次发布白名单的生成脚本，依赖原服务器保留的完整归档；仅需核验本次交付时运行上面的 `verify_export.py` 即可。
