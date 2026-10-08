---
title: 仿真：C-RNTI 驱动的 PDCCH-PDSCH 盲搜
aliases:
  - 仿真 NR PDCCH 盲检测
  - 仿真 C-RNTI 到 PDSCH 解码
type: experiment
status: seed
created: 2026-09-04
tags:
  - domain/5g-nr
  - channel/pdcch
  - channel/pdsch
  - channel/pusch
  - topic/定位
  - stage/simulation
  - stage/verification
  - metric/detection
  - metric/bler
  - evidence/3gpp
source:
  - 3GPP TS 38.211
  - 3GPP TS 38.212
  - 3GPP TS 38.213
  - 3GPP TS 38.214
  - NR-DCI 编码链
simulation:
  - 仿真：C-RNTI 驱动的 PDCCH-PDSCH 盲搜
related:
  - "[[NR PDCCH 盲搜与 PDSCH-PUSCH 资源解析]]"
  - "[[NR PRACH 检测与 RA-RNTI-C-RNTI 关联]]"
  - "[[单用户时频截取与定位观测量]]"
  - "[[仿真-无噪声编解码闭环]]"
---

# 仿真：C-RNTI 驱动的 PDCCH-PDSCH 盲搜

> [!abstract] 实验性质
> 本页是 `EXPERIMENT + NEEDS_VERIFICATION` 设计模板。先在已知 C-RNTI、已知 CORESET/搜索空间和单个 DCI 候选下闭环，再逐步放宽到有限 RNTI 候选池；不把“盲搜所有 C-RNTI”当作默认实时方案。

## 1. 实验目标

1. 验证 PDCCH 候选资源、DM-RS、LLR、Polar/CRC 和 RNTI 掩码链路。
2. 验证有效 DCI 能否一致地产生 PDSCH/PUSCH 的 `resource_snapshot` 与 `coding_snapshot`。
3. 比较已知 RNTI、有限候选 RNTI 和错误 RNTI 下的检测率、误检率和候选级延迟。
4. 检查仅提取定位观测量与完整 PDSCH/PUSCH 译码两条输出是否可以独立工作。

## 2. 分层实验门

| 门 | 配置 | 核心验收 |
|---|---|---|
| C0 | 单时隙、已知 RNTI、无噪声 | 正确候选 CRC/字段通过，错误 RNTI 不通过 |
| C1 | AWGN、固定候选 | PDCCH BLER、漏检、误检和 LLR 质量可统计 |
| C2 | 多候选/多聚合等级 | 候选索引、资源解映射和尾延迟正确 |
| C3 | 有效 DCI 驱动 PDSCH/PUSCH | PRB/符号/MCS/TBS/RV/DM-RS 资源命中 |
| C4 | 有限 RNTI 候选池 | 用户关联、字段合法性和跨时隙连续性判决 |
| C5 | 多用户/邻区/时变信道 | 单用户掩码、残余干扰和定位观测质量可解释 |

C0 通过前不运行大规模盲搜；C3 通过前不把 PDCCH CRC 结果送入定位链。

## 3. 前置配置账本

| 参数 | 内容 | 缺失处理 |
|---|---|---|
| 载波 | `NCellID`、SCS、带宽、BWP、FFT/CP | 标 `NEEDS_VERIFICATION` |
| 监测 | CORESET、搜索空间、周期、候选数、聚合等级 | 不用默认值静默补齐 |
| DCI | 格式、payload 长度、方向和 RNTI 假设 | 记录外层搜索范围 |
| PDCCH | DM-RS scrambling、资源索引、噪声方差 | 保留候选级快照 |
| PDSCH/PUSCH | PRB、符号、层、预编码、DM-RS/PTRS | 从 DCI/RRC 推导并校验 |
| 编码 | CRC、Polar/LDPC、率匹配、RV、TBS | 与 [[3GPP TS 38.212｜Multiplexing and channel coding]] 对齐 |
| 频率 | 用户提到的 `120.88 MHz` | 先确认是中心频率还是其他量 |
| 信道 | AWGN、TDL/CDL、CFO、时变和邻用户 | 一次只加一个因素 |

## 4. 已知 RNTI 的参考链

