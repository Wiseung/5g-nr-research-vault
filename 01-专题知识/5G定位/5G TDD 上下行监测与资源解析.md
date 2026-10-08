---
title: 5G TDD 上下行监测与资源解析
aliases:
  - NR 同频上下行监测
  - 5G TDD 被动监测
type: atomic
status: seed
created: 2026-09-04
tags:
  - domain/5g-nr
  - domain/tdd
  - topic/定位
  - topic/资源解析
  - stage/接收机
  - evidence/3gpp
source:
  - 3GPP TS 38.211
  - 3GPP TS 38.213
  - 3GPP TS 38.331
  - 用户项目流程说明
related:
  - "[[5G 定位与 TDOA｜MOC]]"
  - "[[NR PRACH 检测与 RA-RNTI-C-RNTI 关联]]"
  - "[[NR PDCCH 盲搜与 PDSCH-PUSCH 资源解析]]"
  - "[[01 5G 物理层与信道模型]]"
  - "[[06 OFDM 接收与频域均衡]]"
---

# 5G TDD 上下行监测与资源解析

> [!abstract] 一句话结论
> TDD 在同一载频上按时域资源切换 D（下行）、U（上行）、F（灵活）和 guard 符号；“上下行同时监测”在本项目中应理解为连续采集同一频段并并行解析两种方向，而不是在同一个 OFDM 符号内假设上下行同时发射。

本页把 `guard` 作为工程采集/切换保护标记；规范 slot format 的方向主类仍是 D/U/F，具体保护时段和边界要以当前网络配置为准。

## 1. 项目中的边界

本页把项目目标抽象为一个第三方接收机的资源解析链：

```text
连续 I/Q 采集
    ↓
载频、采样率、粗定时和频偏校正
    ↓
SS/PBCH 同步与小区参数恢复（若可用）
    ↓
MIB/SIB1/RRC/TDD 资源配置快照
    ↓
按帧、时隙、OFDM 符号标注 DL/UL/flexible/guard
    ↓
分别进入 PRACH、PDCCH、PDSCH、PUSCH、DM-RS/SRS 解析器
    ↓
为用户关联、单用户截取和 TDOA 保存带坐标的观测量
```

这是项目的 `PERSONAL_NOTE` 工作模型；标准条款、设备能力和当前网络配置仍需逐项核对，不能由流程图推断。

## 2. “同频同时监测”的准确解释

| 说法 | 在接收机中的准确含义 | 不能直接推出的结论 |
|---|---|---|
| 同一个频段 | UL/DL 使用同一载频或载波带宽 | 不代表两方向在同一时刻占用同一资源 |
| 同时监测 | 连续采样、缓存并对 DL/UL 分支并行处理 | 不代表可跳过 TDD slot format |
| 上下行信息全流程解析 | 对各物理信道恢复资源、同步、控制和数据参数 | 不代表一定能解出所有用户 |
| 第三方接收 | 不参与网络调度和随机接入，只利用可观测空口信号 | 不天然拥有 RRC、C-RNTI 或受上层安全保护的业务内容 |

TDD 符号类别和切换周期由网络配置及版本决定。`DL/UL/flexible` 的具体模式、保护间隔、SCS、BWP 和载波关系应作为 `config_snapshot` 保存，而不是在代码中写死一个时隙模板。

## 2.1 下行与上行定位测量的边界

固定第三方站对下行波形测得的是不同下行发射点到这些站的到达差；它可用于小区/帧同步、配置恢复或下行发射源分析，但不能仅凭该差分直接给出 UE 坐标。项目的 UE 定位主观测应优先来自多个站同时接收的上行 PRACH、PUSCH、SRS 或已知上行参考片段。

3GPP 的 DL-TDOA、UL-TDOA 和 OTDOA 有各自的测量主体与协议流程；本项目采用的第三方被动方案需要单独标为工程假设。详见 [[多站 UL-TDOA 定位与同步]]。

## 3. 资源坐标契约

为了让 PRACH、PDCCH/PDSCH 和多站测量可以互相引用，每个观测应至少携带：

$$
q=(\mathrm{cell},\mathrm{carrier},\mathrm{bwp},\mathrm{frame},\mathrm{slot},\mathrm{symbol},\mathrm{subcarrier},\mathrm{port},\mathrm{direction})
$$

其中 `direction` 是 `DL`、`UL`、`flexible` 或 `unknown`。资源网格局部下标和绝对频率下标必须同时保存；现有 [[3GPP TS 38.211｜Physical channels and modulation]] 已明确提醒二者不能默认相等。

建议把每个资源解析结果分成三层：

