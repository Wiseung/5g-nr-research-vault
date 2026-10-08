---
title: RNTI
aliases:
  - Radio Network Temporary Identifier
  - 无线网络临时标识
type: atomic
status: seed
created: 2026-09-04
tags:
  - domain/5g-nr
  - channel/pdcch
  - topic/rnti
  - topic/用户关联
  - evidence/3gpp
source:
  - 3GPP TS 38.212
  - 3GPP TS 38.213
  - 3GPP TS 38.321
  - 用户项目流程说明
related:
  - "[[02-PRACH/RA-RNTI|RA-RNTI]]"
  - "[[02-PRACH/RAR|RAR]]"
  - "[[02-PRACH/Msg3|Msg3]]"
  - "[[02-PRACH/C-RNTI|C-RNTI]]"
  - "[[03-PDCCH/DCI|DCI]]"
  - "[[03-PDCCH/PDCCH Blind Decoding|PDCCH Blind Decoding]]"
---

# RNTI

> [!warning] 关键纠偏
> RNTI 是控制信道 CRC 掩码和协议上下文的标识，不是从 PRACH 波形中直接读出的用户 ID。PRACH 前导、RA Occasion、RA-RNTI、RAR 中的临时 C-RNTI、Msg3/Msg4 争用解决和连接期间 C-RNTI 必须分层记录，不能把任意一个中间值直接改名为 C-RNTI。

## 1. 一句话定义

RNTI（Radio Network Temporary Identifier）是一组用于区分 NR 控制/数据过程的标识值，常通过 PDCCH/DCI 的 CRC 掩码把候选控制信息绑定到某个过程或 UE 上下文。

## 2. 为什么项目需要它

项目需要用 RNTI 把“检测到的波形”升级为“属于哪个随机接入事件或目标 UE 的控制候选”。RA-RNTI 可把 PRACH occasion 路由到 RAR 监测窗口；临时 C-RNTI 可绑定 Msg3/Msg4；确认后的 C-RNTI 才适合驱动后续 PDCCH/PDSCH 盲搜。错误地把 RA-RNTI 当作 C-RNTI 会产生错误用户关联和错误 TDOA 事件键。

## 3. 它位于整个 5G 空口链路的什么位置

~~~text
PRACH preamble + RA Occasion
  -> RA-RNTI 候选
  -> RA-RNTI 寻址的 RAR PDCCH/PDSCH
  -> RAR 中的 TEMPORARY-C-RNTI
  -> Msg3 / Msg4 contention resolution
  -> C-RNTI 上下文确认
  -> C-RNTI 驱动 PDCCH -> DCI -> PDSCH/PUSCH
~~~

RNTI 是协议关联和 CRC 判决层，既不是 PRACH 序列，也不是 PDCCH 的物理资源坐标。

## 4. 输入

| 输入 | 作用 |
|---|---|
| PRACH occasion 的时域、频域和上行载波索引 | 生成 RA-RNTI 候选 |
| RAR/Msg3/Msg4 观测及 MAC 字段 | 建立临时标识和争用解决证据 |
| PDCCH 候选软比特和 DCI 格式 | 执行 RNTI CRC 掩码检查 |
| RRC/MAC 状态与小区/BWP 配置 | 判断 RNTI 适用上下文和有效窗口 |
| 历史关联记录 | 形成有限 C-RNTI 候选池并跟踪老化 |

任何 RNTI 值都要连同 source_event、类型、时间窗和置信度保存；只保存一个整数无法复现关联过程。

## 5. 输出

建议输出分层的 RNTI 记录：

~~~yaml
rnti_type: "RA-RNTI|TEMPORARY-C-RNTI|C-RNTI|SI-RNTI|P-RNTI|other|unknown"
rnti_value: null
source_event: ""
valid_from: ""
valid_until: ""
crc_mask_context: ""
association_state: "candidate|temporary|confirmed|expired|ambiguous|rejected"
evidence:
  prach_occasion: false
  rar_rapid_match: false
  rar_decoded: false
  msg3_observed: false
  msg4_contention_resolved: false
  followup_dci_consistent: false
~~~

confirmed 只表示在当前项目证据链中可作为控制候选键，不代表已经解出上层业务或获得永久用户身份。