```text
生成/读取 carrier + BWP + CORESET + search-space
    ↓
枚举 monitoring occasion、聚合等级和 candidate
    ↓
提取 PDCCH RE 与 PDCCH DM-RS
    ↓
信道估计、均衡、软解调、解扰和逆率匹配
    ↓
Polar 译码 + C-RNTI CRC 掩码
    ↓
DCI 字段合法性
    ↓
生成 PDSCH/PUSCH resource_snapshot
    ↓
DM-RS 估计、均衡、解调、LDPC/TB-CRC（若执行完整数据链）
```

每一候选都保存 `candidate_state`；不要只保存最终 `dciCRC`。

## 5. 未知 C-RNTI 的候选策略

| 策略 | 候选来源 | 适合阶段 | 统计重点 |
|---|---|---|---|
| RA 驱动 | PRACH→RA-RNTI→RAR/Msg3/Msg4 关联 | 项目第一阶段之后 | 关联漏失和误关联 |
| 历史池 | 已确认 C-RNTI 的时间窗口缓存 | 连续监测 | C-RNTI 老化和重用 |
| 测试池 | 实验 UE 预置的有限值 | 单元/系统测试 | 正负例和误检 |
| 全空间 | 理论 16-bit RNTI 假设 | 仅复杂度上界 | 不作为实时默认 |

候选池必须记录来源、有效期和置信度。若只有 CRC 通过而没有 RA/时序/资源证据，状态保持 `candidate_only`。

## 6. MATLAB 官方示例映射

