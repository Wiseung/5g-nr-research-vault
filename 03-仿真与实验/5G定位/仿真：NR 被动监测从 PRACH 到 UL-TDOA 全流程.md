---
title: 仿真：NR 被动监测从 PRACH 到 UL-TDOA 全流程
aliases:
  - 5G 定位全流程仿真
  - PRACH-PDCCH-PDSCH-TDOA 仿真台账
type: experiment
status: seed
created: 2026-09-04
tags:
  - domain/5g-nr
  - topic/定位
  - topic/tdoa
  - stage/simulation
  - stage/verification
  - process/end-to-end
  - evidence/personal-note
source:
  - 用户项目流程说明
  - 3GPP TS 38.211
  - 3GPP TS 38.213
  - 3GPP TS 38.214
  - 3GPP TS 38.305
simulation:
  - 仿真：NR 被动监测从 PRACH 到 UL-TDOA 全流程
related:
  - "[[5G 定位与 TDOA｜MOC]]"
  - "[[第三方 5G 定位项目接手与数据契约]]"
  - "[[仿真：PRACH 检测与 RA 事件关联]]"
  - "[[仿真：C-RNTI 驱动的 PDCCH-PDSCH 盲搜]]"
  - "[[仿真：多站 UL-TDOA 协同定位]]"
---

# 仿真：NR 被动监测从 PRACH 到 UL-TDOA 全流程

> [!abstract] 实验性质
> 这是端到端编排台账，不是已完成的系统结果。它把“连续同频 TDD 采集 → PRACH/RA 事件 → C-RNTI 关联 → PDCCH/PDSCH/PUSCH 资源解析 → 单用户截取 → 多站 UL-TDOA”拆成可单独验收的阶段，防止最终定位误差掩盖前端协议或采集问题。

## 1. 端到端数据流

```text
连续多站 I/Q + 配置/时钟元数据
    ↓
SSB/PBCH/帧同步与 TDD D/U/F 标注
    ↓
PRACH 检测：RO、preamble、TOA、功率、碰撞
    ↓
RA-RNTI → RAR（PDSCH 上的 MAC 内容）→ TEMPORARY-C-RNTI → Msg3/Msg4
    ↓
C-RNTI 候选池与 PDCCH/DCI 盲搜
    ↓
DCI 驱动 PDSCH/PUSCH 资源快照和 DM-RS
    ↓
单用户时频掩码、滤波/截断和质量评估
    ↓
跨站同一 event_id 的 UL-TOA/RTOA/TDOA
    ↓
校准、几何解算、残差/GDOP/置信度
```

每个箭头都要有可保存的中间 artifact；不能只保存最终位置。

## 2. 阶段输入/输出/门槛

| 阶段 | 输入 | 输出 | 进入下一阶段的门槛 |
|---|---|---|---|
| F0 同步 | 连续 I/Q、载波和采样参数 | 小区/帧/时隙/符号坐标、TDD 标签 | 坐标在已知测试帧上正确 |
| F1 PRACH | RACH 配置、检测窗 | 前导事件、TOA、峰轨迹、RO | 单前导 P0/P1 通过 |
| F2 RA 关联 | F1 事件 + RAR/Msg3/Msg4 | RA-RNTI、临时 C-RNTI、C-RNTI 状态 | 至少一个正例和错误关联负例 |
| F3 控制/数据 | C-RNTI 候选 + CORESET/SS | DCI、resource_snapshot、coding_snapshot | 已知候选 C0/C3 通过 |
| F4 单用户 | 资源快照、DM-RS/参考片段 | 掩码、滤波片段、ToA 质量 | 命中率/残余干扰有记录 |
| F5 多站 | F4 多站事件、时钟/延迟校准 | TDOA、位置、残差、GDOP | T0/T1 通过且不静默接收坏站 |

## 3. 统一事件和配置 ID

一个事件跨站、跨信号和跨阶段使用同一个 `event_id`，但每条证据保留自己的 `observation_id`：

```js
event_id: ""
observation_id: ""
config_id: ""
station_id: ""
frame_slot_symbol: ""
direction: "UL|DL|flexible|unknown"
signal: "PRACH|PDCCH|PDSCH|PUSCH|DM-RS|SRS"
payload_layer: "RAR(MAC)|DCI|DL-SCH|UL-SCH|RRC|PDCP|unknown"
association_state: "candidate|associated|ambiguous|rejected"
raw_artifact: ""
derived_artifact: ""
quality_flags: []
```

`event_id` 的生成规则要先定义：优先使用 C-RNTI + 时序/资源；只有 PRACH 阶段时使用 RO + preamble + 时间窗口，并明确碰撞风险。

## 4. 控制变量原则

每一轮只改变一个主因素：

1. 先固定载波、SCS、BWP、TDD、RACH、CORESET、搜索空间和站点几何。
2. 先运行理想同步/理想 CSI/单径，再加入一种前端误差。
3. 先用已知 C-RNTI，再测试 RA 驱动的有限候选池。
4. 先用 PRACH 或 DM-RS 已知序列做 ToA，再比较完整数据片段。
5. 先做三站二维，再加入四站冗余、未知钟差或三维。

