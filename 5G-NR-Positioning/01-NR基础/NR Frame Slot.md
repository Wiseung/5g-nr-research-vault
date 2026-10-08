---
title: NR Frame Slot
aliases:
  - NR 帧与时隙
  - NR Frame/Slot
type: atomic
status: seed
created: 2026-09-04
tags:
  - domain/5g-nr
  - topic/frame-slot
  - topic/timing
  - stage/基础
  - evidence/3gpp
source:
  - 3GPP TS 38.211
  - 01-专题知识/信道估计与均衡/01 5G 物理层与信道模型
related:
  - "[[5G-NR-Positioning/01-NR基础/Numerology|Numerology]]"
  - "[[5G-NR-Positioning/01-NR基础/SCS|SCS]]"
  - "[[5G-NR-Positioning/01-NR基础/PRB RE Resource Grid|PRB RE Resource Grid]]"
  - "[[5G-NR-Positioning/01-NR基础/NR TDD|NR TDD]]"
  - "[[5G-NR-Positioning/02-PRACH/PRACH Occasion|PRACH Occasion]]"
  - "[[5G-NR-Positioning/03-PDCCH/PDCCH Overview|PDCCH Overview]]"
---

# NR Frame Slot

## 1. 一句话定义

NR Frame/Slot 是把连续采样时间组织成 radio frame、subframe、slot 和 OFDM symbol 的时域坐标体系；`numerology` 决定 slot 的时间粒度。

## 2. 为什么项目需要它

被动接收机必须把 IQ 样点放回正确的帧、时隙和符号，才能判断 PRACH occasion、RAR 窗口、PDCCH 监测时机以及后续 PDSCH/PUSCH 资源。没有稳定的时域坐标，跨站事件也无法形成同一个 `event_id`。

## 3. 它位于整个 5G 空口链路的什么位置

它是同步之后、资源解析之前的基础坐标层：

```text
Raw IQ → [[5G-NR-Positioning/01-NR基础/NR Frame Slot|Frame/Slot 坐标]]
       → [[5G-NR-Positioning/01-NR基础/NR TDD|D/U/F 标注]]
       → PRACH → C-RNTI → PDCCH → PDSCH → ToA/TDOA
```

## 4. 输入

- 小区/帧同步结果或等价的时间参考。
- `numerology`、SCS、采样率、FFT 点数和 CP 配置。
- 捕获起点、帧号起点及是否跨帧连续采集的定义。
- 当前载波/BWP 的时域配置。

## 4.1 同步入口：SSB/PBCH 与帧锚点

在没有可靠外部时钟时，NR 基础坐标通常要先经过下行同步候选，再建立 frame/slot 轴。一个可审计的最小链路是：

~~~text
PSS/SSS 候选
    ↓
小区标识与粗定时/频偏候选
    ↓
PBCH 解调与 MIB 候选
    ↓
公共 SCS/载波/帧边界上下文
    ↓
Frame/slot/symbol 坐标
~~~

这里的“候选”很重要：相关峰通过不等于 MIB 已正确解码，MIB 已解码也不等于已经获得完整的 BWP、TDD 或 PRACH 配置。应分别记录候选峰、译码状态、假设的频率参考和帧起点置信度。PSS/SSS、PBCH/MIB 的序列、映射和字段归属需按项目 Release 的 TS 38.211/38.213/38.331 外部核验，当前仅作为流程入口。

SSB/PBCH 是下行发射源的同步锚点。在本项目中它可以帮助统一小区、帧和频率坐标，但不能把固定站接收的 SSB 到达时间直接当作 UE 上行 ToA；UE 定位仍需要合法的上行观测和跨站校准。

PSS/SSS、SSB、PBCH/BCH、MIB 以及 MIB 到 CORESET-0 的完整概念链见 [[01-NR基础/SSB PBCH MIB]]；本页继续负责 frame/slot/symbol 的时间坐标。

## 5. 输出

