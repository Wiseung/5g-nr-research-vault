---
title: 04-PDSCH
type: directory-index
status: partial
tags:
  - project/5g-nr-positioning
  - stage/ue-extraction
  - topic/pdsch
source:
  - "[[04-PDSCH/PDSCH]]"
  - "[[04-PDSCH/UE Resource Extraction]]"
  - "[[03-PDCCH/README]]"
  - "[[5G-NR-Positioning/00-项目总览/Current Learning Path]]"
related:
  - "[[05-定位观测量/Timing Observation]]"
  - "[[08-MATLAB代码/MATLAB 5G Toolbox API Map]]"
---

# 04-PDSCH

> [!abstract] 目录定位
> 本目录回答“已接受的 DCI 如何变成可回放的 PDSCH 资源、可解释的 DL-SCH 译码状态，以及可供定位支路使用的单 UE 观测候选”。它不把下行能量峰、PDSCH TB-CRC 或单站相关峰自动升级为 UE 身份或可靠位置。

## 目录边界

```text
配置/RRC + C-RNTI
        -> PDCCH/ DCI
        -> PDSCH resource_snapshot
        -> RE/DM-RS/PTRS 分类
        -> 信道估计/均衡/LLR
        -> DL-SCH/LDPC/HARQ
        -> UE Resource Extraction
        -> Timing Observation / TDOA
```

PDSCH 是物理信道，DL-SCH 是其主要传输信道承载；PDCCH 只提供控制信息，DM-RS/PTRS 是参考资源。每个阶段都有自己的输入、输出和失败状态。

- [[PDSCH]]：由 DCI 驱动的下行资源、DM-RS、译码和 UE 掩码。
- [[UE Resource Extraction]]：把合法资源快照转换为 RE/样点掩码，并分离译码与定位支路。

## 推荐阅读顺序

| 顺序 | 笔记 | 需要回答的问题 | 主要产物 |
|---:|---|---|---|
| 0 | [[03-PDCCH/PDCCH Implementation Contract|PDCCH Implementation Contract]] | 哪个 DCI 候选可以被消费？ | `candidate_id`、`config_id`、DCI 状态 |
| 1 | [[03-PDCCH/DCI|DCI]] | 控制时刻如何指向数据时刻？ | `resource_snapshot`、`coding_snapshot` |
| 2 | [[PDSCH]] | PDSCH 的资源、参考、编码和 HARQ 如何闭合？ | RE/DM-RS/LLR/TB 状态 |
| 3 | [[UE Resource Extraction]] | 如何从混合 IQ 标出目标 UE 的资源？ | 掩码、样点窗口、质量账本 |
| 4 | [[05-定位观测量/Timing Observation|Timing Observation]] | 哪些片段能进入时间观测？ | raw/calibrated ToA |

复用的基础与长文：[[01-NR基础/PRB RE Resource Grid]]、[[01-NR基础/NR Frame Slot]]、[[01-专题知识/5G定位/NR PDCCH 盲搜与 PDSCH-PUSCH 资源解析]]、[[01-专题知识/信道估计与均衡/DM-RS]]、[[01-专题知识/信道编译码/NR编码链/NR-DL-SCH 编码链]]。

## 共享数据契约

### `resource_snapshot`

回答“在哪里”：

```js
resource_snapshot:
  snapshot_id: ""
  event_id: ""
  candidate_id: ""
  config_id: ""
  control_slot: null
  data_slot: null
  bwp_id: null
  prb_indices_local: []
  prb_indices_absolute: []
  symbol_indices: []
  re_sets:
    data: []
    dmrs: []
    ptrs: []
    reserved: []
  layer_count: null
  port_count: null
  mapping_version: ""
  state: "complete|partial|rejected"
```

### `coding_snapshot`

回答“用什么编码/重传状态”：

```js
coding_snapshot:
  event_id: ""
  transport_channel: "DL-SCH|unknown"
  mcs_index: null
  modulation_order_Qm: null
  tbs_bits: null
  codeblock_count_C: null
  base_graph: "unknown"
  lifting_size_Z: null
  total_E: null
  per_codeblock_Er: []
  rv: null
  ndi: null
  harq_process_id: null
  llr_convention: "unknown"
  state: "not_attempted|decoded|tb_crc_pass|tb_crc_fail|invalid"
```