不允许在同一曲线中同时改变 SNR、CFO、滤波器、站点几何和译码参数而不分层记录。

## 5. 结果与证据矩阵

| 证据 | 记录对象 | 说明 |
|---|---|---|
| 配置证据 | `config_snapshot` | 来自 SSB/MIB/SIB1/RRC、工具配置或明确假设 |
| 波形证据 | 原始 I/Q、网格、相关轨迹 | 可回放、保留时间戳和采样率 |
| 协议证据 | RNTI、DCI、MAC 字段、CRC | 区分候选通过与有效关联 |
| 资源证据 | PRB/RE/符号/端口掩码 | 局部与绝对坐标同时存在 |
| 测量证据 | ToA/RTOA、峰策略、校准项 | 记录 raw/corrected 两套值 |
| 定位证据 | TDOA、位置、GDOP、残差 | 记录有效站和置信区间 |
| 性能证据 | 检测率、BLER、延迟、丢帧 | 带样本量、种子和停止规则 |

## 6. 端到端最小正例/负例

### 正例

- 单 UE、单前导、无碰撞、已知 C-RNTI 或完整 4-step RA。
- 三站二维、理想公共时钟、单径、固定滤波器。
- 预期每阶段状态从 `sync_locked` → `preamble_detected` → `user_associated` → `toa_valid` → `tdoa_usable`。

### 负例

- 错误 PRACH occasion、错误 RNTI、错误 CORESET 或错误 DCI 字段。
- 同一 occasion 两个 UE 碰撞。
- 单站固定延迟、采样率漂移、CFO、NLOS 或近共线几何。

负例的目标是让系统输出明确的 `rejected`、`ambiguous` 或 `toa_unreliable`，而不是返回一个看似合理的坐标。

## 7. 实时化账本

| 模块 | 在线工作 | 需测的尾延迟/资源 |
|---|---|---|
| 采集与缓存 | DMA、丢样检查、时间戳 | 缓冲深度、丢帧率 |
| 同步/方向 | SSB、TDD D/U/F | 锁定时间、重锁次数 |
| PRACH | 相关器/峰筛选 | 每 occasion 计算量、峰保留数 |
| PDCCH | 候选循环、Polar/CRC | 候选数、最大尾延迟、RNTI 池大小 |
| 数据提取 | 网格掩码、DM-RS、滤波 | 每用户/每站处理时间 |
| TDOA 融合 | 对齐、WLS、异常站 | 融合周期、站间网络延迟 |

平均延迟不能替代 P95/P99 或最大尾延迟；实时定位还要记录跨站数据到达不同步造成的等待时间。

## 8. 全流程结果表模板

| run_id | 配置/Release | 站数 | RA 状态 | C-RNTI 状态 | PDCCH 结果 | 资源命中 | 单用户质量 | TDOA RMSE | 位置 RMSE | P95 延迟 | 故障状态 |
|---|---|---:|---|---|---|---|---|---:|---:|---:|---|
|  |  |  |  |  |  |  |  |  |  |  |  |

## 9. 依赖实验页

- F1：[[仿真：PRACH 检测与 RA 事件关联]]。
- F3：[[仿真：C-RNTI 驱动的 PDCCH-PDSCH 盲搜]]。
- F5：[[仿真：多站 UL-TDOA 协同定位]]。
- 理论/数据契约：[[第三方 5G 定位项目接手与数据契约]]、[[5G 定位与 TDOA｜MOC]]。
- 既有链路基线：[[仿真-无噪声编解码闭环]]、[[08 仿真实验：LS 与 MMSE]]、[[09 仿真实验：MIMO 均衡]]。

## 10. 可复现记录

- 代码仓库/提交号：
- MATLAB/5G Toolbox 版本：
- 运行环境和硬件：
- `config_id`/Release/条款版本：
- 中心频率、带宽、采样率确认记录：
- 随机种子和停止规则：
- 原始/派生 artifact 路径：
- 失败样本和异常说明：

## 11. 伪代码与 MATLAB/Python 阶段编排骨架

此处只实现端到端调度、artifact 账本和失败门控；F0-F5 的处理函数分别来自本页依赖实验或项目适配器。每阶段必须返回 `artifact` 和显式 `gate.pass/reason`，阶段失败时立即阻断后续处理，并先保存失败证据。

### 伪代码

```text
创建 run_id、config_id 和空阶段账本
按 F0→F1→F2→F3→F4→F5 顺序执行：
    调用当前阶段适配器(capture, 已完成阶段结果)
    保存输入快照、artifact、质量门结果和失败原因
    若 gate.pass 为假：标记 BLOCKED，停止，不调用下游阶段
全部阶段通过后标记 COMPLETE
持久化总账本，并确保所有 observation 都能追溯到 event_id/capture_id
```

### MATLAB

将函数保存为 `runPassivePipeline.m`。`adapters` 的六个字段都是项目函数句柄；它们分别实现前置实验页的同步、PRACH、RA 关联、PDCCH/DCI、单用户观测和 TDOA 处理。

