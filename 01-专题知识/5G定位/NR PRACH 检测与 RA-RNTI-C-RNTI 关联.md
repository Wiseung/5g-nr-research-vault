---
title: NR PRACH 检测与 RA-RNTI-C-RNTI 关联
aliases:
  - 5G PRACH 解码与 C-RNTI 获取
  - NR 随机接入前导检测
type: atomic
status: seed
created: 2026-09-04
tags:
  - domain/5g-nr
  - channel/prach
  - channel/random-access
  - topic/定位
  - topic/用户关联
  - process/detection
  - evidence/3gpp
source:
  - 3GPP TS 38.211
  - 3GPP TS 38.213
  - 3GPP TS 38.321
  - 用户项目流程说明
simulation:
  - 仿真：PRACH 检测与 RA 事件关联
related:
  - "[[02 参考信号与导频设计]]"
  - "[[5G TDD 上下行监测与资源解析]]"
  - "[[NR PDCCH 盲搜与 PDSCH-PUSCH 资源解析]]"
  - "[[多站 UL-TDOA 定位与同步]]"
---

# NR PRACH 检测与 RA-RNTI-C-RNTI 关联

> [!warning] 关键纠偏
> PRACH 前导本身通常只提供随机接入事件、前导索引和到达时延等观测，不能单独“解出”连接期间使用的 C-RNTI（Cell Radio Network Temporary Identifier）。要建立 C-RNTI 关联，至少还要跟踪 RAR、临时 C-RNTI、Msg3/Msg4 及争用解决过程；如果抓包窗口内没有新的随机接入，PRACH 也不能作为既有用户 C-RNTI 的来源。

## 1. 四个对象不要混淆

| 对象 | 所在过程/承载 | 第三方可观察的证据 | 是否等于用户身份 |
|---|---|---|---|
| PRACH 前导/`preamble index` | Msg1，物理随机接入 | 相关峰、时域/频域 occasion、功率和时延 | 否；同一 occasion 可能发生碰撞 |
| RA-RNTI | RAR 的 PDCCH 寻址上下文 | 由 PRACH occasion 推导的候选掩码 | 否；它标识响应窗口/资源上下文 |
| TEMPORARY-C-RNTI | RAR 中的随机接入响应字段 | RAR PDSCH 解码后的 MAC 字段 | 过程中的临时标识 |
| C-RNTI | 后续 UE 专用控制/数据寻址 | 争用解决成功后的 RNTI CRC 掩码和时序证据；也可能由 Msg3 的 C-RNTI MAC CE 提供 | 可作为用户关联键，但仍需跨帧验证 |

表中“标准事实”依赖 TS 38.211/38.213/38.321 的适用 Release；具体 RA-RNTI 位构成、2-step/4-step 分支和字段语义应按当前版本核对，不在这里硬编码一个跨版本公式。

在已锁定的 TS 38.321 版本中，RA-RNTI 可按 PRACH occasion 的时域、频域和上行载波索引计算；常见写法为：

$$
RA\text{-}RNTI=1+s_{id}+14t_{id}+14\cdot80f_{id}+14\cdot80\cdot8\,ul\_carrier\_id.
$$

这里的 $s_{id}$、$t_{id}$、$f_{id}$ 和 `ul_carrier_id` 必须从同一版本的 PRACH occasion 定义取得。该式是版本化标准接口，不应脱离配置或直接套用到 2-step/特殊场景。

## 2. 4-step RA 的关联链

对常见 4-step 随机接入，第三方接收机可按下面的证据链尝试建立关联：

```text
Msg1: UE 发送 PRACH 前导
    ↓  (preamble index + PRACH occasion + timing)
由 occasion 生成 RA-RNTI 候选
    ↓
Msg2/RAR: RA-RNTI 寻址的 PDCCH + PDSCH
    ↓  (RAPID 匹配、TA、UL grant、TEMPORARY-C-RNTI)
Msg3: 按 UL grant 发送 PUSCH（CCCH SDU 或 C-RNTI MAC CE）
    ↓
Msg4: PDCCH/PDSCH 争用解决
    ↓
TEMPORARY-C-RNTI 成功转为/确认 C-RNTI（依过程分支）
```

第三方的“用户区分”应写成**关联置信度**，而不是把一个相关峰直接命名为用户 ID。建议关联键为：

$$
e_{RA}=(\mathrm{cell},\mathrm{frame},\mathrm{slot},\mathrm{RO}_{t},\mathrm{RO}_{f},\mathrm{preamble},\widehat{\tau},\mathrm{SSB/beam})
$$

