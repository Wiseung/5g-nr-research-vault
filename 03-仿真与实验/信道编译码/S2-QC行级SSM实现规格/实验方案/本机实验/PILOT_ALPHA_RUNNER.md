# 固定N pilot、α标定与有界优化对照入口

本目录新增 `pilot_alpha.py` 和 `compare_optimization.py`。数学定义、协议v1及原 `experiment_manifest.json` 不变；它们不是50k正式训练runner，不解除 `train_smoke.py` 的500步上限。

2026-11-13实际运行记录使用 `20261113-163414-pilot-alpha`，预登记、后台监督与完整命令在同名 `logs/` 下，结果在同名 `results/` 下。硬件为已获授权的RTX4090，不能标为5090实验。

## pilot与标定

使用已确认的独立环境解释器执行。所有入口FP32、TF32/AMP关闭；GPU由外部 `CUDA_VISIBLE_DEVICES` 指定。直接运行前应先确认目标卡空闲。

```bash
python -B -u pilot_alpha.py --mode verify --output results/NEW_RUN/nms-verification --batch 625
python -B -u pilot_alpha.py --mode run --output results/NEW_RUN/calibration --verification results/NEW_RUN/nms-verification/summary.json --batch 625
```

`verify` 检查原实现与简化NMS/graph重放的逐元素一致性、分块一致性及20k→100k流前缀。`run` 要求校验结果的源码哈希与当前脚本一致，依次处理两个主配置：

1. 完整21点、每点20k的α=.8初始pilot。
2. 9个α、5个SNR、每点20k配对标定；top2各延长至100k。以平均payload BLER、平均轮数和α递增作字典序选择。
3. α改变时，用独立split重做完整pilot；冻结最终γ_ref和训练/验证SNR，不循环重选α。

交点以相邻正BLER点做log插值。目标未被包围时扩网格；上界为零误帧时在相邻点间补中点，每点仍固定20k，不加伪计数或外插。每点都有32个shard、逐帧错误/拒收/BCE、原始npz哈希、Wilson95%及零错误单侧exact上界。

固定shape graph只重放原FP32算子，不早停、不改变NMS公式，不用于硬件排名。默认batch625必须整除每shard625帧；可用125或25等较小合法值。改batch后应重做验收。

输出目录初始为空。pilot中断可显式添加 `--resume`：已完成点必须通过原npz哈希核验，才会复用；未完成点重新采样，不累计重复帧。若修复脚本，先保留原源码/环境/失败日志，再重新执行 `verify`，并使用新的日志阶段名启动。不要覆盖旧运行证据。

## 独立优化对照

```bash
python -B -u compare_optimization.py --calibration results/NEW_RUN/calibration/summary.json --output results/NEW_RUN/optimization --steps 500
```

固定两个配置、三种子17/29/43、batch8，比较常数LR1e-3与协议1000步warmup的前500步。步数只允许1..500。不同设置共用初始化、训练观测流与固定验证集，并自动对拍；α和SNR均取已冻结的标定结果。输出逐步梯度裁剪前后范数、head份额、参数更新、η分布、loss、耗时和显存。

默认五个SNR各256固定验证帧，在0/250/最终步验证。最终检查点保存模型、AdamW及run_spec；检验重载输出和优化器状态一致性，检查训练后对称性、状态界和无噪声合法码字。`--resume` 只跳过已完整完成的run，不实现单个run的中途精确续训。

该入口是早期优化诊断：batch8、500步和256验证帧不同于正式协议；没有走到完整warmup/cosine，也不提供正式BLER收益或最终优化设置排名。所有试验结果与总预算均应公开，不能只展示最好种子。

## 可靠后台运行与审计

本轮 `logs/20261113-163414-pilot-alpha/runner.py` 使用POSIX setsid监督进程，stdout/stderr直接写独立日志文件，并保存实际命令、PID、session和原始退出码，不使用吞错管道。该监督脚本固定本轮GPU0的UUID；用于其他主机前须按实际卡修改并记录。

`after_calibration.py` 仅在完整pilot/α结果及其退出码通过后，顺序启动冻结模型梯度探针、Sionna噪声参考、优化对照、CPU产物验收和报告。失败立即中断后续阶段，已有结果保留。

正式50k runner仍需另行实现：有效batch64、microbatch无关样本键、完整优化日程、正式验证预算、断点续训和RNG/优化器/数据索引恢复，不能将本入口上限改大替代。
