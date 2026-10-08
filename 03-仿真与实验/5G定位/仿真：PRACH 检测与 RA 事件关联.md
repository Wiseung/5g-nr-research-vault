---
title: 仿真：PRACH 检测与 RA 事件关联
aliases:
  - 仿真 NR PRACH 到达时间检测
  - PRACH TOA 仿真
type: experiment
status: seed
created: 2026-09-04
tags:
  - domain/5g-nr
  - channel/prach
  - topic/定位
  - stage/simulation
  - stage/verification
  - metric/detection
  - metric/toa
  - evidence/3gpp
source:
  - 3GPP TS 38.211
  - 3GPP TS 38.213
  - 3GPP TS 38.321
  - 02 参考信号与导频设计
simulation:
  - 仿真：PRACH 检测与 RA 事件关联
related:
  - "[[NR PRACH 检测与 RA-RNTI-C-RNTI 关联]]"
  - "[[5G TDD 上下行监测与资源解析]]"
  - "[[多站 UL-TDOA 定位与同步]]"
---

# 仿真：PRACH 检测与 RA 事件关联

> [!abstract] 实验性质
> 本页是 `EXPERIMENT + NEEDS_VERIFICATION` 的设计模板，不包含已运行的检测率、时延误差或 C-RNTI 结果。目标是先验证 PRACH 相关峰和资源坐标，再验证 RAR/Msg3/Msg4 的事件关联。

## 1. 实验目标与边界

### 目标

1. 在已知 PRACH 配置下生成并检测单个前导，验证 `preamble_index`、occasion 和样点偏移。
2. 测量 AWGN、CFO、采样时钟偏差、多径和窗口截断对相关峰及 TOA 的影响。
3. 构造同一 occasion 的多个前导/碰撞，验证峰保留、误检和“最强峰不等于全部用户”的边界。
4. 用一个可控的 4-step RA 状态机把 PRACH 事件与 RA-RNTI、RAR 的 TEMPORARY-C-RNTI、Msg3/Msg4 关联起来。

### 非目标

- 不把 `nrPRACHDetect` 的单个 strongest peak 输出当作多用户检测器。
- 不把 PRACH 检测通过当作 C-RNTI 已确认。
- 不把仿真结果当作当前运营商网络或 3GPP 全部 Release 的一致性证明。

## 2. 分层验收门

| 门 | 场景 | 必须通过的检查 | 状态 |
|---|---|---|---|
| P0 | 单径、无噪声、单前导 | 序列、资源、峰位置和已知延迟闭合 | 待运行 |
| P1 | AWGN 扫描 | 检测概率、虚警概率、TOA RMSE 有样本量 | 待运行 |
| P2 | CFO/采样率偏差/多径 | 峰宽、首径与最大峰策略可解释 | 待运行 |
| P3 | 多 UE/同 occasion 碰撞 | 全峰轨迹、碰撞标记和用户数上界 | 待运行 |
| P4 | 4-step RA 事件链 | RAPID、TA、UL grant、临时 C-RNTI 与 Msg3/4 状态一致 | 待运行 |

只有 P0/P1 通过后才进入 P2；只有 P3 能区分碰撞后才把结果用于多站 TDOA。

## 3. 参数账本

| 参数 | 试验值/候选 | 记录要求 |
|---|---|---|
| 中心频率 | `120.88e6 Hz` 仅作待确认候选 | 确认它是载频、带宽还是采样率；不得默认 |
| 载波/小区 | `carrier_snapshot` | NCellID、FR、SCS、BWP 和 Release |
| PRACH | `prach_snapshot` | 格式、L_RA、根序列、循环移位、零相关区、功率 |
| occasion | `RO_t`, `RO_f` | 帧、时隙、符号、频域 occasion、SSB 关联 |
| 前导 | 单个/集合 | 实际候选索引和碰撞组合 |
| 采样 | `F_s` | 采样率、FFT、CP、I/Q 类型和时间起点 |
| 延迟 | `n_0`、`δ_frac` | 整数样点、亚采样延迟生成方法 |
| 频偏 | 0、低、中、高 | Hz、归一化 CFO、估计/补偿状态 |
| 信道 | 单径、TDL/CDL 或自定义多径 | 路径延迟、功率、Doppler、随机种子 |
| 噪声 | SNR 轴 | 噪声注入位置和归一化定义 |
| 门限 | 固定/自适应 | 公式、训练窗口和阈值来源 |
| 关联 | 4-step/2-step/CFRA | 当前只先实现哪一分支，其他标 TODO |

