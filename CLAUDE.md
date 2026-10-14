# Project Chameleon 精简发布版

讨论用中文。先读 README.md 和 RESEARCH_REPORT_ZH.md。

模型为无损、允许交叉充电、无模式互斥的多设备因果区间兑现。保持证明、精确有理数证书、浮点证据和开放问题之间的区别。

已证明的精确情形：N≤3；单一类型任意台数；C_i≥E_i 且 D_i≥E_i；至多 3 个成比例且同比例电量的组。
一般异构情形的子集或 {0,±1} 模板并不精确。仿射策略 certified 才安全接受；float_only/rejected 均不能由内近似推出不可行。

研究已阶段性收束；本仓库只维护必要运行代码、资料与结果，不继续开放问题搜索。代码改动需运行 `python -m unittest discover -s tests -v` 与 `python verify_release.py`。不要下载或提交论文全文与个人材料。旧研究的 Git 历史入口见 ARCHIVE.md。