## 6. 关键参数

| RNTI 上下文 | 典型作用 | 本项目记录 |
|---|---|---|
| RA-RNTI | 将 PRACH occasion 关联到 RAR 监测窗口 | occasion、生成公式版本、有效窗口 |
| TEMPORARY-C-RNTI | RAR 后临时接入/争用解决 | RAR 字段、Msg3/Msg4 事件键 |
| C-RNTI | 连接期间 UE 专用 PDCCH/PDSCH/PUSCH 上下文 | 确认依据、起止时间、后续 DCI 连续性 |
| SI-RNTI | 系统信息等公共控制 | 独立公共候选，不混入 UE 统计 |
| P-RNTI | 寻呼等公共控制 | 独立公共候选，不当作 C-RNTI |
| 其他专用 RNTI | 配置/过程相关控制 | 先核对标准和网络配置 |

RNTI 位宽、保留范围、掩码端序和各类型适用 DCI 格式必须按目标 Release 核验，不能依据一个工具箱默认值。

## 7. 时域位置

RA-RNTI 的有效性绑定 PRACH occasion 和 RAR 窗口；临时 C-RNTI 绑定 RAR 后的 Msg3/Msg4 过程；C-RNTI 在争用解决成功或相应 MAC 过程后进入后续连接上下文。实现应保存 first_seen、last_seen、状态转换和超时原因。既有连接 UE 没有新 PRACH 时，不能用一个新建 RA-RNTI 去解释其 C-RNTI。

## 8. 频域位置

RNTI 本身不占据独立的频域 RE。它通过 CRC 掩码影响 PDCCH/DCI 的判决；实际候选频域位置仍由 [[03-PDCCH/CORESET|CORESET]]、[[03-PDCCH/Search Space|Search Space]] 和 CCE/REG 映射决定。RA-RNTI 的生成输入包含 PRACH occasion 的频域上下文，但这不意味着 RNTI 是一个频率坐标。

## 9. 数学原理

对 DCI 候选的解码结果 $\hat{\mathbf a}$，RNTI 掩码判决可抽象为：

$$
\mathrm{CRC}(\hat{\mathbf a})
\oplus \mathrm{mask}(r)
=\mathbf{0},
$$

其中 $r$ 是待检 RNTI 假设。定义候选接受指示：

$$
q(r,h)
=\mathbf{1}\left[
\mathrm{CRC}_{r}(\hat{\mathbf a}_h)=0
\right].
$$

只有当 q=1 且候选资源、DCI 字段、时间连续性和过程上下文一致时，才把 RNTI 状态升级：

$$
\mathrm{state}_{t+1}
=\Psi(\mathrm{state}_t,q,\mathrm{RAR},\mathrm{Msg3},\mathrm{Msg4},\mathrm{DCI}).
$$

对常见 4-step RA，已有 [[02-PRACH/RA-RNTI|RA-RNTI]] 笔记记录过版本化的 occasion 映射公式；该公式的字段含义、2-step/CFRA 分支和常数必须与目标 TS 38.321 版本重新核对，不能跨场景套用。

## 10. 3GPP 对应规范

| 规范 | 相关内容 | Clause/字段状态 |
|---|---|---|
| TS 38.212 | DCI CRC 附加、RNTI 掩码、Polar/率匹配接口 | DCI/控制信息 §5.3 相关子条款；Release/位序 NEEDS_EXTERNAL_REFERENCE |
| TS 38.213 | PDCCH 监测、RNTI 上下文和控制接收过程 | 控制信道接收 §10 范围；精确子条款 NEEDS_EXTERNAL_REFERENCE |
| TS 38.321 | Random Access、RAR、争用解决、RNTI/MAC CE 状态 | 常用参考 §5.1.3、§5.1.4、§5.1.5、§6.1.3、§6.2.3；版本/字段需外部核验 |
| TS 38.331 | RRC 提供的 Search Space、CORESET、专用配置 | ASN.1 字段版本需外部核验 |

本地 [[01-专题知识/5G定位/NR PRACH 检测与 RA-RNTI-C-RNTI 关联|PRACH-RNTI 关联笔记]] 已明确“PRACH 不能直接解出 C-RNTI”，并给出 4-step 证据链；它属于 PERSONAL_NOTE + STANDARD partial 组织，不替代当前 Release 规范。

