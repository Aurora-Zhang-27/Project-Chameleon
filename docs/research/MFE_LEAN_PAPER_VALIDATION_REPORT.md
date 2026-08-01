# MFE v3 轻量完整二进制实验报告

日期：2026-08-01

状态：**完成；作为当前本地数值主结果，取代 v4 partial-integrality 路线。**

## 1. 技术摘要

Project Chameleon 现在采用一套保留完整 24 小时物理结构、但减少重复求解规模的 MFE v3 实验。新设计不删除充放电模式变量，不使用连续松弛，也不依赖 v4 的 adaptive partial-integrality certificate。它只减少参数格点、construction scenarios、held-out paths 和合同变体。

六个代表性 PV+BESS 格点全部完成 full-binary `C_full-32` 求解。完整模型求解时间为 2.19-60.10 秒，六个格点合计 113.94 秒。32 条 construction paths 和 768 条 held-out line-path records 均通过独立物理 replay 与成本对账，没有 unresolved stage-2 solve。

在每个格点 32 条共同 held-out paths 上，recourse-aware intertemporal `C1` 相比 `C_ASSOC` market proxy 降低 10.66%-13.94% 的平均 realized cost；六个 paired 95% 描述性区间均排除零。`C1` 的平均成本仅比 full-binary `C_full-32` 高 1.06%-2.55%，说明保留跨期能量与真实 recourse 信息已经回收了大部分可测信息价值。

安全结论是：

> v3 的计算障碍来自 384-scenario extensive form 的重复规模，而不是完整 binary truth model 本身。把 construction scenarios 降至 32、把网格降至 6 cells 后，可以在本机保留完整物理模型并得到稳定、可 replay 的合同比较；没有必要把 v4 松弛作为主实验路线。

## 2. 为什么覆盖原来的 lean 主结果

原 2026-07-30 lean 实验使用 6 cells、64 held-out paths 和四条线：`C0-fixture`、`C1`、`C_ASSOC`、`C_WS`。它证明了 `C1` 相比市场 proxy 的经济方向，但没有在每个格点重建 full-binary `C_full-32`，因此主要使用 pathwise wait-and-see `C_WS` 作为信息边界。

随后完成的本地诊断表明：

1. 32-scenario full-binary MILP 在 2h 和 4h 格点通常只需 2-5 秒；
2. 最困难的 1h 格点也能在约 40-60 秒内达到 0.1% 以内的 relative gap；
3. 所有 construction decisions 都能在完整物理模型中 replay；
4. 因而本地实验可以直接保留完整 mode binaries，无需使用 v4 的部分松弛作为核心证据。

旧 lean 结果和 v4 counterexample 仍作为研究过程与负结果保留：v4 继续证明“直接删除 mode binaries 并不安全”，但不再承担最终主实验的求解任务。

## 3. 当前实验问题

本实验回答：

> 当 horizon、损耗、互斥模式、弃光、火电与电池 recourse、备用激活和 terminal SOC 全部保留时，减少信息的合同相对 full-binary stochastic construction 会付出多少 held-out realized cost？

比较对象为：

| 合同线 | 含义 |
|---|---|
| `C0-fixture` | 静态参数 `(15,35,35,50)`，不做 per-cell refit |
| `C1` | recourse-aware 1/99 intertemporal inner envelope |
| `C_ASSOC` | CAISO-style SOC rule market proxy |
| `C_full-32` | 32 条 construction scenarios 上求解的完整 binary nonanticipative extensive form |

`C_full-32` 不是提前知道 held-out path 的 wait-and-see 解。它在 construction sample 上选择一个共同 stage-1 决策，再在未见的 paired held-out paths 上使用与其他合同相同的真实 stage-2 optimizer。

## 4. 实验设计

| 项目 | 当前冻结选择 |
|---|---|
| 资源 | one PV+BESS，四台火电机组，单节点 |
| 数据 | RTS-GMLC 公开可复现合成 benchmark，不是 observed CAISO data |
| horizon | 24 小时 |
| storage duration | 1h、2h、4h |
| reserve requirement | 5%、20% |
| initial SOC | 固定 50% |
| PV error scale | 固定 `sigma=0.08` |
| cells | 6 |
| construction scenarios | 每格 32 条 |
| construction seed | `2026080101` |
| held-out paths | 每格 32 条共同 paired paths |
| held-out seed | `2026080104` |
| contract lines | 4 |
| full-model gap | 0.1% |
| full-model time limit | 每格 120 秒 |
| execution | one process、one numerical thread |