1. **配置层**：载波、SCS、BWP、Point A、TDD 配置、CORESET、搜索空间、RACH 配置。
2. **观测层**：采样起止、相关峰、能量、频偏、定时偏移、占用 RE 和置信度。
3. **协议层**：RA-RNTI、TEMPORARY-C-RNTI、C-RNTI、DCI、PDSCH/PUSCH 调度和 HARQ 状态。

三层要保留版本或时间戳。配置切换后继续使用旧资源掩码，会把正确的波形误判为译码失败。

## 4. 接收机最小前置条件

| 前置项 | 作用 | 缺失时的风险 |
|---|---|---|
| 采样时钟与载频 | 把样点映射到时间/频率 | TDOA 偏差、ICI、相关峰展宽 |
| SS/PBCH 或等价小区同步 | 建立帧、时隙和小区标识 | 无法可靠解释符号坐标 |
| MIB/SIB1/RRC 配置 | 恢复 BWP、TDD、RACH、CORESET/搜索空间 | 盲搜空间膨胀或资源错位 |
| PRACH 资源配置 | 生成候选前导与检测窗 | 只能做宽泛能量检测 |
| 站点时钟/硬件延迟标定 | 让多站时间差可比较 | 定位偏差无法由算法消除 |

如果当前数据采集尚未包含 MIB/SIB1/RRC，先把缺失字段标为 `NEEDS_VERIFICATION`，不要用“常见 5G 配置”代替。

## 5. 与现有 5G 笔记的接口

| 本页环节 | 已有笔记 | 需要继承的约定 |
|---|---|---|
| 资源网格/OFDM | [[01 5G 物理层与信道模型]]、[[06 OFDM 接收与频域均衡]] | FFT、CP、$k/l$ 或 $k/m$ 轴、功率归一化 |
| 参考信号 | [[02 参考信号与导频设计]]、[[DM-RS]]、[[SRS]] | 观测对象、端口/层、序列和有效时间 |
| 控制盲检 | [[3GPP TS 38.213｜Physical layer procedures for control]]、[[NR-DCI 编码链]] | CORESET、搜索空间、候选、RNTI CRC、失败状态 |
| 数据解析 | [[3GPP TS 38.214｜Physical layer procedures for data]]、[[NR-DL-SCH 编码链]]、[[NR-UL-SCH 编码链]] | resource_snapshot、coding_snapshot、RV、DM-RS |
| 信道模型 | [[3GPP TR 38.901｜Channel model]] | TDL/CDL、多普勒、同步和 CP 影响分层 |

## 6. 第三方监测的输出状态

不要把“有能量”“相关峰通过”“CRC 通过”和“可用于定位”合并成一个布尔值。建议使用以下状态：

| 状态 | 含义 |
|---|---|
| `energy_seen` | 窗口内存在超过门限的能量 |
| `sync_locked` | 已建立可复用的时间/频率参考 |
| `resource_mapped` | 能把观测映射到具体时频资源 |
| `candidate_crc_pass` | 某候选控制/数据链通过相应 CRC |
| `user_associated` | 已有跨消息、跨时隙的用户关联证据 |
| `toa_valid` | 定时估计质量满足本轮测量门限 |
| `tdoa_usable` | 多站时间戳、校准和残差均通过门限 |

例如 `candidate_crc_pass` 不等于 `user_associated`；错误候选也可能出现低概率 CRC 通过，需结合 RNTI、字段合法性、时序连续性和资源占用再判定。

## 7. 采集与解析日志

每个站点、每个事件至少保存：

```yaml
station_id: ""
capture_id: ""
sample_rate_hz: null
center_frequency_hz: null
clock_reference: ""
hardware_delay_samples: null
cell_id: null
frame_slot_symbol: ""
direction: "DL|UL|flexible|unknown"
bwp_and_tdd_snapshot: ""
channel_or_signal: "PRACH|PDCCH|PDSCH|PUSCH|DM-RS|SRS"
resource_indices: ""
association_key: ""
timing_offset_samples: null
frequency_offset_hz: null
quality_flags: []
```

原始 I/Q、解析后的资源网格和协议字段应能通过 `capture_id` 互相追溯。只保存最终 C-RNTI 或定位坐标会丢失故障定位所需的中间证据。

## 8. 最小验收顺序

1. 单站、单小区、单个已知 PRACH 前导的无噪声或高 SNR 采集。
2. 只验证帧/时隙/符号坐标和 PRACH 相关峰，不引入 PDCCH/PDSCH 盲搜。
3. 加入 TDD UL/DL/flexible 标记，检查方向分支没有跨符号泄漏。
4. 用已知 RNTI 的控制链验证 PDCCH 候选和 DCI 字段，再接 PDSCH/PUSCH。
5. 最后接入多站时间戳、硬件延迟和 TDOA 解算。