## 11. MATLAB / MATLAB 5G Toolbox 对应函数

| 函数/接口 | 用途 | 状态 |
|---|---|---|
| nrDCIDecode | 在候选 DCI 解码时尝试 RNTI/CRC 上下文 | NEEDS_EXTERNAL_REFERENCE；核对参数和返回状态 |
| nrPDCCHDecode | 提供候选软比特给 DCI/RNTI 判决 | NEEDS_EXTERNAL_REFERENCE |
| nrPRACHDetect | 生成 PRACH 前导/occasion 观测，作为 RA-RNTI 输入 | NEEDS_EXTERNAL_REFERENCE；不是 C-RNTI 解码器 |

当前 Vault 没有可运行的 RNTI API 单元测试。MATLAB 函数名、RNTI 参数类型、CRC 位序和 2-step/4-step 支持需在本机版本中确认。

## 12. 本项目中的用途

RNTI 负责把 PRACH 事件接到 C-RNTI 驱动的控制链：

1. [[02-PRACH/PRACH Occasion|PRACH Occasion]] 和前导检测产生事件键。
2. 根据 occasion 生成 RA-RNTI 候选，在 RAR 窗口盯住 RA-RNTI PDCCH。
3. 解析 [[02-PRACH/RAR|RAR]]，记录 TA、UL grant 和 TEMPORARY-C-RNTI。
4. 按 [[02-PRACH/Msg3|Msg3]]/Msg4 证据完成争用解决，升级为 [[02-PRACH/C-RNTI|C-RNTI]] 候选或确认状态。
5. 用 C-RNTI 约束 [[03-PDCCH/PDCCH Blind Decoding|PDCCH Blind Decoding]]，得到 [[03-PDCCH/DCI|DCI]] 并驱动 [[04-PDSCH/PDSCH|PDSCH]]。
6. 把 RNTI 状态、时隙和资源快照传递给定位观测，形成可追溯的 UE 事件键。

## 13. 常见误区

- 把 PRACH 前导索引、RA Occasion 或 RA-RNTI 直接写入 c_rnti 字段。
- 把 RAR 中的 TEMPORARY-C-RNTI 当成已经完成争用解决的 C-RNTI。
- 只凭一个候选 CRC pass 就确认 C-RNTI，忽略 RAPID、Msg3/Msg4 和后续 DCI 连续性。
- 把 RNTI 当作永久、全网唯一的用户身份或加密密钥。
- 把公共 SI-RNTI/P-RNTI 候选混入 C-RNTI 误检率。
- 忽略 2-step RA、CFRA、重同步和 RRC 重配置等分支，套用 4-step 状态机。

## 14. 与相似概念的区别

| 概念 | 代表什么 | 与 RNTI 的区别 |
|---|---|---|
| PRACH preamble | 随机接入序列选择 | 是物理事件，不是控制掩码 |
| RA Occasion | 前导的时频机会 | 是 RNTI 生成输入，不是 RNTI |
| RA-RNTI | RAR 窗口上下文 | 不等于临时或最终 C-RNTI |
| TEMPORARY-C-RNTI | RAR 后临时标识 | 需后续过程确认/转入连接上下文 |
| C-RNTI | 连接期间 UE 专用控制上下文 | 仍是临时网络标识，不是上层永久身份 |
| CRC | 错误检测结果 | RNTI 可作为 CRC 掩码输入 |

## 15. 代码实现注意事项

- 用状态机保存 rnti_type、值、来源事件、有效期、置信度和状态转换原因。
- 将 RNTI 候选池按来源分组（RA 驱动、历史、测试、公共），统计时分开。
- CRC 掩码函数必须显式记录位序/端序和标准 Release；禁止在不同 RNTI 类型间复用未经验证的实现。
- C-RNTI 确认需要多证据门：RAPID/临时标识、Msg3/Msg4、后续 DCI、资源和时序一致性。
- 对 RNTI 重用、超时、BWP/RRC 切换和小区切换使缓存失效，避免旧用户污染新事件。
- 事件日志同时保留候选值和拒绝值，便于计算误关联率和定位故障。

## 16. 待实验验证的问题