随后用 `RAR-RAPID`、临时 C-RNTI、Msg3 时频资源、Msg4 寻址和后续 DCI 的时间连续性更新 `association_key`。

### 2.1 状态机与分支

| 状态 | 进入条件 | 第三方可保存的证据 | 失败/分支 |
|---|---|---|---|
| `RA_IDLE` | 尚未观测到有效前导 | 配置快照和监测窗口 | 不代表小区没有用户 |
| `MSG1_DETECTED` | PRACH 峰通过门限 | RO、前导、TOA、功率、碰撞标记 | 多峰/低 SNR 时为 `ambiguous` |
| `RAR_WINDOW` | 已由 RO 生成 RA-RNTI 候选 | RA-RNTI、监测时机和候选 PDCCH | RAR 未检测或 RAPID 不匹配 |
| `TEMP_C_RNTI` | RAR 成功且字段可解析 | TA、UL grant、TEMPORARY-C-RNTI | MAC/PHY 字段缺失 |
| `MSG3_PENDING` | UL grant 指向后续 PUSCH | Msg3 资源、方向、候选临时 RNTI | TDD 标注或资源解析失败 |
| `CONTENTION_RESOLUTION` | Msg3 已观测 | Msg4 候选、争用解决身份、CRC | 超时、错误身份或碰撞 |
| `C_RNTI_CONFIRMED` | 争用解决成功或 C-RNTI MAC CE 路径成立 | C-RNTI 掩码、后续 DCI 连续性 | 只保留为临时/候选关联 |

4-step CBRA、4-step CFRA、2-step RA（MsgA/MsgB）和重同步/波束恢复的状态转换不同。当前页以 4-step CBRA 为主线，其他分支在配置未确认前必须标 `TODO`，不能把所有 PRACH 峰都套用同一 Msg3/Msg4 解释。

同一个 RAR MAC PDU 可能包含多个与前导对应的 RAPID 子 PDU；第三方应按 `RAPID ↔ preamble index` 逐项匹配，而不是假设一个 PRACH occasion 只有一个用户或一个 RAR。

## 3. PRACH 检测模型