- `frame_index`、`subframe_index`、`slot_index`、`symbol_index`。
- 每个坐标对应的样点区间和符号中心时刻。
- 可供 [[5G-NR-Positioning/01-NR基础/NR TDD|NR TDD]]、[[5G-NR-Positioning/02-PRACH/PRACH Occasion|PRACH Occasion]] 和 [[5G-NR-Positioning/03-PDCCH/PDCCH Overview|PDCCH Overview]] 使用的时间键。
- 跨站可比的采集时间戳及其不确定度。

## 6. 关键参数

| 参数 | 含义 | 项目记录要求 |
|---|---|---|
| `mu` | numerology 索引 | 与 SCS、Release 一起保存 |
| `Delta_f` | 子载波间隔 | 不要由采样率反推后静默覆盖 |
| `N_FFT` | FFT 点数 | 与采样率和有效子载波数成套记录 |
| `N_CP` | CP 样点数/时间 | 区分普通 CP 与扩展 CP |
| `N_sym_slot` | 每时隙 OFDM 符号数 | 按 CP 和版本核对，不能永远写死 14 |
| `frame_start_sample` | 捕获中的帧起点 | 保留同步置信度和漂移信息 |

## 7. 时域位置

常见 NR 组织是 10 ms radio frame、每帧 10 个 1 ms subframe；在普通 CP 下，slot 数随 `mu` 增大而增加，常用关系为：

$$
N_{slot}^{frame}=10\,\cdot2^\mu,\qquad
T_{slot}\approx\frac{1\ \mathrm{ms}}{2^\mu}.
$$

这里是数量级和常见配置关系；扩展 CP、特殊时隙及具体 Release 应以锁定的规范和网络配置为准，并在日志中保留实际符号边界。

## 7.1 时间层级与编号

NR 的时间坐标建议按“宏观周期 → 调度粒度 → 资源符号”保存，而不要只保存一个样点偏移：

| 层级 | 常用时长/数量关系 | 解析意义 |
| --- | --- | --- |
| Radio frame | 10 ms | 跨站和长期日志的粗粒度锚点 |
| Subframe | 1 ms；每帧 10 个 | 与 TDD pattern 和部分配置字段对齐 |
| Slot | 普通 CP 下约 $1\text{ ms}/2^\mu$ | PDCCH、PDSCH/PUSCH 调度的主要时间键 |
| OFDM symbol | $T_u+T_{CP,l}$ | 资源网格最小时间坐标 |

在一个局部、单 numerology 的日志中，可以定义连续 slot 序号：

$$
n_{\mathrm{slot,local}}
=10\cdot2^\mu\,n_{\mathrm{frame}}
 +2^\mu\,n_{\mathrm{subframe}}
 +n_{\mathrm{slot}}.
$$

这个序号只是工程索引，不等同于网络的 SFN；若捕获跨越 SFN 回绕、丢样或配置切换，应另存单调的 <code>capture_sample_index</code> 和帧同步置信度。

## 8. 频域位置

Frame/slot 本身不指定占用哪些子载波。给定时域坐标后，频域坐标还要由载波、BWP、PRB 和 RE 网格确定，见 [[5G-NR-Positioning/01-NR基础/PRB RE Resource Grid|PRB RE Resource Grid]]。同一 slot 可同时存在控制、数据、参考信号和保护 RE。

## 9. 数学原理

对第 `m` 个 OFDM symbol，中心时刻可按实际 CP 长度累计：

$$
t_m=t_0+\sum_{i=0}^{m-1}(T_u+T_{CP,i})
 +\frac{T_u+T_{CP,m}}{2},
\qquad T_u=\frac{1}{\Delta f}.
$$

样点到符号坐标的映射应先减去捕获起点和同步偏移，再按每个 symbol 的 `N_FFT+N_CP`（或实际 CP 表）切分；不要用均匀 14 等分替代有不同 CP 的边界。

## 9.1 绝对样点映射

将 symbol 映射到 IQ 时采用左闭右开区间。设一个 slot 的起点为 $q_0$，第 $l$ 个 symbol 的 FFT 长度为 $N_{FFT}$、CP 长度为 $N_{CP,l}$，则：

$$
q_l=q_0+\sum_{i=0}^{l-1}(N_{FFT}+N_{CP,i}),\qquad
\mathcal I_l=[q_l,\ q_l+N_{CP,l}+N_{FFT}).
$$