## 4. 检测器与参考实现

已知前导 $u_p[n]$ 的匹配滤波基线为：

$$
z_p[\ell]=\sum_n r[n]u_p^*[n-\ell],
\qquad
\widehat{n}_{p}=\arg\max_\ell |z_p[\ell]|.
$$

建议同时实现两条支路：

1. **单峰 API 支路**：用于与官方工具行为对照，记录其返回的索引、偏移和检测信息。
2. **全峰自定义支路**：保留每个前导、每个 occasion 的完整相关轨迹，用峰间距、峰值比、首径规则和门限筛选多个候选。

伪代码：

```text
读取 prach_snapshot
生成合法 PRACH occasion 和前导参考
对每个 occasion/前导执行匹配滤波
保存 correlation_trace，而不是只保存 argmax
检测局部峰、旁瓣和峰簇
估计 integer + fractional delay
输出 preamble event 与 quality_flags
```

## 5. MATLAB 接口核验

MathWorks 官方 [nrPRACHDetect](https://www.mathworks.com/help/5g/ref/nrprachdetect.html) 文档说明该函数在时域波形上生成内部参考并相关检测，返回检测到的前导索引、样点偏移和检测信息；文档还说明多实例输入按 strongest peak 返回。因此本实验必须额外实现或保留全相关曲线，才能覆盖 P3 碰撞场景。

官方 [5G NR PRACH 波形生成示例](https://www.mathworks.com/help/5g/ug/5g-nr-prach-waveform-generation.html) 可作为参数化和资源可视化入口。`nrPRACHConfig`、波形生成和 OFDM 相关函数的属性/签名需用本机 `ver`、`help` 或官方对应 Release 再核对；当前没有已运行 MATLAB 结果，API 状态为 `NEEDS_EXTERNAL_REFERENCE`。

## 6. 指标定义

### 检测概率和虚警

$$
P_D=\frac{N_{\mathrm{detected\;true}}}{N_{\mathrm{true\;events}}},
\qquad
P_{FA}=\frac{N_{\mathrm{false\;peaks}}}{N_{\mathrm{empty\;occasions}}}
$$

明确“事件”是前导、occasion 还是峰；碰撞场景不能把两个真实前导的漏检混入普通虚警。

### TOA 误差

$$
e_{\tau}=\widehat{\tau}-\tau_{true},
\qquad
\mathrm{RMSE}_{\tau}=\sqrt{\frac{1}{N}\sum_{q=1}^{N}e_{\tau,q}^{2}}.
$$

分别报告 strongest-peak、first-detected-path 和峰簇拟合三种策略；如果只有单径，不得据此宣称多径下的首径性能。

### 资源定位准确性

统计 `RO_t`、`RO_f`、`preamble_index`、SSB 关联和方向标签的正确率。资源标签错位即使 TOA 数值看似合理，也不能进入 RA 关联。

## 7. RA 事件关联子实验

从 P3 通过后构造一个最小可控的 4-step 事件链：

```text
PRACH event (RO + preamble)
    ↓
RA-RNTI candidate
    ↓
RAR PDCCH/PDSCH (RAPID + TA + UL grant + TEMPORARY-C-RNTI)
    ↓
Msg3 PUSCH
    ↓
Msg4 contention resolution
    ↓
C-RNTI association state
```

每个状态保存 `event_id`、时间窗口、资源、RNTI、CRC、MAC 字段和失败原因。RAR/Msg3/Msg4 的 MAC 组包和完整 PHY 映射不是本地已有的一键函数，先允许使用合成消息和理想信道；标准字段、2-step/CFRA 分支列为 `TODO + NEEDS_EXTERNAL_REFERENCE`。

## 8. 故障注入矩阵

| 注入 | 预期诊断 | 不应误判为 |
|---|---|---|
| 根序列/循环移位错 | 相关峰消失或旁瓣异常 | 现场无 UE |
| occasion 偏一符号 | 资源标签错、峰偏移 | C-RNTI 无效 |
| CFO 未补偿 | 峰展宽/幅度下降 | 检测器门限单独失效 |
| 截断窗口过短 | 峰形/TOA 偏差 | TDOA 几何错误 |
| 同 occasion 前导碰撞 | 多峰或不可分离 | 每个峰都是真用户 |
| RA-RNTI 计算错 | RAR 候选无匹配 | PRACH 检测失败 |
| RAPID 错 | RAR 关联拒绝 | TEMPORARY-C-RNTI 不存在 |
| Msg4 缺失 | 只能保留临时关联 | PRACH 没有检测到 |

## 9. 结果表模板

| 场景 | SNR | 前导/用户数 | CFO | 多径 | $P_D$ | $P_{FA}$ | TOA RMSE | 首径/最大峰 | 资源正确率 | 关联状态 |
|---|---:|---:|---:|---|---:|---:|---:|---|---:|---|
| P0 |  | 1 | 0 | 单径 |  |  |  |  |  |  |
| P1 |  | 1 | 0 | 单径 |  |  |  |  |  |  |
| P2 |  | 1 |  | TDL |  |  |  |  |  |  |
| P3 |  | 2+ |  | TDL |  |  |  |  |  |  |
| P4 |  | 1 |  |  |  |  |  |  |  |  |

## 11. 伪代码与 MATLAB/Python 基线

以下序列仅用于验证匹配滤波、样点偏移和事件状态门控。它是 Zadoff-Chu 序列的教学级基线，不含 TS 38.211 的 PRACH occasion、CP、循环移位集合、频域映射和完整波形生成；正式 P0/P1 应换成已锁定配置生成的 PRACH 模板或本机 `nrPRACH` 工具链。

### 伪代码

```text
读取并锁定 PRACH 配置与候选前导模板
对每个 occasion:
    生成或读取同一配置下的参考波形
    叠加传播时延、CFO、多径和噪声，保存真值
    对每个候选模板计算归一化滑动相关轨迹
    保存全部轨迹；用门限和峰簇规则标注检测/碰撞
    将样点偏移换算成相对 ToA，并记录插值和质量
    状态置为 MSG1_DETECTED 或 AMBIGUOUS
    只有 RAPID 匹配、RAR、Msg3/Msg4 证据完整时才确认 C-RNTI
```

### MATLAB

```matlab
rng(7);
L = 139;
rootSet = [25, 29, 34]; % 合法互素根的简化测试集合，不是完整 PRACH 配置
n = (0:L-1).';
templates = exp(-1j * pi * ((n .* (n + 1)) / L) * rootSet);

trueCandidate = 2;
trueDelay0 = 37; % 零基样点时延
rx = complex(zeros(L + trueDelay0 + 32, 1));
rx(trueDelay0 + (1:L)) = templates(:, trueCandidate);
snrDb = 20;
noiseVar = 10^(-snrDb / 10); % 单位参考序列功率
rx = rx + sqrt(noiseVar / 2) * ...
    (randn(size(rx)) + 1j * randn(size(rx)));

traceByCandidate = cell(1, numel(rootSet));
peakByCandidate = zeros(1, numel(rootSet));
sampleByCandidate0 = zeros(1, numel(rootSet));
for p = 1:numel(rootSet)
    ref = templates(:, p);
    corrTrace = conv(rx, conj(flipud(ref)), "valid");
    rxEnergy = conv(abs(rx).^2, ones(L, 1), "valid");
    metric = abs(corrTrace) ./ ...
        (sqrt(sum(abs(ref).^2) .* rxEnergy) + eps);
    [peakByCandidate(p), index] = max(metric);
    traceByCandidate{p} = metric;
    delta = 0;
    if index > 1 && index < numel(metric)
        y1 = metric(index - 1);
        y2 = metric(index);
        y3 = metric(index + 1);
        denominator = y1 - 2 * y2 + y3;
        if abs(denominator) > eps
            delta = max(-0.5, min(0.5, ...
                0.5 * (y1 - y3) / denominator));
        end
    end
    sampleByCandidate0(p) = index - 1 + delta;
end

[bestPeak, candidate] = max(peakByCandidate);
threshold = 0.5; % 必须由正例/空 occasion 负例标定
detected = bestPeak >= threshold;
event = struct("candidateIndex", candidate - 1, ...
    "sampleOffset0", sampleByCandidate0(candidate), ...
    "peak", bestPeak, "state", "NO_DETECTION", ...
    "associationState", "candidate_only");
if detected
    event.state = "MSG1_DETECTED";
end

% 只有由独立 PHY/MAC 解码器产生的证据才能升级关联状态。
rarRapidMatched = false;
msg3Observed = false;
msg4Resolved = false;
if detected && rarRapidMatched && msg3Observed && msg4Resolved
    event.associationState = "C_RNTI_CONFIRMED";
end
fprintf("detected=%d candidate=%d delay=%.3f peak=%.3f state=%s\n", ...
    detected, event.candidateIndex, event.sampleOffset0, ...
    event.peak, char(event.state));
```

### Python

```python
import numpy as np

rng = np.random.default_rng(7)
length = 139
roots = np.array([25, 29, 34])  # 简化序列测试集，不是 NR PRACH 配置
n = np.arange(length)[:, None]
templates = np.exp(-1j * np.pi * n * (n + 1) * roots[None, :] / length)

true_candidate = 1
true_delay = 37  # 零基样点时延
rx = np.zeros(length + true_delay + 32, dtype=np.complex128)
rx[true_delay:true_delay + length] = templates[:, true_candidate]
snr_db = 20.0
noise_var = 10.0 ** (-snr_db / 10.0)
rx += np.sqrt(noise_var / 2) * (
    rng.standard_normal(rx.size) + 1j * rng.standard_normal(rx.size)
)

traces = []
peaks = []
offsets = []
for ref in templates.T:
    corr = np.convolve(rx, np.conj(ref[::-1]), mode="valid")
    energy = np.convolve(np.abs(rx) ** 2, np.ones(length), mode="valid")
    metric = np.abs(corr) / (np.sqrt(np.vdot(ref, ref).real * energy) + 1e-12)
    index = int(np.argmax(metric))
    delta = 0.0
    if 0 < index < metric.size - 1:
        y1, y2, y3 = metric[index - 1:index + 2]
        denominator = y1 - 2 * y2 + y3
        if abs(denominator) > 1e-12:
            delta = float(np.clip(0.5 * (y1 - y3) / denominator, -0.5, 0.5))
    traces.append(metric)
    peaks.append(float(metric[index]))
    offsets.append(index + delta)

candidate = int(np.argmax(peaks))
threshold = 0.5  # 应由正例/空 occasion 负例标定
detected = peaks[candidate] >= threshold
event = {
    "candidate_index": candidate,
    "sample_offset0": offsets[candidate],
    "peak": peaks[candidate],
    "state": "MSG1_DETECTED" if detected else "NO_DETECTION",
    "association_state": "candidate_only",
}

# 这些字段应来自独立的 RAR/Msg3/Msg4 解码和协议校验。
evidence = {"rar_rapid_matched": False, "msg3_observed": False,
            "msg4_resolved": False}
if detected and all(evidence.values()):
    event["association_state"] = "C_RNTI_CONFIRMED"
print(event)
```

这里的 `candidateIndex` 只是模板数组下标，必须通过配置映射到真实 `preamble_index`。匹配峰仅证明候选参考相关，不证明一个 occasion 内用户数，也不单独提供 C-RNTI；P3 碰撞和 P4 RA 关联仍需独立正负例与完整配置。

Python 示例依赖 NumPy；MATLAB 示例使用基础数组/卷积函数，但序列仍是教学级模板，不是完整 NR PRACH 波形。

## 10. 可复现记录

- MATLAB/5G Toolbox 版本：
- 代码提交号：
- 运行主机和天线/采样设置：
- 随机种子：
- PRACH 配置文件：
- 中心频率/带宽确认记录：
- 噪声、CFO、时钟偏差和滤波器定义：
- 原始相关轨迹路径：
- 结果表路径：

## 证据与出处

- `STANDARD + partial`：[[3GPP TS 38.211｜Physical channels and modulation]]、[[3GPP TS 38.213｜Physical layer procedures for control]]；具体 Release 表和 PRACH 数值需锁定。
- `STANDARD + partial`：外部 [ETSI TS 38.211 V17.7.0](https://www.etsi.org/deliver/etsi_ts/138200_138299/138211/17.07.00_60/ts_138211v170700p.pdf) 与 [ETSI TS 38.321 V16.21.0](https://www.etsi.org/deliver/etsi_ts/138300_138399/138321/16.21.00_60/ts_138321v162100p.pdf)；版本混用只用于导航，正式实验需统一版本。
- `PERSONAL_NOTE`：[[02 参考信号与导频设计#2.8 PRACH 前导与信道估计的区别]]、[[NR PRACH 检测与 RA-RNTI-C-RNTI 关联]]。
- `NEEDS_EXTERNAL_REFERENCE`：MathWorks 官方 PRACH 检测/波形页面，访问日期 2026-09-04；API 仍需本机版本核验。

## 当前状态

尚未运行。完成 P0 后再把本页 `status` 从 `seed` 更新为带运行证据的状态；在此之前不得填写虚构的 $P_D$、TOA RMSE 或 C-RNTI 成功率。