- [ ] 用已知 4-step RA 样本验证 PRACH occasion -> RA-RNTI -> RAR 的映射闭环。
- [ ] 在 RAR 中区分 RAPID、TA、UL grant 和 TEMPORARY-C-RNTI，并关联到 Msg3。
- [ ] 构造错误 RNTI、错误 RAPID、碰撞和超时样本，确认状态不会错误升级为 C-RNTI。
- [ ] 验证正确 C-RNTI 驱动的 PDCCH DCI 连续性，以及历史池老化/重用规则。
- [ ] 单独测试 2-step RA/CFRA 分支，在配置未确认时保持 NEEDS_EXTERNAL_REFERENCE。

## 17. RNTI 类型谱系

RNTI 类型首先按“公共控制、接入过程、专用 UE、过程控制”分组。下表是接收端建立候选池的分类入口；精确保留范围、适用 DCI 格式和生效条件必须按目标 Release 核验：

| 分组 | 类型示例 | 控制用途 | 项目处理 |
|---|---|---|---|
| 公共控制 | `SI-RNTI`、`P-RNTI` | 系统信息、寻呼等 | 独立统计，不归入某个 UE |
| 随机接入 | `RA-RNTI`、`MSGB-RNTI`、`TC-RNTI`（本库也写作 `TEMPORARY-C-RNTI`） | RAR/MsgB 响应窗口及接入过程 | 绑定 RO、窗口和载波；短时有效 |
| UE 专用 | `C-RNTI`、`CS-RNTI` | 专用调度或配置授权 | 绑定 UE 证据、BWP 和生命周期 |
| 功控/过程 | `TPC-PUSCH-RNTI`、`TPC-PUCCH-RNTI`、`TPC-SRS-RNTI`、`SFI-RNTI`、`INT-RNTI`、`SP-CSI-RNTI` 等 | 组控制、功控、时隙/抢占或 CSI 过程 | 只有配置明确启用才加入对应分支 |

类型名相近不代表可以互换 CRC 掩码。尤其是 `RA-RNTI`、`MSGB-RNTI`、`TEMPORARY-C-RNTI` 和 `C-RNTI` 的生命周期不同；`TEMPORARY-C-RNTI` 是 RAR/接入过程中的临时 UE 标识，不应直接写成已确认的连接键。

## 18. CRC 掩码不是物理扰码

实现至少分开命名以下两个操作：

```text
DCI payload + CRC
    -> 用 RNTI 对 CRC 字段做掩码（协议上下文）
    -> Polar/率匹配
    -> PDCCH 比特扰码/调制（物理传输）
```

接收端逆处理时，PDCCH 物理解扰应先按物理层规则完成；Polar 译码后再按候选 RNTI 检查 CRC 掩码。不要把 RNTI 当作随机序列初始化，也不要在软比特阶段直接 XOR 一个整数：

$$
q(r,h)=\mathbf{1}\left[
\mathrm{CRC}(\hat{a}_h)\oplus\mathrm{mask}(r)=\mathbf{0}
\right].
$$

CRC 长度、掩码比特顺序、物理扰码初始化和候选 RNTI 适用范围必须由同一 TS 38.212/38.211 Release 核验。当前只保留接口，不把位序或常数写成未经验证的实现。

## 19. RNTI 证据状态机

协议状态与接收端证据状态应分开。建议用以下证据状态描述“目前证明了什么”：

```text
unknown
  -> candidate (数值/类型有来源，但未匹配控制)
  -> control_seen (至少一个合法候选通过 CRC/RNTI)
  -> process_consistent (字段、时序、资源与过程一致)
  -> confirmed (RA/争用解决或明确专用证据支持)
  -> tracked (跨时隙持续观察)
  -> expired (超过有效窗口/配置变更)
```

任意阶段都可能进入 `ambiguous` 或 `rejected`，但原始候选不可删除：

| 升级条件 | 最低证据 | 不足时的状态 |
|---|---|---|
| `candidate` | RNTI 数值、类型和来源事件齐全 | `unknown` |
| `control_seen` | 合法候选、CRC/RNTI 通过 | 仍可为 `candidate_only` |
| `process_consistent` | DCI 字段/资源/时序可解释 | `rnti_suspect` |
| `confirmed` | RAR/Msg3/Msg4、C-RNTI CE 或明确专用配置证据 | `ambiguous` |
| `tracked` | 连续窗口内同一配置和资源行为一致 | `expired`/`reused` |

