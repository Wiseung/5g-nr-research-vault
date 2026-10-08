---
title: 5G-NR-Positioning
aliases:
  - 5G NR 被动定位项目知识库
type: project-index
status: seed
created: 2026-09-04
tags:
  - project/5g-nr-positioning
source:
  - 用户项目需求
related:
  - "[[00-项目总览/5G NR Passive Positioning Pipeline]]"
  - "[[00-项目总览/Current Learning Path]]"
  - "[[00-项目总览/项目知识地图]]"
---

# 5G-NR-Positioning

这是 5G NR 被动定位项目的项目化入口。已有 `NR_decode_test.m` 先覆盖公共下行同步与 SIB1 入口；项目定位主线则是 `PRACH -> Random Access -> C-RNTI -> UE-specific PDCCH -> DCI -> PUSCH/资源提取 -> Timing Observation -> TDOA`。两者相关但不可混为同一解码能力。

- 先看：[[00-项目总览/5G NR Passive Positioning Pipeline]]
- 再按优先级：[[00-项目总览/Current Learning Path]]
- 初始下行知识：[[01-NR基础/SSB PBCH MIB]]（PSS/SSS -> SSB/PBCH/MIB -> CORESET-0/SS0 -> SI-RNTI/SIB1）
- 代码导读：[[08-MATLAB代码/NR_decode_test 代码学习与协议映射]]
- 总结与缺口：[[00-项目总览/项目知识地图]]
- 规范入口：[[10-3GPP规范/3GPP Specification Map]]

## 目录入口

- [[00-项目总览/README]]
- [[01-NR基础/README]]
- [[02-PRACH/README]]
- [[03-PDCCH/README]]
- [[04-PDSCH/README]]
- [[05-定位观测量/README]]
- [[06-TDOA定位/README]]
- [[07-多站协同/README]]
- [[08-MATLAB代码/README]]
- [[09-采数实验/README]]
- [[10-3GPP规范/README]]

## 证据规则

新笔记只在有来源时使用 `STANDARD`、`PERSONAL_NOTE` 或 `EXPERIMENT`；未核对的条款/API 使用 `NEEDS_EXTERNAL_REFERENCE`，未完成的现场步骤使用 `NEEDS_VERIFICATION`/`TODO`。不覆盖原始采集和既有 Vault 笔记。
