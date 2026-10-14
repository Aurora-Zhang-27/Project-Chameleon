# Project Chameleon — causal storage deliverability

最小运行包与阶段性研究成果（2026-10-14）。研究已在当前范围收束，未解决的问题保留为开放问题。

Given heterogeneous lossless storage devices and an interval of aggregate power requests at each period, decide whether an initial energy state admits a causal policy that fulfils every allowed request sequence. This package contains exact recursions for proven regimes, rational counterexample certificates, and a certified affine-policy inner test.

## 模型与结论

电量 e_i∈[0,E_i]，功率 p_i∈[−C_i,D_i]，e⁺=e−p，Σp_i=y_t∈[l_t,u_t]。动作可看当前与过去调用，不可看未来。无损、允许设备间交叉充电；每段时长已吸收入功率界。互斥、有损模型不在结论范围内。

| 情形 | 结论 |
|---|---|
| N≤3，参数任意 | 精确有理数递推；最多 14 个子集界，算术次数 O(T)；已独立复核 |
| 同一型号，任意 m、任意初态 | 精确 2m 个排序部分和界，O(mT)；已独立复核 |
| C_i≥E_i 且 D_i≥E_i | 总电量区间精确递推，O(T) |
| ≤3 个成比例且组内同比例电量的组 | 合成后用 N≤3 递推；充分条件 |
| 一般异构 N≥4 | 子集界及 {0,±1} 模板不总是精确；含两类反例和系数 2 面的有理数证书 |
| 历史相关、按正负部提升的仿射策略 | LP 规模 O(NT²)；认证接受安全，拒绝仅说明策略类失败；有精确失败证书 |

面方向增长、一般异构精确判定的多项式复杂度仍开放。文献新意仅指已核对来源中未找到先例；仿射方法与同类车队的拉平最优策略本身是已知结果。

## 安装与最小运行

Python 3.9+（固定版本复现建议使用 Python 3.9–3.12；更高版本可安装 requirements.txt 的兼容版本）。只需 NumPy、SciPy，无求解器许可证、绘图依赖或外部数据。

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-reproduce.txt
python run.py --demo
python run.py --input examples/affine.json --requests 0 1/10
```

输入字段是 `E`、`C`、`D`、`initial`、`intervals`。非终止小数建议用 JSON 字符串 `"1/3"`，保留有理数语义。

成比例分组需先按命题 5 合成为至多 3 台虚拟设备，再将虚拟参数送入入口；本包不自动搜索分组。

返回值：

- `feasible`：精确递推，或取得经过逐条有理数核对的策略/树见证。
- `infeasible`：物理盒、精确必要条件、精确递推，或已认证模板界排除。
- `unknown`：仿射 rejected/float_only，不代表原问题不可行。
- `infeasible_float`：可选请求树报不可行且关闭 presolve 重解仍不可行，但未生成有理数 Farkas 证书。

一般异构入口先检查精确聚合必要条件，再找仿射策略。可选更强的外包与兜底：

```bash
python run.py --input examples/affine_gap.json --template
python run.py --input examples/affine_gap.json --tree
```

`--template` 使用全部 0/±1 方向，并核对每个 LP 的有理数原始—对偶证书，限 N≤6；方向枚举随 N 指数增长。`--tree` 仅在待定时使用端点请求树，限 T≤12，随 T 指数增长。树见证是共享历史的端点策略；没有直接作为区间内任意调用的控制器返回。

API：`from chameleon_runtime import decide`，`result, policy = decide(data)`。有可执行策略时 `policy.power(observed_history)` 返回精确分数功率。仿射返回的是通过认证的修复系数，`policy.as_dict()` 可序列化；不会把原始浮点解当成认证策略交付。

## 复现与必要结果

```bash
python -m unittest discover -s tests -v
python verify_release.py
```

验证包含 N2/N3/同类算法、主要反例的零功率和正功率版本、仿射缺口及接口边界。输出见 [results](results/README.md)。发布验证记录明确区分精确证书与浮点对照。

历史夹逼样本共 211,063 个：树 LP 浮点判定 211,060 个可兑现，210,959 个取得分段仿射有理数认证，101 个仅浮点接受，另有 3 个仿射拒绝。严格流程仍有 104 个点需其他方法处理，约 0.049%；不是零兜底，也不是一般接受率保证。这些是发布前版本的历史汇总，本次未重跑全部样本。

只保存聚合结果、来源哈希和本次证书日志，不提交个人材料、论文全文、大批搜索记录。

## 阅读入口

1. [研究报告](RESEARCH_REPORT_ZH.md)：问题、阶段成果和开放问题。
2. [证明、实验与独立复核](complexity_20260925/README.md)。
3. [旧版历史入口与精简范围](ARCHIVE.md)。旧 MFE 冻结资料可在原提交和归档标签查看，本机完整研究目录未改动。