单个 CRC pass 只能推进到 `control_seen`，不能跳过协议证据直接升级到 `confirmed`。

## 20. 候选池优先级与老化

为了控制盲搜复杂度，候选池应按来源和可信度分层：

| 优先级 | 来源 | 默认有效范围 | 处理策略 |
|---:|---|---|---|
| 1 | 当前 RA 事件产生的 RA/MSGB-RNTI | 对应响应窗口 | 只在 CSS 和窗口内尝试 |
| 2 | RAR 得到的 TEMPORARY-C-RNTI | 当前接入过程 | 绑定 RAPID、grant、Msg3/Msg4 |
| 3 | 已确认 C-RNTI/专用 RNTI | 配置和连接生命周期 | 绑定 `config_id`、BWP、最后观测 slot |
| 4 | 历史缓存 RNTI | 明确的老化窗口 | 只作低优先级候选并单独统计 |
| 5 | 测试/理论候选池 | 仅实验 | 不得与现场误检混报 |

每个条目至少有 `first_seen`、`last_seen`、`valid_until`、`source_event`、`config_id` 和 `expiry_reason`。RRC/BWP/小区切换、RA 超时、争用失败和 RNTI 重用都可能使旧条目失效。

## 21. RNTI 冲突与误关联

RNTI 数值在不同小区、不同时间或不同过程里可能重用；数值相同不等于同一 UE。候选去重键建议为：

```js
(cell_id, capture_id, config_id, rnti_type, rnti_value,
 source_event, valid_time_window)
```

以下情况要保留多分支而不是强行选一个：

| 情况 | 风险 | 输出 |
|---|---|---|
| 同一 RNTI 在两个候选位置通过 | 候选碰撞或误检 | `candidate_collision`，保留两个 candidate_id |
| 不同 RNTI 在同一候选通过 | CRC/位序/低 SNR 歧义 | `rnti_ambiguous`，等待字段/连续性证据 |
| RA-RNTI 与 C-RNTI 数值相同 | 语义和窗口混淆 | 以类型/来源/窗口隔离 |
| 跨小区复用同一值 | 错误跨站关联 | 以 cell/capture 隔离 |
| 旧 C-RNTI 在新 BWP 继续通过 | 缓存污染 | 标 `expired`，重新建立候选 |

误关联率的分母应明确是“RNTI 尝试数”“候选数”还是“事件数”；不能用最终位置数量代替。

## 22. 与 RA 事件的证据连接

RNTI 记录应把 RA 过程的中间消息作为可追溯引用：

```js
association_record:
  event_id: ""
  ro_context_ref: ""
  preamble_index: null
  ra_rnti: null
  msgb_rnti: null
  temporary_c_rnti: null
  c_rnti: null
  evidence_refs:
    - rar_pdcch_candidate: ""
    - rar_tb_crc: ""
    - rapid_match: false
    - msg3_resource: ""
    - msg4_or_success_rar: ""
  state: "candidate|ambiguous|confirmed|expired|rejected"
  failure_reason: ""
```

`RAPID` 匹配只能说明 RAR 与某个前导相容；还要结合 grant、Msg3/Msg4 或适用的 2-step/CFRA 分支。相关 RO 和公式见 [[02-PRACH/RA-RNTI|RA-RNTI]]，不要在本页复制一份可能过期的常数。

## 23. 定位事件键的使用

RNTI 适合做“控制上下文标签”，不适合单独做“物理身份真值”。传给定位支路时至少附带：

- `rnti_type/value`、证据状态和有效时间窗；
- 关联的 DCI `candidate_id`、数据资源和方向；
- `cell_id`、`config_id`、站点和采样起点；
- 关联置信度、冲突/碰撞标志和拒绝原因。

只有 `confirmed`/`tracked` 且资源、时序一致的事件，才适合进入单用户上行掩码；`candidate_only` 事件可以保留作待验证样本，但不应被标成确定的 UE ToA/TDoA。

## 24. RNTI 验证矩阵