轻量化发生在重复数量上，不发生在物理结构上。保留：

- lossy bidirectional battery；
- charge/discharge mode binaries；
- PV curtailment；
- battery and thermal redispatch；
- imbalance settlement；
- isolated up/down activation branches；
- reserve shortfall、load shedding 与 spill；
- terminal SOC；
- construction scenarios 共享的 nonanticipative stage-1 decision。

## 5. 样本、指标与比较基准

每个 cell 的 held-out 样本为 32 条共同 PV paths。每条 path 上，四条合同使用同一个实际 PV realization 和同一个真实 stage-2 physical recourse model。

主要指标是：

1. `realized_cost_usd`：固定合同 stage-1 后，在 held-out path 上执行真实 recourse 的总成本；
2. paired cost difference：同一 cell、同一 path 上两条合同的 realized cost 差；
3. gap to `C_full-32`：合同平均 realized cost 相对 full-binary benchmark 均值的百分比差；
4. physical replay validity：序列化结果是否满足独立重算的物理恒等式、SOC 与互斥要求；
5. cost reconciliation：序列化成本与独立重算成本是否一致。

95% 区间使用 32 个 paired differences 的正态近似：

$$
mean(diff) plus/minus 1.96 times sd(diff) / sqrt(32).
$$

这些是当前 32 条注册路径的描述性不确定性区间，不是 CAISO 总体推断，也不是因果效应。

## 6. 完整 binary 模型可以在本机运行

| Duration | Reserve | `C_full-32` solve time | Relative gap | Construction replay |
|---:|---:|---:|---:|---:|
| 1h | 5% | 60.10 s | 0.0014% | 32/32 |
| 1h | 20% | 40.10 s | 0.00002% | 32/32 |
| 2h | 5% | 3.96 s | 0.0392% | 32/32 |
| 2h | 20% | 2.90 s | 0.0026% | 32/32 |
| 4h | 5% | 4.69 s | 0.0131% | 32/32 |
| 4h | 20% | 2.19 s | approximately 0% | 32/32 |

全部六个格点都满足注册的 0.1% gap 要求。短时 1h 电池的整数模式证明更困难，但仍在 120 秒限制内完成。

因此原 v3 结论应修订为：

> 384 scenarios 在本机计算预算内 unresolved；32 scenarios 的完整 binary v3 extensive form 可稳定完成。

## 7. 数据完整性与物理验证

执行规模为：

$$
6 cells x 32 held-out paths x 4 lines = 768 records.
$$

| 检查 | 结果 |
|---|---:|
| duplicate `(cell,path,line)` keys | 0 |
| incomplete four-line pairs | 0 |
| unexpected cell-line counts | 0 |
| construction physical replay failures | 0 |
| construction cost-reconciliation failures | 0 |
| held-out physical replay failures | 0 |
| held-out cost-reconciliation failures | 0 |
| held-out stage-2 unresolved | 0 |

因此成本差异不是由不可 replay 的内部轨迹、未解决模型或成本序列化错误造成的。

## 8. `C1` 在六个格点都优于 `C_ASSOC`

负数表示 `C1` 更便宜。

| Duration | Reserve | Mean `C1-C_ASSOC` | Paired 95% interval | Relative to `C_ASSOC` |
|---:|---:|---:|---:|---:|
| 1h | 5% | -$25,501 | [-$43,359, -$7,643] | -11.32% |
| 1h | 20% | -$34,192 | [-$51,580, -$16,805] | -13.94% |
| 2h | 5% | -$23,753 | [-$41,676, -$5,830] | -10.66% |
| 2h | 20% | -$33,253 | [-$49,771, -$16,735] | -13.57% |
| 4h | 5% | -$23,993 | [-$41,853, -$6,133] | -10.80% |
| 4h | 20% | -$31,916 | [-$46,863, -$16,969] | -13.05% |

