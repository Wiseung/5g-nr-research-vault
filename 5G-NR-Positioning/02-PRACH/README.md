---
title: 02-PRACH
type: directory-index
status: partial
---

# 02-PRACH

本目录把 PRACH 当作“可观测的随机接入事件入口”，而不是把一个相关峰直接当成 UE 身份。主链是：

```text
配置快照 -> PRACH Occasion -> 前导/序列 -> 检测与 ToA
       -> RA-RNTI -> RAR -> Msg3/Msg4 -> C-RNTI 候选
```

`PRACH` 是 Msg1 的物理承载；`Random Access Procedure` 是跨 PHY/MAC/RRC 的过程。目录中的所有结论都要保留这条边界。

## 阅读入口与依赖

| 顺序 | 笔记 | 作用 | 主要输出 |
|---:|---|---|---|
| 1 | [[PRACH Overview]] | 建立信号、协议和定位边界 | 事件键与证据层级 |
| 2 | [[PRACH Configuration]] | 解析 RACH-ConfigCommon/Generic | `config_snapshot` |
| 3 | [[PRACH Occasion]] | 把配置展开为合法时频 RO | `ro_snapshot` |
| 4 | [[Zadoff Chu Sequence]] | 生成根序列和本地模板 | `root_sequence` |
| 5 | [[Cyclic Shift]] | 枚举移位与前导索引 | `preamble_map` |
| 6 | [[PRACH Preamble]] | 解释一个 Msg1 前导实例 | `preamble_event` |
| 7 | [[PRACH Detection]] | 相关、门限和峰筛选 | `peak_list` |
| 8 | [[Timing Estimation]] | 产生带质量的相对时延 | `toa_observation` |
| 9 | [[RA-RNTI]] | 生成 RAR 监测上下文 | `ra_rnti_candidate` |
| 10 | [[RAR]] | 解析 Msg2/fallback RAR | `rar_event` |
| 11 | [[Msg3]] | 从 UL grant 找到 Msg3 PUSCH | `msg3_event` |
| 12 | [[Random Access Procedure]] | 推进 2-step/4-step 状态机 | `ra_state_event` |
| 13 | [[C-RNTI]] | 形成后续 PDCCH 候选 | `crnti_candidate` |

前置坐标来自 [[../01-NR基础/NR Frame Slot|NR Frame Slot]]、[[../01-NR基础/Numerology|Numerology]]、[[../01-NR基础/SCS|SCS]]、[[../01-NR基础/PRB RE Resource Grid|PRB/RE Resource Grid]] 和 [[../01-NR基础/NR TDD|NR TDD]]。

## 项目事件契约

下面是项目侧的最小事件结构，不是 3GPP ASN.1 定义。缺失字段用 `null` 或 `unknown`，不得用“常见参数”补齐。

```js
event_id: "cell=<cell_id>|frame=<frame>|slot=<slot>|ro=<ro_id>|preamble=<index>"
capture_id: "<capture-id>"
config_id: "<immutable-config-id>"
cell_id: null
frame: null
slot: null
ro:
  time_index: null
  frequency_index: null
  first_symbol: null
  duration_samples: null
  ssb_index: null
preamble:
  index: null
  logical_root_index: null
  sequence_number: null
  cyclic_shift: null
detection:
  statistic: null
  threshold: null
  peaks: []
  state: "energy_seen|preamble_detected|ambiguous|rejected"
timing:
  reference: "capture_start|ro_start|sync_reference|unknown"
  sample_offset: null
  seconds: null
  quality: "valid|unreliable|unknown"
association:
  ra_rnti: null
  rar_rapid: null
  temporary_c_rnti: null
  c_rnti: null
  state: "candidate|matched|confirmed|expired|ambiguous"
evidence:
  standard: []
  personal_note: []
  experiment: []
  gaps: []
```

### 不变量

- `config_id`、`capture_id`、Release 和采样率必须同时记录；配置切换时不能复用旧 RO。
- `ro_id`、`preamble_index`、`ra_rnti`、`temporary_c_rnti` 和 `c_rnti` 是不同字段，不能互相覆盖。
- 相关峰只能将事件推进到 `preamble_detected`；升级到 `c_rnti=confirmed` 必须有 RAR、争用解决或后续控制链证据。
- ToA 先保留参考点和校准状态，再交给 [[../05-定位观测量/Timing Observation|Timing Observation]] 或 TDOA。

## 层间边界

| 层 | 本目录记录什么 | 不应越界声称 |
|---|---|---|
| PHY/38.211 | 序列、波形、时频资源、端口和采样坐标 | 不直接产生 C-RNTI |
| PHY procedure/38.213 | RO 有效性、响应窗口、RAR/PDCCH 时序 | 不定义完整 MAC PDU 语义 |
| MAC/38.321 | Msg1/Msg2/Msg3/Msg4、RAPID、TA、Temporary C-RNTI、争用解决 | 不替代 IQ 相关器 |
| RRC/38.331 | RACH-ConfigCommon/Generic、SSB/RO 映射和 BWP 配置 | 不等于现场已解出的配置 |
| Measurement/38.215 | TADV/首径等标准测量定义 | 不把项目自定义 ToA 自动升级为标准测量 |
| Project | 事件键、候选状态、校准和实验记录 | 不把假设写成规范事实 |