```matlab
function ledger = runPassivePipeline(capture, adapters, outputDir)
stageNames = {'F0_sync', 'F1_prach', 'F2_ra', ...
    'F3_pdcch', 'F4_single_user', 'F5_tdoa'};
if ~isfolder(outputDir)
    mkdir(outputDir);
end

ledger = struct();
ledger.runId = string(capture.runId);
ledger.configId = string(capture.configId);
ledger.finalState = "RUNNING";
ledger.stageResults = cell(numel(stageNames), 1);

for k = 1:numel(stageNames)
    name = stageNames{k};
    try
        if ~isfield(adapters, name)
            error("Missing adapter: %s", name);
        end
        handler = adapters.(name);
        [artifact, gate] = handler(capture, ledger);
        assert(isstruct(gate) && isfield(gate, "pass") && ...
            isfield(gate, "reason") && isscalar(gate.pass), ...
            "每个阶段必须返回标量 gate.pass 和 gate.reason");
    catch ME
        artifact = struct("adapterError", string(ME.message));
        gate = struct("pass", false, "reason", string(ME.message));
    end

    record = struct("stage", name, "artifact", artifact, "gate", gate);
    ledger.stageResults{k} = record;
    runId = char(ledger.runId);
    artifactPath = fullfile(outputDir, ...
        sprintf("%s_%02d_%s.mat", runId, k, name));
    save(artifactPath, "record", "-v7.3");

    if ~gate.pass
        ledger.finalState = "BLOCKED_" + string(name);
        ledger.failedStage = string(name);
        ledger.failureReason = string(gate.reason);
        ledgerPath = fullfile(outputDir, ...
            char(ledger.runId + "_ledger.mat"));
        save(ledgerPath, "ledger", "-v7.3");
        return;
    end
end

ledger.finalState = "COMPLETE";
ledgerPath = fullfile(outputDir, char(ledger.runId + "_ledger.mat"));
save(ledgerPath, "ledger", "-v7.3");
end
```

### Python

```python
def run_passive_pipeline(capture, adapters, persist):
    """按门控顺序运行阶段适配器；persist 负责写入可回放 artifact。"""
    stage_names = (
        "F0_sync", "F1_prach", "F2_ra", "F3_pdcch",
        "F4_single_user", "F5_tdoa",
    )
    ledger = {
        "run_id": capture["run_id"],
        "config_id": capture["config_id"],
        "final_state": "RUNNING",
        "stages": {},
    }

    for stage in stage_names:
        try:
            if stage not in adapters:
                raise KeyError(f"missing stage adapter: {stage}")
            artifact, gate = adapters[stage](capture, ledger)
            if not isinstance(gate.get("pass"), bool) or "reason" not in gate:
                raise ValueError("adapter must return bool gate['pass'] and gate['reason']")
            record = {"artifact": artifact, "gate": gate}
        except Exception as exc:
            record = {
                "artifact": None,
                "gate": {"pass": False, "reason": f"adapter_error: {exc}"},
            }

        ledger["stages"][stage] = record
        persist(stage, record, ledger)
        if not record["gate"]["pass"]:
            ledger["final_state"] = f"BLOCKED_{stage}"
            ledger["failed_stage"] = stage
            ledger["failure_reason"] = record["gate"]["reason"]
            persist("ledger", ledger, ledger)
            return ledger

    ledger["final_state"] = "COMPLETE"
    persist("ledger", ledger, ledger)
    return ledger
```

将 `persist` 实现为写入 MAT/HDF5/JSON 加二进制波形索引的工程函数；原始 I/Q 不应直接塞入 JSON。各阶段适配器还应校验 `event_id`、`capture_id`、`config_id` 连续性，并在无法确认用户关联、ToA 质量或跨站事件一致性时返回失败/歧义门，不得用下游解算掩盖上游失败。

## 证据与出处

- `PERSONAL_NOTE`：用户提供的三阶段项目路线和第三方连续监测目标。
- `STANDARD + partial`：[[3GPP TS 38.211｜Physical channels and modulation]]、[[3GPP TS 38.212｜Multiplexing and channel coding]]、[[3GPP TS 38.213｜Physical layer procedures for control]]、[[3GPP TS 38.214｜Physical layer procedures for data]]。
- `STANDARD + partial`： [ETSI TS 38.305 V18.5.0](https://www.etsi.org/deliver/etsi_ts/138300_138399/138305/18.05.00_60/ts_138305v180500p.pdf)；标准定位架构与本项目定制被动 UL-TDOA 分开记录。
- `STANDARD + partial`： [ETSI TS 38.215 V17.2.0](https://www.etsi.org/deliver/etsi_ts/138200_138299/138215/17.02.00_60/ts_138215v170200p.pdf)；区分标准 SRS UL-RTOA 与项目 PRACH/PUSCH 相关峰 TOA。
- `EXPERIMENT + NEEDS_VERIFICATION`：本页是验收编排和结果模板，尚无端到端运行结果。

## 当前状态

尚未运行。建议按 F0→F1→F2→F3→F4→F5 顺序逐门验收，每门通过后才扩大场景；任何一门失败都回到对应中间 artifact 排查。
