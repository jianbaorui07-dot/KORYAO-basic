# WorldForge 任务格式说明

任务 JSON 必须声明 task_id、title、goal、map、mode、actor_limit、build_limit_per_step、quality_mode 和 checkpoint_required。

v0.1 只允许 preview_then_execute 模式。执行前必须生成文字计划、预计 Actor 数量和性能风险说明。执行时不得导入外部资产，不得删除非 WorldForge Actor。
