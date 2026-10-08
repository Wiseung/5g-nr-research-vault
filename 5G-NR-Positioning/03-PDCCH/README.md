---
title: 03-PDCCH
type: directory-index
status: seed
---

# 03-PDCCH

本目录回答一个核心问题：在没有 gNB 调度内部状态时，如何从合法的 PDCCH 候选恢复可信 DCI，并把它转换为可回放的 PDSCH/PUSCH 资源和定位事件上下文。

> [!important] 证据边界
> 这里的“通过”分成 `CRC pass`、`valid_dci` 和 `associated` 三层。前者只表示某个 RNTI 假设下 CRC 通过，后两者还需要字段、资源、时序和跨事件证据。当前目录没有现场运行结果；实验条目继续保留 `EXPERIMENT + NEEDS_VERIFICATION`。

## 阅读顺序

|  顺序 | 笔记                                       | 要回答的问题                          | 主要输出              |                                 |
| --: | ---------------------------------------- | ------------------------------- | ----------------- | ------------------------------- |
|   0 | [[03-PDCCH/PDCCH Implementation Contract | PDCCH Implementation Contract]] | 所有阶段共享哪些字段和状态？    | 配置/候选/快照契约                      |
|   1 | [[03-PDCCH/PDCCH Overview                | PDCCH Overview]]                | PDCCH 在项目链路中负责什么？ | 控制到数据的总览                        |
|   2 | [[03-PDCCH/CORESET                       | CORESET]]                       | 哪片时频资源允许承载控制？     | CORESET 资源集合                    |
|   3 | [[03-PDCCH/Search Space                  | Search Space]]                  | 何时监测、尝试哪些候选？      | monitoring occasions/candidates |
|   4 | [[03-PDCCH/CCE REG                       | CCE REG]]                       | 候选如何从 CCE 落到 RE？  | 显式索引和掩码                         |
|   5 | [[03-PDCCH/PDCCH Blind Decoding          | PDCCH Blind Decoding]]          | 如何逐候选完成检测与消歧？     | candidate records/状态            |
|   6 | [[03-PDCCH/DCI                           | DCI]]                           | 控制比特如何变成调度快照？     | resource/coding snapshot        |
|   7 | [[03-PDCCH/RNTI                          | RNTI]]                          | 候选属于哪个控制上下文？      | RNTI 生命周期和关联证据                  |

## 依赖关系

```text
[[02-PRACH/C-RNTI|C-RNTI]]
        ↓
[[03-PDCCH/CORESET|CORESET]] + [[03-PDCCH/Search Space|Search Space]]
        ↓
[[03-PDCCH/CCE REG|CCE REG]]
        ↓
[[03-PDCCH/PDCCH Blind Decoding|PDCCH Blind Decoding]]
        ↓
[[03-PDCCH/DCI|DCI]] + [[03-PDCCH/RNTI|RNTI]]
        ↓
[[04-PDSCH/PDSCH|PDSCH]] / PUSCH / [[05-定位观测量/Timing Observation|Timing Observation]]
```

## 阶段门

1. **配置门**：`config_id`、BWP、TDD、CORESET 和 Search Space 坐标完整。
2. **候选门**：每个 monitoring occasion 可生成有序候选，越界和未监测状态可区分。
3. **物理门**：CCE/REG/RE 正逆映射、DM-RS 掩码和 LLR 长度闭合。
4. **控制门**：正确/错误 RNTI、DCI 格式和字段合法性可分别统计。
5. **资源门**：有效 DCI 可生成带控制/数据 slot 区分的 `resource_snapshot`。
6. **定位门**：只有上行参考/资源和跨站时间基准满足条件，才进入 ToA/TDoA。

## 统一字段

所有原子笔记都应优先使用以下键：`config_id`、`event_id`、`candidate_id`、`monitoring_occasion`、`coreset_id`、`search_space_id`、`aggregation_level`、`candidate_index`、`rnti_hypothesis`、`dci_format`、`crc_state`、`field_valid`、`resource_snapshot`、`coding_snapshot`、`failure_reason`。

## 规范与工具入口

| 入口 | 负责边界 | 当前状态 |
|---|---|---|
| [[02-标准与参考/3GPP/3GPP TS 38.211｜Physical channels and modulation|TS 38.211]] | PDCCH/DM-RS/CCE-REG-RE 物理映射 | `STANDARD + partial` |
| [[02-标准与参考/3GPP/3GPP TS 38.212｜Multiplexing and channel coding|TS 38.212]] | DCI CRC、Polar、率匹配 | `STANDARD + partial` |
| [[02-标准与参考/3GPP/3GPP TS 38.213｜Physical layer procedures for control|TS 38.213]] | 监测时机、搜索空间、控制过程 | `STANDARD + partial` |
| [[02-标准与参考/3GPP/3GPP TS 38.214｜Physical layer procedures for data|TS 38.214]] | DCI 到 PDSCH/PUSCH 调度解释 | `STANDARD + partial` |
| [[5G-NR-Positioning/08-MATLAB代码/MATLAB 5G Toolbox API Map|MATLAB API Map]] | 工具箱函数和维度核验 | `NEEDS_EXTERNAL_REFERENCE` |

精确 Release、条款、表格、API 签名和实际实验结果必须回写到对应原子笔记，不能用本目录的抽象描述替代。

- [[PDCCH Overview]]
- [[CORESET]]
- [[Search Space]]
- [[CCE REG]]
- [[PDCCH Blind Decoding]]
- [[DCI]]
- [[RNTI]]
- [[PDCCH Implementation Contract]]
