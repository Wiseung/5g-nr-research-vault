# 关键结果导出

范围、模型、数据预算及执行限制见 [实验入口](../../GITHUB_EXPERIMENTS.md)。

- `training.csv`：24次完整50k训练的摘要，seed17/29/43全部保留。
- `thresholds.csv`：各cohort的方法门限、相对NMS收益及固定模型的配对95%区间。
- `test_points.csv`：每点帧数、错误数、BLER、拒收及BCE；不能跨cohort累加相同信道观测的分母。
- `selected_models.json`：24个验证集选定模型的原始身份、SHA256及仓库相对路径。
- `files.sha256.json`：本次白名单文件哈希，不含自身；不是完整原始数据清单。
- `scope.json`：原始commit、已完成范围、公开与本机留存材料、绝对路径说明。

运行 `python3 -B verify_export.py` 校验本交付；标准库即可。选定checkpoint包含原始模型与优化器状态；原始PT/JSON未改写。全部逐帧数据仍在服务器，不能从摘要恢复逐帧差异或重算所有统计检验。