六个区间全部排除零，且高备用格点的成本差普遍更大。这与理论机制一致：备用压力越高，忽略跨期能量与 recourse 结构的市场 proxy 越容易产生昂贵的后续修复。

这支持：

> 在当前 24 小时合成 benchmark 与 32 条 paired held-out paths 中，`C1` 的跨期信息具有稳定的描述性经济价值。

它不支持：

> 真实 CAISO 采用同一合同一定节省 10.66%-13.94%。

## 9. `C1` 已接近 full-binary benchmark

| Duration | Reserve | Mean `C1-C_full-32` | Paired 95% interval | Relative to `C_full-32` |
|---:|---:|---:|---:|---:|
| 1h | 5% | $2,104 | [-$296, $4,503] | 1.06% |
| 1h | 20% | $2,266 | [$511, $4,021] | 1.09% |
| 2h | 5% | $2,192 | [-$970, $5,355] | 1.11% |
| 2h | 20% | $3,648 | [$1,330, $5,965] | 1.75% |
| 4h | 5% | $2,113 | [-$1,142, $5,367] | 1.08% |
| 4h | 20% | $5,280 | [$3,473, $7,088] | 2.55% |

三个低压力或较低辨识度格点的 paired interval 包含零，因此不能宣称 `C_full-32` 在每个 cell 都统计上优于 `C1`。但均值方向一致，且差距远小于 `C_ASSOC` 相对 full-binary benchmark 的 13.17%-17.94%。

[[FIGURE: results/mfe_v3_lightweight_full_binary/figures/full_binary_frontier.png]]

图 1. 六个代表性格点相对 full-binary `C_full-32` 的平均 realized-cost gap。每格 32 条 paired held-out paths；图中是描述性均值。`C1` 在所有格点都最接近 full-binary benchmark。

## 10. v4 的最终定位

v4 的连续松弛反例仍然成立并应保留：

- full physical MILP：$201,327.897881；
- all-mode relaxed LP：$201,322.091094；
- 最大同时充放电：10.625 MW；
- 固定 relaxed stage-1 后恢复真实物理 recourse：$204,203.165340。

这个结果证明删除 mode binaries 会制造虚假灵活性。但新实验进一步证明，在 32 construction scenarios 和 6 cells 的范围内，没有必要用 partial integrality 才能运行完整模型。

因此 v4 的角色调整为：

1. 理论与数值负结果：连续松弛不 exact；
2. 可选的大规模求解加速研究；
3. 不再作为当前主实验的求解基础。

## 11. 结论与下一步

当前主实验支持三项结论：

1. **完整物理可以保留。** 轻量化应优先减少场景、cells 和合同拟合次数，而不是删除物理模式变量。
2. **`C1` 的价值稳定。** 它在六个格点都比 `C_ASSOC` 便宜 10.66%-13.94%，且没有物理 replay 失败。
3. **仍存在剩余信息价值。** `C1` 距 `C_full-32` 还有 1.06%-2.55% 的平均差距，但已回收大部分市场 proxy 损失。

如果未来需要 powered market inference，应在服务器或实验室环境中扩大：

- held-out paths；
- initial SOC 与 PV sigma；
- network、unit commitment 与更多资源；
- 多个独立 construction seeds。

在此之前，当前 6-cell full-binary 实验足以作为 theory-paper mechanism validation，不应外推为真实市场效果。

## 12. 可复现文件

- 执行器：`src/chameleon/mfe_v3_lightweight.py`
- 分析器：`src/chameleon/mfe_v3_lightweight_analysis.py`
- 原始 cell JSON：`results/mfe_v3_lightweight_full_binary/v3full_*.json`
- 格点汇总：`results/mfe_v3_lightweight_full_binary/regime_summary.csv`
- 配对统计：`results/mfe_v3_lightweight_full_binary/paired_statistics.csv`
- 验证摘要：`results/mfe_v3_lightweight_full_binary/validation_summary.json`
- 主图：`results/mfe_v3_lightweight_full_binary/figures/full_binary_frontier.png`

最终回归状态：**79 tests passed。**