现有 [[02 参考信号与导频设计#2.8 PRACH 前导与信道估计的区别]] 给出相关检测基线。对已知前导 $u[n]$：

$$
r[n]=\alpha u[n-n_0]+w[n],
\qquad
z[\ell]=\sum_n r[n]u^*[n-\ell]
$$

粗略峰值估计为：

$$
\widehat{n}_0=\arg\max_\ell |z[\ell]|,
\qquad
\widehat{\tau}=\frac{\widehat{n}_0+\delta_{frac}}{F_s}
$$

其中 $\delta_{frac}$ 是可选的亚采样峰值修正，必须记录采用的插值/拟合方法。有效 PRACH 带宽给出时延分辨率的数量级 $\Delta\tau\approx1/B_{RA}$；这不是完整 PDSCH/PUSCH CSI 的估计精度。

### 检测输出

每个峰至少保存：

| 字段 | 含义 |
|---|---|
| `preamble_index` | 在当前候选集合中的前导编号 |
| `time_occasion` / `freq_occasion` | PRACH 时频资源坐标 |
| `correlation_peak` | 相关峰值及归一化方式 |
| `timing_offset_samples` | 相对捕获起点的样点偏移 |
| `fractional_delay` | 亚采样修正及方法 |
| `cfo_estimate` | 频偏估计或未估计标记 |
| `multipath_peaks` | 多径峰/峰宽/旁瓣诊断 |
| `threshold` | 检测门限和自适应规则 |
| `collision_flag` | 同 occasion 多用户/多峰风险 |

## 4. 从 PRACH 到 C-RNTI 的接收算法

1. 读取当前小区的 PRACH 格式、根序列、循环移位、频域 occasion、时域 occasion 和检测窗口。
2. 只在合法 PRACH 资源上做匹配滤波；保存原始相关轨迹，不只保存最大峰。
3. 对峰值做门限、峰间距、旁瓣和多径检查，输出 `energy_seen`、`preamble_detected` 或 `ambiguous`。
4. 将 `(occasion, preamble index)` 映射到 RA-RNTI 候选；不要把 RA-RNTI 当作 C-RNTI。
5. 在相应 RAR 窗口监测 RA-RNTI 寻址的 PDCCH，解码 RAR PDSCH，并验证 RAPID 是否与该前导匹配。
6. 记录 RAR 的 TA、UL grant 和 TEMPORARY-C-RNTI；把临时标识绑定到该 `e_RA` 事件。
7. 按 UL grant 在 Msg3 资源上检测 PUSCH，判断是否出现 CCCH SDU 或 C-RNTI MAC CE。
8. 在争用解决窗口监测 Msg4，检查临时 RNTI/用户争用解决身份和后续 C-RNTI 寻址证据。
9. 只有在跨消息、跨时隙和字段约束一致时，才把状态升级为 `user_associated`；否则保留 `candidate_associated`。

## 5. 重要失效边界

| 情况 | 能否从 PRACH 直接得到 C-RNTI | 处理 |
|---|---:|---|
| 新的 4-step RA，RAR/Msg3/Msg4 全部可见 | 否，但可逐步关联 | 保存完整状态机证据 |
| 只有 Msg1 可见 | 否 | 只输出前导/时延事件 |
| 多个 UE 同一 occasion 同一前导 | 否 | 标记碰撞，不能强行拆分用户 |
| 既有连接用户，没有新的 RA | 否 | 从已知 C-RNTI 候选或更高层上下文开始 |
| 2-step RA 或专用无争用 RA | 不按 4-step 链套用 | 单独核对 MsgA/MsgB 和配置 |
| RAR/PHY 资源不可见、上层安全保护或 SNR 不足 | 不一定 | 将 PHY 解码、MAC 字段可见性和上层解密分开记录，避免把 CRC 失败归因于 PRACH |

PRACH 检测到的相关峰还可能包含多径、频偏、采样时钟偏差和邻接前导干扰。峰值位置可作为粗 TOA/事件触发，但不能未经校准直接当作绝对距离。

## 6. MATLAB 入口与版本门槛

MathWorks 官方 `nrPRACHDetect` 页面描述了：对时域波形生成内部参考并做相关检测，返回检测到的前导索引、样点时延和检测信息；该接口适合作为 PRACH 检测单元测试入口：

- [nrPRACHDetect 官方文档](https://www.mathworks.com/help/5g/ref/nrprachdetect.html)
- [5G NR PRACH 波形生成示例](https://www.mathworks.com/help/5g/ug/5g-nr-prach-waveform-generation.html)

函数属性、Release 版本、短/长前导支持和多实例返回行为必须在本机 MATLAB/5G Toolbox 版本上再核对。当前库没有本项目 MATLAB 脚本，故所有 API 映射仍是 `NEEDS_EXTERNAL_REFERENCE`，不能把文档示例当作已运行结果。

### 6.1 已知前导模板相关与 RA-RNTI

下面的相关器适用于对配置解析器生成的候选参考波形做检测单元测试；它不是 PRACH 序列生成器，也没有替代 `nrPRACHDetect` 对 PRACH 格式、occasion 和接收配置的处理。将函数分别保存为对应名称的 `.m` 文件。每个模板返回归一化相关轨迹，峰值偏移相对于捕获窗口起点。

```matlab
function result = detectPrachTemplateBank(rx, templates, sampleRateHz, threshold)
% rx: N-by-1 复数采样；templates: L-by-Ncandidate 复数模板
rx = rx(:);
if isvector(templates)
    templates = templates(:);
end
assert(size(templates, 1) <= numel(rx), ...
    "模板长度不能超过接收窗口");
assert(sampleRateHz > 0 && threshold >= 0 && threshold <= 1);

nCandidate = size(templates, 2);
result = repmat(struct("candidateIndex", 0, "detected", false, ...
    "peak", NaN, "sampleOffset", NaN, "toaSeconds", NaN, ...
    "metric", []), nCandidate, 1);

for p = 1:nCandidate
    ref = templates(:, p);
    refEnergy = sum(abs(ref).^2);
    assert(refEnergy > 0, "候选模板不能为零向量");

    corrTrace = conv(rx, conj(flipud(ref)), "valid");
    rxEnergy = conv(abs(rx).^2, ones(numel(ref), 1), "valid");
    metric = abs(corrTrace) ./ ...
        (sqrt(refEnergy .* rxEnergy) + eps);
    [peak, index] = max(metric);

    % 三点抛物线插值；边界峰不做亚采样修正
    delta = 0;
    if index > 1 && index < numel(metric)
        left = metric(index - 1);
        center = metric(index);
        right = metric(index + 1);
        denominator = left - 2 * center + right;
        if abs(denominator) > eps
            delta = 0.5 * (left - right) / denominator;
            delta = max(-0.5, min(0.5, delta));
        end
    end

    sampleOffset = (index - 1) + delta; % 零基样点偏移
    result(p).candidateIndex = p - 1;
    result(p).detected = peak >= threshold;
    result(p).peak = peak;
    result(p).sampleOffset = sampleOffset;
    result(p).toaSeconds = sampleOffset / sampleRateHz;
    result(p).metric = metric;
end
end
```

```matlab
function raRnti = raRntiFromOccasion(sId, tId, fId, ulCarrierId)
% 仅用于已锁定且确认适用该 TS 38.321 版本/过程分支。
v = [sId, tId, fId, ulCarrierId];
assert(all(isfinite(v) & v >= 0 & v == floor(v)), ...
    "occasion 索引必须是非负整数");
raRnti = 1 + sId + 14 * tId + 14 * 80 * fId + ...
    14 * 80 * 8 * ulCarrierId;
end
```

模板的列顺序必须与 `candidateIndex` 到协议前导索引的映射表一致；实际 ToA 还要考虑捕获起点、采样时钟、CFO、多径和接收链延迟。该代码只产出前导候选与时延观测，不能据此把状态升级为 `C_RNTI_CONFIRMED`；RAR、Msg3/Msg4 和后续控制信道证据仍需独立解码与关联。

## 7. 故障定位矩阵

| 现象 | 首先检查 | 不要直接下的结论 |
|---|---|---|
| 无相关峰 | 资源配置、根序列、SCS、CFO、窗口 | “现场没有用户” |
| 峰位置漂移 | 采样时钟、CP/窗口、频偏、多径 | “TDOA 算法错” |
| RAPID 不匹配 | occasion/SSB 关联、前导索引、RA-RNTI 计算 | “C-RNTI 解码失败” |
| RAR CRC 失败 | PDCCH 候选、PDSCH 资源、DM-RS、LLR | “PRACH 检测错” |
| 多个 C-RNTI 候选 | CRC、字段合法性、时序连续性、碰撞 | “所有候选都是真用户” |
| Msg3/Msg4 不可见 | TDD 方向标注、UL grant、捕获窗口、遮挡 | “临时 C-RNTI 无效” |

## 证据与出处

- `STANDARD + partial`： [ETSI TS 38.211 V17.7.0](https://www.etsi.org/deliver/etsi_ts/138200_138299/138211/17.07.00_60/ts_138211v170700p.pdf)，重点核对 §5.3.2、§6.3.3 的 PRACH 波形、序列和资源映射。
- `STANDARD + partial`： [ETSI TS 38.321 V16.21.0](https://www.etsi.org/deliver/etsi_ts/138300_138399/138321/16.21.00_60/ts_138321v162100p.pdf)，重点核对 §5.1.3 Random Access Preamble transmission、§5.1.4 Random Access Response、§5.1.5 Contention Resolution、§6.1.3 MAC CE 和 §6.2.3 RAR；版本与项目网络可能不同。
- `STANDARD + partial`： [ETSI TS 38.213 V17.7.0](https://www.etsi.org/deliver/etsi_ts/138200_138299/138213/17.07.00_60/ts_138213v170700p.pdf)，重点核对 §8.1 PRACH occasion/资源和 §8.2/§8.2A RAR 上下文；正式引用以项目锁定版本为准。
- `PERSONAL_NOTE`：[[02 参考信号与导频设计#2.8 PRACH 前导与信道估计的区别]]。
- `PERSONAL_NOTE`：用户提供的“先通过 PRACH 区分用户，再解 C-RNTI”的项目流程；本页对其中“PRACH 直接给 C-RNTI”的隐含假设作了协议边界修正。

## 当前状态

- `EXPERIMENT + NEEDS_VERIFICATION`：未接入嘉琪的真实 PRACH MATLAB 工程和采集数据。
- `TODO`：确认当前网络是 2-step 还是 4-step RA、是否能捕获 RAR/Msg3/Msg4，以及项目将 C-RNTI 关联到哪一个消息边界。

## 项目化入口

- PRACH 原子笔记集：[[5G-NR-Positioning/02-PRACH/PRACH Overview]]、[[5G-NR-Positioning/02-PRACH/Random Access Procedure]]、[[5G-NR-Positioning/02-PRACH/C-RNTI]]
- 项目主线：[[5G-NR-Positioning/00-项目总览/5G NR Passive Positioning Pipeline]]