去 CP 后的 FFT 窗口是 $[q_l+N_{CP,l},\,q_l+N_{CP,l}+N_{FFT})$；符号中心样点可用该窗口中心表示，而不是整个含 CP 区间的中心。若采样率转换比例不是整数，先在浮点时间轴累计，再在最终边界处按统一规则取整，避免每个 symbol 独立四舍五入造成漂移。

说明性例子：$\mu=1$、$N_{FFT}=2048$、$F_s=61.44$ MHz 时，$F_s=N_{FFT}\Delta f$，一个去 CP symbol 是 2048 样点；普通 CP 下 14 个 symbol 的有用部分为 28672 样点，slot 总时长约 500 μs，剩余样点来自 CP。实际 CP 表和 slot 总长度仍需从配置/工具箱读取。

## 10. 3GPP 对应规范

- **TS 38.211**：§4.2（numerology 接口）、§4.3.1–§4.3.3（frame/subframe、slot、OFDM symbol）；条款标题和编号需按项目锁定的 Release 再核对。
- **TS 38.213**：与 slot format、控制监测时机相关的过程，尤其 §11.1 的 D/U/F slot format 入口。
- 相关字段/参数：`mu`、SCS、CP、slot/symbol 编号、slot format、帧边界。
- 证据状态：`STANDARD + partial`；本 Vault 尚未锁定项目 Release 和网络配置，精确表格值标为 `NEEDS_EXTERNAL_REFERENCE`。

## 11. MATLAB / MATLAB 5G Toolbox 对应函数

- `nrCarrierConfig`：承载 SCS、载波带宽和网格相关配置；用对象属性保存 `SubcarrierSpacing`、`NSizeGrid` 等。
- `nrOFDMInfo`：根据 carrier 配置查询 FFT、采样率、CP 和符号长度等波形信息。
- `nrOFDMModulate` / `nrOFDMDemodulate`：在资源网格和时域波形之间转换，适合验证样点边界。
- 当前没有在本 Vault 验证“从任意 IQ 自动恢复 frame/slot”的单一 API；函数签名、Release 行为和同步输入需在本机 MATLAB/5G Toolbox 核对，状态为 `NEEDS_EXTERNAL_REFERENCE`。

## 12. 本项目中的用途

1. 以同步结果建立统一 frame/slot/symbol 时间轴。
2. 用 [[5G-NR-Positioning/01-NR基础/NR TDD|NR TDD]] 将每个 symbol 标为 DL、UL、F 或 unknown。
3. 在合法时隙中搜索 [[5G-NR-Positioning/02-PRACH/PRACH Occasion|PRACH Occasion]]，把前导事件送入 Random Access 状态机。
4. 用同一时间键关联 RAR、Msg3、C-RNTI、PDCCH/DCI 和 [[5G-NR-Positioning/04-PDSCH/PDSCH|PDSCH]]/PUSCH，最后为 ToA/TDOA 保留跨站时间戳。

## 12.1 定位事件时间键

为让多站观测能够判断“是否是同一个 UE 事件”，建议每个候选至少保存：

| 字段 | 含义 |
| --- | --- |
| <code>capture_id</code> / <code>station_id</code> | 捕获文件和站点身份 |
| <code>config_id</code> | numerology、CP、FFT、采样率和 TDD 版本 |
| <code>frame_index</code>、<code>slot_index</code>、<code>symbol_index</code> | 空口离散坐标 |
| <code>sample_start</code>、<code>sample_peak</code> | 原始样点位置，采用同一边界约定 |
| <code>time_raw_seconds</code> | 由采样率换算的未校准时间 |
| <code>time_calibrated_seconds</code> | 扣除时钟、RF、数字滤波等校准项后的时间 |
| <code>direction</code> | D/U/F/unknown 及判定来源 |
| <code>quality</code> | 同步置信度、峰值/旁瓣、丢样和不确定度 |

<code>frame/slot/symbol</code> 只解决“在空口结构中的哪里”，不等于传播时间。跨站匹配时优先用公共时间基准和事件内容，再用离散坐标做一致性检查；不能因为两个文件的 <code>slot_index</code> 相同就假定它们的样点已同步。

## 13. 常见误区