每一步都应保留 `pass/fail` 原因和输入快照。现有 [[仿真-无噪声编解码闭环]] 的“先边界、后全链”原则适用于这里。

## 9. MATLAB 示例：按配置标注 TDD 方向

方向矩阵应由当前小区的 RRC/TDD 配置解析得到，行对应采集窗口内的时隙，列对应时隙内 OFDM 符号。下面的代码只负责把已解析的方向映射到资源事件；它不内置任何固定 TDD pattern。

```matlab
% directionGrid: Nslot-by-Nsymbol string/cell array，值为 D/U/F/G/unknown
% nSymbolsPerSlot: 来自当前 CP/numerology 配置，不在这里假设固定值
% slotRow、symbolColumn: 相对于该快照的 MATLAB 1-based 坐标
% events 至少含 slotRow、symbolColumn、captureId、resourceId
directionGrid = upper(string(directionGrid));
assert(size(directionGrid, 2) == nSymbolsPerSlot, ...
    "每时隙符号数必须与当前 numerology 配置一致");
assert(all(events.slotRow >= 1 & events.slotRow <= size(directionGrid, 1)));
assert(all(events.symbolColumn >= 1 & ...
    events.symbolColumn <= size(directionGrid, 2)));

linearIndex = sub2ind(size(directionGrid), ...
    events.slotRow, events.symbolColumn);
events.direction = directionGrid(linearIndex);
allowed = ["D", "U", "F", "G", "UNKNOWN"];
assert(all(ismember(events.direction, allowed)), ...
    "方向值不合法；保留 unknown，不要猜测方向");

events.isDownlink = events.direction == "D";
events.isUplink = events.direction == "U";
events.isFlexibleOrUnknown = ismember(events.direction, ...
    ["F", "G", "UNKNOWN"]);
events.configSnapshotId = repmat(string(configSnapshotId), height(events), 1);

% flexible/guard/unknown 不会被误送入 DL 或 UL 专用解析分支
dlEvents = events(events.isDownlink, :);
ulEvents = events(events.isUplink, :);
deferredEvents = events(events.isFlexibleOrUnknown, :);
```

`directionGrid` 和 `configSnapshotId` 必须与同一份已核验配置绑定；如果项目内部把 guard 仅作为采集保护标记，应在导入时保留其来源，不要把它等同于规范 D/U/F 方向字段。

## 证据与出处

- `PERSONAL_NOTE`：用户提供的项目流程说明，描述第三方同频 TDD 监测、PRACH 触发用户区分、C-RNTI 后续盲搜以及多站 TDOA 目标。
- `STANDARD + partial`：[[3GPP TS 38.211｜Physical channels and modulation]]、[[3GPP TS 38.213｜Physical layer procedures for control]]；本地页覆盖资源和控制边界，但具体网络 Release/TDD 表格仍需核对。
- `PERSONAL_NOTE`：[[02 参考信号与导频设计#2.8 PRACH 前导与信道估计的区别]]、[[01 5G 物理层与信道模型]]、[[06 OFDM 接收与频域均衡]]。
- `NEEDS_EXTERNAL_REFERENCE`：TS 38.331 的当前 RRC 字段、运营商实际 TDD 配置和设备采集接口尚未在本库核验。
- `NEEDS_EXTERNAL_REFERENCE`：D/U/F 与 flexible/guard 的具体时隙格式应按 TS 38.213 §11.1 和项目网络配置核对。
- `NEEDS_EXTERNAL_REFERENCE`：可先查看 [ETSI TS 38.213 V17.7.0](https://www.etsi.org/deliver/etsi_ts/138200_138299/138213/17.07.00_60/ts_138213v170700p.pdf) §11.1 的 D/U/F 术语，再以项目锁定版本核对。
- `NEEDS_EXTERNAL_REFERENCE`：可参考 [MathWorks NR 小区搜索与 MIB/SIB1 恢复示例](https://www.mathworks.com/help/5g/ug/nr-cell-search-and-mib-and-sib1-recovery.html)，但示例假设、函数签名和本机工具箱版本仍需核对。

## 当前状态

- `EXPERIMENT + NEEDS_VERIFICATION`：尚无本项目真实采集数据和多站时钟标定结果。
- `TODO`：从嘉琪的 MATLAB 工程导出一次完整配置快照，核对采样率、SCS、PRACH 格式、BWP、TDD pattern 和帧号起点；确认“120.88 兆”究竟是中心频率、带宽、采样率还是其他参数。

## 项目化入口

- NR 基础：[[5G-NR-Positioning/01-NR基础/NR TDD]]、[[5G-NR-Positioning/01-NR基础/NR Frame Slot]]
- 项目主线：[[5G-NR-Positioning/00-项目总览/5G NR Passive Positioning Pipeline]]