MathWorks 的 [Downlink Control Processing and Procedures](https://www.mathworks.com/help/5g/ug/downlink-control-processing-and-procedures.html) 展示了对每个聚合等级和候选循环，并使用 `nrPDCCHSpace`、`nrChannelEstimate`、`nrExtractResources`、`nrEqualizeMMSE`、`nrPDCCHDecode` 与 `nrDCIDecode` 完成候选级处理。该示例明确假设已知部分配置；未知 DCI 格式/长度需要外层搜索。

MathWorks 的 [DL-SCH and PDSCH Transmit and Receive Processing Chain](https://www.mathworks.com/help/5g/gs/dl-sch-and-pdsch-transmit-and-receive-processing-chain.html) 展示 `nrPDSCHDMRSIndices`、`nrPDSCHDMRS`、`nrPDSCHDecode` 和 `nrDLSCHDecoder` 的链路。

这些函数名和流程仅作外部 API 参考。运行前必须在本机固定 MATLAB/5G Toolbox 版本，检查对象属性、输入维度、RNTI 参数、数据类型和 OFDM 归一化；本页没有实际运行结果。

## 7. 资源命中与数据闭环

对 DCI 推导的目标资源 $\mathcal{R}_{DCI}$，比较发送端真值 $\mathcal{R}_{true}$ 与接收端解析集合 $\widehat{\mathcal{R}}$：

$$
\mathrm{resource\_recall}
=\frac{|\widehat{\mathcal{R}}\cap\mathcal{R}_{true}|}{|\mathcal{R}_{true}|},
\qquad
\mathrm{resource\_precision}
=\frac{|\widehat{\mathcal{R}}\cap\mathcal{R}_{true}|}{|\widehat{\mathcal{R}}|}.
$$

随后检查：

- PRB、OFDM 符号和 BWP 绝对坐标。
- DM-RS/PTRS/保留 RE 是否正确扣除且未重复扣除。
- MCS、TBS、层数、RV、HARQ 进程和扰码初始化。
- PDSCH/PUSCH 解调后的 LLR 符号、逆率匹配和 TB-CRC。
- 资源命中正确但 TB-CRC 失败时，能否区分 CSI/LLR/编码原因。

## 8. 定位支路与译码支路

```text
PDCCH/DCI 通过
    ├─ 定位支路：资源掩码 → 已知 DM-RS/参考片段 → ToA/RTOA/质量
    └─ 译码支路：完整 PDSCH/PUSCH → 软解调 → LDPC → TB-CRC
```

定位支路不必等待业务比特恢复，但必须保留 C-RNTI/资源/时序关联证据；译码支路可作为用户关联和质量校验。两支路的样点时间基准必须一致。

## 9. 指标与结果表

| 场景 | RNTI 策略 | 候选数 | PDCCH 检测率 | 错误候选误检率 | DCI 字段正确率 | 资源 precision/recall | PDSCH/PUSCH BLER | 候选延迟 | 定位支路状态 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| C0 | 已知 |  |  |  |  |  |  |  |  |
| C1 | 已知 |  |  |  |  |  |  |  |  |
| C2 | 已知 |  |  |  |  |  |  |  |  |
| C3 | 已知 |  |  |  |  |  |  |  |  |
| C4 | 有限池 |  |  |  |  |  |  |  |  |
| C5 | 有限池 |  |  |  |  |  |  |  |  |

## 10. 故障注入

| 注入 | 应定位到 |
|---|---|
| 错误 CORESET/搜索空间 | 资源解映射/监测配置 |
| 错误聚合等级或候选索引 | PDCCH RE/DM-RS 提取 |
| LLR 取反/噪声方差错 | 软解调/Polar 接口 |
| RNTI 掩码错 | CRC/RNTI 判决 |
| DCI 字段位序交换 | 字段合法性/格式解析 |
| K0/PRB/符号偏一 | DCI→PDSCH/PUSCH 资源映射 |
| DM-RS 端口/层错 | CSI/均衡 |
| RV/TBS 错 | 逆率匹配/LDPC/TB-CRC |
| 候选池放入未确认 RNTI | 用户关联/误检控制 |

## 11. 可复现记录

- MATLAB/5G Toolbox 版本：
- 代码提交号：
- carrier/BWP/CORESET/search-space 配置文件：
- DCI 格式和字段定义：
- RNTI 候选来源与有效期：
- FFT、CP、采样率、归一化和噪声定义：
- 每候选原始 LLR/CRC/字段日志路径：
- resource_snapshot/coding_snapshot 路径：
- 结果表和停止规则：

## 12. 伪代码与 MATLAB/Python 候选门控示例

下面的代码验证 C0/C3 的账本判决和资源掩码接口，不执行 PDCCH 解扰、Polar/CRC、DCI 位域解析或 PDSCH LDPC。`candidateResults` 必须由本机版本固定的 5G Toolbox 或项目 PHY 解码适配器产生；简化脚本不能替代盲解链路。

### 伪代码

```text
从配置快照生成 monitoring occasion 和许可的候选 RNTI 集合
对每个候选执行 RE/DM-RS 提取、信道估计、均衡和软解调
对每个 RNTI 假设执行 PDCCH/Polar/CRC 判决
只有 RNTI 假设在许可集合内，且 CRC、DCI 字段、资源范围和时序连续性全部通过才接纳
将接纳的 DCI 解析为规范化 BWP 局部 grant
构造 allocated RE，再扣除 DM-RS/PTRS/reserved RE 得到 data RE
保存每候选输入、状态、延迟和资源快照；分别走定位与完整译码支路
```

### MATLAB

```matlab
% 下列候选结果是控制判决层的合成正/负例，不是 PHY 解码输出。
grant = struct("startPRB0", 4, "nPRB", 6, ...
    "startSymbol0", 2, "nSymbols", 10);
candidateResults = {
    struct("rnti", uint16(hex2dec('4601')), "crcPass", true, ...
        "rntiAllowed", true, "fieldValid", true, ...
        "resourceValid", true, ...
        "temporalConsistent", true, "grant", grant);
    struct("rnti", uint16(hex2dec('1234')), "crcPass", false, ...
        "rntiAllowed", false, "fieldValid", false, ...
        "resourceValid", true, ...
        "temporalConsistent", false, "grant", grant)
    };

accepted = false(numel(candidateResults), 1);
for k = 1:numel(candidateResults)
    q = candidateResults{k};
    accepted(k) = q.rntiAllowed && q.crcPass && q.fieldValid && ...
        q.resourceValid && q.temporalConsistent;
end
validIndex = find(accepted);

if ~isempty(validIndex)
    nPRB = 24;
    nSymbols = 14; % 仅为普通 CP 的合成资源网格示例；实测读取配置
    nSC = 12 * nPRB;
    q = candidateResults{validIndex(1)};
    g = q.grant; % 已由 DCI parser 转换成 BWP 局部、0-based grant
    sc = 12 * g.startPRB0 + (1:12 * g.nPRB);
    sym = g.startSymbol0 + (1:g.nSymbols);
    assert(sc(1) >= 1 && sc(end) <= nSC && ...
        sym(1) >= 1 && sym(end) <= nSymbols);

    allocatedRE = false(nSC, nSymbols);
    allocatedRE(sc, sym) = true;
    dmrsMask = false(nSC, nSymbols);
    ptrsMask = false(nSC, nSymbols);
    reservedMask = false(nSC, nSymbols);
    % 仅为接口演示的合成掩码；实际掩码用配置和官方索引函数生成。
    dmrsMask(sc, [3, 10]) = true;
    dataRE = allocatedRE & ~dmrsMask & ~ptrsMask & ~reservedMask;
    fprintf("接纳候选数=%d，allocated RE=%d，data RE=%d\n", ...
        numel(validIndex), nnz(allocatedRE), nnz(dataRE));
else
    disp("没有候选通过完整接纳条件；不进入数据/定位支路");
end
```

### Python

```python
import numpy as np

# 合成的候选账本正/负例；真实账本由固定版本的 PHY decoder 输出。
grant = {"start_prb0": 4, "n_prb": 6,
         "start_symbol0": 2, "n_symbols": 10}
candidates = [
    {"rnti": 0x4601, "rnti_allowed": True, "crc_pass": True, "field_valid": True,
     "resource_valid": True, "temporal_consistent": True, "grant": grant},
    {"rnti": 0x1234, "rnti_allowed": False, "crc_pass": False, "field_valid": False,
     "resource_valid": True, "temporal_consistent": False, "grant": grant},
]

accepted = [q for q in candidates if all((
    q["rnti_allowed"], q["crc_pass"], q["field_valid"], q["resource_valid"],
    q["temporal_consistent"],
))]

if accepted:
    n_prb, n_symbols = 24, 14  # 合成网格；实测读取 CP/numerology 配置
    n_sc = 12 * n_prb
    g = accepted[0]["grant"]  # BWP 局部、0-based 规范化 grant
    sc = np.arange(12 * g["start_prb0"],
                   12 * (g["start_prb0"] + g["n_prb"]))
    sym = np.arange(g["start_symbol0"],
                    g["start_symbol0"] + g["n_symbols"])
    if sc[-1] >= n_sc or sym[-1] >= n_symbols:
        raise ValueError("grant 超出当前 BWP/时隙范围")

    allocated = np.zeros((n_sc, n_symbols), dtype=bool)
    allocated[np.ix_(sc, sym)] = True
    dmrs = np.zeros_like(allocated)
    ptrs = np.zeros_like(allocated)
    reserved = np.zeros_like(allocated)
    # 合成掩码只演示接口；实际 DM-RS/PTRS 索引须由配置生成。
    dmrs[np.ix_(sc, np.array([2, 9]))] = True
    data_re = allocated & ~dmrs & ~ptrs & ~reserved
    print("accepted=", len(accepted), "allocated RE=", allocated.sum(),
          "data RE=", data_re.sum())
else:
    print("无候选通过完整接纳条件，不进入数据/定位支路")
```

Python 示例依赖 NumPy。两段示例中的 DM-RS 掩码是合成测试数据；真实 C3 需用 DCI 格式、BWP、DM-RS/PTRS 配置生成资源索引，并将译码器提供的候选状态、原始 LLR、字段合法性和 TB-CRC 结果写入实验账本。

## 证据与出处

- `PERSONAL_NOTE`：[[NR PDCCH 盲搜与 PDSCH-PUSCH 资源解析]]、[[NR-DCI 编码链]]、[[3GPP TS 38.213｜Physical layer procedures for control]]。
- `STANDARD + partial`：[[3GPP TS 38.211｜Physical channels and modulation]]、[[3GPP TS 38.212｜Multiplexing and channel coding]]、[[3GPP TS 38.214｜Physical layer procedures for data]]。
- `NEEDS_EXTERNAL_REFERENCE`：MathWorks PDCCH/PDSCH 官方示例，访问日期 2026-09-04；API 和 Release 需本机核验。
- `EXPERIMENT + NEEDS_VERIFICATION`：本页参数、指标和结果表是实验设计，不是已测结果。

## 当前状态

尚未运行。先完成 C0/C1，再评估有限 RNTI 池；没有有效 DCI 和资源快照时，不应声称完成 PDSCH/PUSCH 盲解。