| 测试 | 操作 | 预期结果 |
|---|---|---|
| 掩码正例 | 正确 DCI + 正确 RNTI | CRC pass，状态不自动越级 |
| 掩码负例 | 正确 DCI + 错误 RNTI | CRC fail，记录尝试来源 |
| 资源负例 | 错误候选 + 正确 RNTI | 不应仅凭 CRC 通过接受 |
| RA 关联 | 正确 RO/RAPID/临时标识 | 逐状态升级并保留引用 |
| 碰撞 | 同 RO 同前导多 UE | `ambiguous`，不合并身份 |
| 超时 | RAR/争用解决窗口过期 | 条目 `expired`，停止默认尝试 |
| 重用 | 新小区/新配置复用同数值 | 事件键隔离，禁止跨上下文合并 |
| 2-step/CFRA | 切换接入分支 | 未确认分支时保持 `NEEDS_VERIFICATION` |

## 25. Rel-17 V17.8.0 RNTI 判决核验基线

对照 [ETSI TS 138 212 V17.8.0](https://www.etsi.org/deliver/etsi_ts/138200_138299/138212/17.08.00_60/ts_138212v170800p.pdf) §7.3.2 和 [ETSI TS 138 213 V17.8.0](https://www.etsi.org/deliver/etsi_ts/138200_138299/138213/17.08.00_60/ts_138213v170800p.pdf) §10.1（访问日期 2026-09-05），可以确认以下实现边界：

1. DCI 整个 payload 参与 CRC 计算；参考版本使用 24-bit `CRC24C`，`K=A+24`。
2. RNTI 的 16 bit 只掩码 CRC parity 的后 16 个位置，且规范把 RNTI 的 MSB 放在掩码序列的第一个位置；不能把一个整数直接 XOR 到 payload 或全部 CRC。
3. DCI 译码完成后才做 RNTI/CRC 判决；RNTI 掩码与 TS 38.211 的 PDCCH 物理比特扰码是两个不同阶段。
4. CSS/USS 及 RA-RNTI、MsgB-RNTI、TC-RNTI、C-RNTI 等适用上下文由 Search Space 和控制过程决定；同一个数值在不同类型/小区/窗口中不能直接合并。

上述是 Rel-17 参考版本的标准事实；当前项目 Release、2-step/4-step、CFRA/BFR 和专用 RRC 状态仍需按现场快照复核。

## 26. 证据与当前状态

- `STANDARD + verified-reference`：本地 TS 38.212/38.213/38.321 相关笔记，以及上面的 Rel-17 V17.8.0 CRC/RNTI 参考版本。
- `PERSONAL_NOTE`：本页的候选池优先级、证据状态机、老化和定位事件键。
- `NEEDS_EXTERNAL_REFERENCE`：当前项目 Release 的 RNTI 类型完整清单、保留范围、特殊过程、现场配置和工具箱行为。
- `EXPERIMENT + NEEDS_VERIFICATION`：尚无现场 RNTI 尝试数、误关联率或跨时隙跟踪结果。

## 27. Related Notes

- [[03-PDCCH/PDCCH Overview|PDCCH Overview]]
- [[03-PDCCH/CORESET|CORESET]]
- [[03-PDCCH/Search Space|Search Space]]
- [[03-PDCCH/DCI|DCI]]
- [[03-PDCCH/PDCCH Blind Decoding|PDCCH Blind Decoding]]
- [[02-PRACH/PRACH Overview|PRACH Overview]]
- [[02-PRACH/PRACH Occasion|PRACH Occasion]]
- [[02-PRACH/RA-RNTI|RA-RNTI]]
- [[02-PRACH/RAR|RAR]]
- [[02-PRACH/Msg3|Msg3]]
- [[02-PRACH/C-RNTI|C-RNTI]]
- [[01-专题知识/5G定位/NR PRACH 检测与 RA-RNTI-C-RNTI 关联|NR PRACH 检测与 RA-RNTI-C-RNTI 关联]]
- [[01-专题知识/信道编译码/NR编码链/NR-DCI 编码链|NR-DCI 编码链]]
- [[04-PDSCH/PDSCH|PDSCH]]
- [[03-PDCCH/PDCCH Implementation Contract|PDCCH Implementation Contract]]
