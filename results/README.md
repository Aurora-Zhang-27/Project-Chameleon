# 保留的结果

- `affine_samples.csv`：8 个历史样本批次按 N 和功率菜单汇总，严格待定数为 samples − segregated_certified。
- `affine_scaling.csv`：历史耗时中位数。LP 求解、重新求解并认证、模型构建分别计时；长时段 mild 批次没有树 LP 对照。
- `vertex_summary.json`：分段仿射顶点筛查的汇总，浮点证据，不是逐顶点有理数证书。
- `provenance.json`：本机源提交及原始 JSON 文件 SHA256。原始数据不随精简包发布；复现样本生成脚本仍保留。
- `certificates.txt`、`release_checks.json`：本次发布工作区运行的精确证书、回归及入口检查记录。

历史计时依赖机器和软件版本；实验高接受率不是一般精确性证明。精确反例以证书脚本为准。

`affine_scaling.csv` 的 tree_feasible_float 空值表示未运行树 LP，不是没有可兑现初态。