## 证据等级

- `STANDARD`：已在指定规范版本中找到的定义；记录版本、条款和 URL。
- `PERSONAL_NOTE`：Vault 中的解释或推导；保留原符号和适用范围。
- `EXPERIMENT`：有配置、指标和原始结果的本项目运行；只有脚本模板仍标 `NEEDS_VERIFICATION`。
- `NEEDS_EXTERNAL_REFERENCE`：缺少指定 Release 的表格、API 签名或条款核验。
- `NEEDS_VERIFICATION`：现场配置、设备可见性、阈值或校准尚未证实。

## Release 17 核验基线

这些链接只作为本轮技术补充的规范基线，不代表当前采集网络必然使用同一版本。

| 规范 | 本轮版本 | 重点范围 |
|---|---|---|
| [TS 38.211 V17.8.0](https://etsi.org/deliver/etsi_ts/138200_138299/138211/17.08.00_60/ts_138211v170800p.pdf) | Release 17 | §5.3.2、§6.3.3.1、§6.3.3.2：PRACH 序列、波形和资源 |
| [TS 38.213 V17.8.0](https://etsi.org/deliver/etsi_ts/138200_138299/138213/17.08.00_60/ts_138213v170800p.pdf) | Release 17 | §8、§8.1、§8.2、§8.2A：随机接入物理过程和窗口 |
| [TS 38.321 V17.8.0](https://etsi.org/deliver/etsi_ts/138300_138399/138321/17.08.00_60/ts_138321v170800p.pdf) | Release 17 | §5.1、§6.1.5、§6.2.2/§6.2.3：MAC 状态、RAR 和争用解决 |
| [TS 38.331 V17.0.0](https://etsi.org/deliver/etsi_ts/138300_138399/138331/17.00.00_60/ts_138331v170000p.pdf) | Release 17 | RACH-ConfigCommon/Generic 和 RRC 字段 |
| [TS 38.215 V17.5.0](https://etsi.org/deliver/etsi_ts/138200_138299/138215/17.05.00_60/ts_138215v170500p.pdf) | Release 17 | §5.2.7：PRACH TADV 与首径/参考点边界 |

版本、条款和字段若与设备解码结果冲突，保留冲突并标 `NEEDS_VERIFICATION`，不要静默选择一方。

## 目录验收清单

- [ ] 能从 RRC/SIB/设备元数据生成带 Release 的 `config_snapshot`。
- [ ] 能将 `prach-ConfigurationIndex` 展开为时间、频率和 TDD 有效性，而不是只保存索引。
- [ ] 本地模板与根序列、循环移位、`L_RA` 和 PRACH SCS 一致。
- [ ] 检测结果保留全峰轨迹、门限、CFO/多径诊断和失败原因。
- [ ] ToA 明确参考点、校准、峰策略和不确定度。
- [ ] RA-RNTI 只由 RO 上下文生成；RAR 必须检查 RAPID；Temporary C-RNTI 不直接等于最终 C-RNTI。
- [ ] 2-step、4-step、CBRA、CFRA 分支有显式状态，未观测到的消息不写成成功。
- [ ] 所有标准/API/实验声明都有证据等级和待核验项。

## 当前缺口

1. 当前网络的 Release、2-step/4-step、CBRA/CFRA 和 SUL 状态尚未从设备快照锁定。
2. 尚无真实 IQ 正例证明 RAR、Msg3、Msg4 均在同一捕获窗口可见。
3. MATLAB 5G Toolbox 的本机版本、函数签名和 `nrPRACHDetect` 多峰行为仍需运行验证。
4. 多站 PRACH ToA 还缺 RF/滤波群时延、时钟偏置和采样率漂移的实测校准。

## 关联入口

- 项目主线：[[../00-项目总览/5G NR Passive Positioning Pipeline|5G NR Passive Positioning Pipeline]]、[[../00-项目总览/项目知识地图|项目知识地图]]。
- 实验主线：[[../../03-仿真与实验/5G定位/仿真：PRACH 检测与 RA 事件关联|PRACH 检测与 RA 事件关联]]、[[../../03-仿真与实验/5G定位/仿真：NR 被动监测从 PRACH 到 UL-TDOA 全流程|PRACH 到 UL-TDOA 全流程]]。
- 旧长文：[[../../01-专题知识/5G定位/NR PRACH 检测与 RA-RNTI-C-RNTI 关联|现有 PRACH-RA 主线]]。