两个快照共享 `event_id`、`config_id` 和版本引用；`null` 表示未知，不得用 0 伪装已知值。字段位宽、TBS 表、DM-RS/PTRS 序列与 API 签名要回到锁定 Release 的标准或实现记录。

## 阶段门

| 阶段门 | 通过条件 | 失败时的降级 |
|---|---|---|
| 控制门 | DCI 候选 CRC/RNTI、格式和字段合法 | `dci_invalid` |
| 坐标门 | BWP/Point A、局部/绝对 PRB、slot/symbol 闭合 | `coordinate_mismatch` |
| 掩码门 | data/DM-RS/PTRS/reserved 互斥且不越界 | `mask_overlap` / `resource_invalid` |
| 参考门 | DM-RS 序列、端口/层、估计域相容 | `reference_fail` |
| 软信息门 | LLR 符号、尺度、长度、顺序已定义 | `llr_invalid` |
| 编码门 | `A/B/C/K'/F/N/E/E_r` 与 RV/HARQ 闭合 | `coding_invalid` |
| 观测门 | 原始 I/Q、窗口、群时延、RF/时钟校准可追溯 | `partial_observation` / `toa_unreliable` |

`tb_crc_pass` 只表示数据链路通过；`tdoa_usable` 还需要定位门通过。静态链接或 YAML 检查通过，不代表动态实验已经运行。

## 失败诊断顺序

出现“PDSCH 解不出来”时，按以下顺序定位：

1. `config_id`/Release/RRC 是否与捕获时间一致？
2. DCI 控制 slot、调度偏移和数据 slot 是否分开记录？
3. BWP、Point A、PRB/VRB 和 symbol 坐标是否越界或错位？
4. data、DM-RS、PTRS 和保留资源是否交叠？
5. 参考信号序列、端口、层、预编码和 `H_eff` 域是否一致？
6. LLR 符号、噪声方差、率匹配索引和码块边界是否闭合？
7. 若译码成功但定位不稳，是否存在滤波/RF/时钟偏差、多径或多用户碰撞？

不要先调相关峰阈值或强行填默认 TBS 来掩盖上游错误。

## 当前证据状态

- `STANDARD + partial`：[[02-标准与参考/3GPP/3GPP TS 38.211｜Physical channels and modulation]]、[[02-标准与参考/3GPP/3GPP TS 38.212｜Multiplexing and channel coding]]、[[02-标准与参考/3GPP/3GPP TS 38.213｜Physical layer procedures for control]]、[[02-标准与参考/3GPP/3GPP TS 38.214｜Physical layer procedures for data]] 的职责和接口。
- `PERSONAL_NOTE`：PDSCH、UE 资源掩码、DM-RS 和单用户定位接口的组织方式。
- `EXPERIMENT + NEEDS_VERIFICATION`：目录内暂无真实网络 IQ、现场 C-RNTI/PDSCH 正例、动态 BLER/NMSE/ToA 结果。
- `NEEDS_EXTERNAL_REFERENCE`：项目 Release、精确标准表格/条款、MATLAB 5G Toolbox 函数签名、专用 RRC/DM-RS 配置。

## 目录验收清单

- [ ] 可从 `candidate_id` 回到 DCI、`resource_snapshot` 和原始 IQ。
- [ ] 控制时刻与数据时刻、BWP 局部与载波绝对坐标均可回放。
- [ ] RE 掩码覆盖、互斥、顺序和越界都有统计。
- [ ] DM-RS/PTRS、层/端口/天线和等效信道域显式记录。
- [ ] DL-SCH 长度账本、LLR 约定、RV/HARQ 软合并状态可回读。
- [ ] 译码支路和定位支路共享事件键但不共享成功标志。
- [ ] 未运行的实验和未核验的 API/表格保持 `NEEDS_VERIFICATION`/`NEEDS_EXTERNAL_REFERENCE`。

## 关联入口

- [[03-PDCCH/README|03-PDCCH]]：控制候选和 DCI 资源快照。
- [[05-定位观测量/README|05-定位观测量]]：ToA/RToA/TDoA 接口。
- [[08-MATLAB代码/MATLAB 5G Toolbox API Map|MATLAB API Map]]：工具箱线索和核验队列。
- [[5G-NR-Positioning/00-项目总览/Current Learning Path|Current Learning Path]]：项目学习顺序。