- 把 1 ms subframe、slot 和 OFDM symbol 当成同一个单位。
- 只按 `sample_rate` 切块，忽略 SCS、FFT、CP 和同步偏移。
- 假设所有 slot 都是 14 个普通 CP symbol，未检查扩展 CP 或特殊配置。
- 把帧号重置、捕获文件起点或设备时间戳当作空口帧边界。
- 用下行同步时间直接当作多站 UE 发射时间，跳过硬件延迟和时钟偏差。

## 14. 与相似概念的区别

| 概念 | 主要回答的问题 |
|---|---|
| Frame/Subframe | 较粗的周期和系统时间组织 |
| Slot | 调度和 TDD 方向通常使用的时间粒度 |
| OFDM symbol | 资源网格的最小时域坐标 |
| Numerology | 决定 SCS、slot 粒度和波形时间尺度的参数 |
| Sample timestamp | 设备采集时钟上的样点时间，必须通过同步映射到空口坐标 |

## 15. 代码实现注意事项

- 所有转换函数显式传入 `mu`、SCS、FFT、CP 表和 `capture_start_sample`，不要依赖隐式全局状态。
- 同时保存整数样点边界与浮点 symbol 中心时刻，供 PRACH 相关峰和 TDOA 校准使用。
- 对跨文件/跨站捕获，记录 frame rollover、丢样、重采样和时钟漂移。
- 用断言检查 `symbol_index`、`slot_index` 范围以及样点区间不重叠；异常时返回 `unknown`，不要静默修正。

## 15.1 边界断言与回放测试

建议把以下断言作为每个捕获片段的入口检查：

- 相邻 symbol 区间严格首尾相接或显式保留 guard，不允许隐式重叠；
- <code>sample_end - sample_start</code> 与 FFT/CP 表一致；
- slot、subframe、frame 边界在跨文件拼接后仍单调；
- 丢样、重采样和帧同步重锁会生成新的质量状态或 <code>config_id</code>；
- 同一 <code>event_id</code> 的各站记录都能回到原始 I/Q 和相同的资源/方向快照。

回放测试至少覆盖 slot 起点、跨 subframe、跨 frame、TDD 切换附近和捕获截断处。测试通过只说明坐标转换自洽，不说明同步误差或定位精度已经合格。

## 16. 待实验验证的问题

- 从当前设备 IQ 能否稳定恢复帧起点、帧号和 `mu`？
- 在不同 SCS、CP、采样率和 CFO 下，symbol 边界误差是多少样点？
- TDD 切换附近的 flexible/guard 区间如何标记，是否需要保留不确定窗口？
- 多站文件的 frame/slot 坐标能否通过公共时钟或事件键对齐？

## 17. Related Notes

- [[5G-NR-Positioning/01-NR基础/Numerology|Numerology]]
- [[5G-NR-Positioning/01-NR基础/SCS|SCS]]
- [[5G-NR-Positioning/01-NR基础/PRB RE Resource Grid|PRB RE Resource Grid]]
- [[5G-NR-Positioning/01-NR基础/NR TDD|NR TDD]]
- [[01-专题知识/信道估计与均衡/01 5G 物理层与信道模型|01 5G 物理层与信道模型]]
- [[01-专题知识/信道估计与均衡/06 OFDM 接收与频域均衡|06 OFDM 接收与频域均衡]]
- [[01-专题知识/5G定位/5G TDD 上下行监测与资源解析|5G TDD 上下行监测与资源解析]]
- [[5G-NR-Positioning/02-PRACH/PRACH Occasion|PRACH Occasion]]
- [[5G-NR-Positioning/03-PDCCH/PDCCH Overview|PDCCH Overview]]

## 证据与状态

- `STANDARD + partial`：TS 38.211 的 frame、slot、symbol 和 numerology 入口；Release/表格尚未锁定。
- `PERSONAL_NOTE`：沿用 [[01-专题知识/信道估计与均衡/01 5G 物理层与信道模型|01 5G 物理层与信道模型]] 的时间尺度与索引记号。
- `NEEDS_VERIFICATION`：当前项目的帧号起点、CP 类型、同步算法和设备时间戳语义。
