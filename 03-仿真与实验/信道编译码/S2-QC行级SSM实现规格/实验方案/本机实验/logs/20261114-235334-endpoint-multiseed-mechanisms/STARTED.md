**独立目标区测试、多种子与机制消融：实际运行记录**

RUN_ID：20261114-235334-endpoint-multiseed-mechanisms。用户已授权依次完成独立细网格pilot、冻结200k帧/点T20配对测试、seed29/43和机制消融。GPU为原RTX4090 GPU0，FP32，TF32/AMP关闭；不提交或推送Git。

本轮从已归档BG2第24000步、BG1第42000步模型出发，alpha分别0.75/0.70。训练源码与已归档产物保持原样，新的测试、统计、控制模型与消融训练入口位于本轮code目录。

独立pilot已实际启动：PID1324979，session1324977。两个配置起始细网格分别为1.5:0.1:2.3和1.2:0.1:1.9 dB，每点20k帧、32shard。每帧NMS和S2共享payload及噪声。正式test使用不同split；两配置pilot均完成并审计后，按预登记的正错误数包围点规则冻结测试网格，所有点固定200k帧，无错误数提前停机。

后台流水线当前PID1332846，session1332845，已验证为独立POSIX会话。此前两个失败审计尝试保留在pipeline-failed-01/02，修复后从通过的pilot产物继续。步骤如下：

1. pilot完成及原始计数审计。
2. 新机制入口正确性验收（只做有限步实现对拍，不计入正式消融预算），在访问正式test前冻结机制源码。
3. 冻结测试网格，完成seed17配对测试、独立审计与中文报告。
4. 原正式runner依次完成BG2/BG1的seed29、seed43各50k×batch64；每个run独立审计，使用同一冻结test网格配对复现。
5. 静态eta验证集标定（0:.05:.50，五SNR各20k，top2补到100k），保留eta=.05初始化对照。
6. 行级MLP/EMA/GRU各两配置、seed17/29/43，全部同50k×batch64、同训练流与验证选模预算；分别独立测试。参数量相对SSM差异均在±10%内。
7. 最终汇总报告、先前归档哈希核验与本轮归档。

本优先级组包含新增4个SSM训练和18个神经机制对照，共22个正式run；这些是后台排队任务，不是已完成结果。按既有每run约3–7小时的记录，整个队列预计需数天，实际以退出记录为准。单卡顺序执行，保留已有400GPUh总协议上限，本轮另设160小时阶段墙钟保护上限；低于12GiB剩余磁盘时停止启动后续阶段，不删除历史产物。

- [预登记](preregistration.json)
- [测试入口验收](endpoint_verification.json)
- [首次同形状对拍问题及修复](endpoint-verification-incident.json)
- [机制定义与参数数目](mechanism_design_frozen.json)
- [统计模块验收](statistics_verification.json)
- [流水线阶段与最新采样/训练进度](pipeline_status.json)
- [pilot命令与PID](pilot/launch.json)
- [pilot stdout](pilot/stdout.log) · [stderr](pilot/stderr.log)
- [后台命令与PID](pipeline/launch.json)
- [后台 stdout](pipeline/stdout.log) · [stderr](pipeline/stderr.log)

每个阶段有独立launch.json、stdout.log、stderr.log和exit.json，直接子进程返回码不经过shell管道。任一正确性检查失败则保留日志并停止后续阶段，不把性能低于期望当作运行失败，也不据test结果重调模型或alpha。

完成后的报告保存在本机实验根目录，文件名以本RUN_ID开头。最终completion_audit.json仅在整个队列成功结束后生成；未生成前不能声称全轮已完成。细粒度状态以pipeline_status.json和各阶段exit.json为准。


2026-11-15 00:18后状态：pilot17点/34万独立观测已完成且审计通过；BG2测试点[1.8,1.9,2.0,2.1,2.2]、BG1测试点[1.5,1.6,1.7,1.8]已冻结，200k帧/点，共180万独立观测。测试PID1333736，session1333734，正在运行。见[startup_gate.json](startup_gate.json)和[尝试目录映射](attempt_locations.json)。后续22个训练run仍在队列中，尚未执行。
