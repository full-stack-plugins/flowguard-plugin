# 旧 FlowGuard 状态快照

> **文档说明**：保留本仓从旧 `.flowguard/` 迁移前的状态和审计记录，供逐项核对；不是当前流程事实源。
> **版本**：v1.0
> **最后更新**：2026-09-23

## 1. 迁移说明

旧目录中的 10 份阶段文档已复制到 `docs/project/` 和 `docs/features/journal-restore/`。原始 `project.json`、`features/journal-restore/state.json`、`journal/events.jsonl` 及配置原样归档在此，避免迁移时丢失旧审计信息。

当前项目不应把这里的旧状态当作可继续推进的状态机；阶段状态以 `docs/` 中的新文档为准。迁移后旧验收不自动继承，须重新核对。

旧 `journal-restore` 的五个跳过用例原样归档为 `test_recover.py`，它们要求重建已废弃的 `.flowguard/project.json` 和 `state.json`，不属于现行十阶段验收。现行恢复行为由 `tests/test_docs_pipeline.py` 的缓存丢失/SessionStart 恢复测试与 `tests/test_docs_migration.py` 的 dry-run、冲突保护测试验证；旧 journal 追加事件的要求不迁移为 `docs/` 流程要求。

---

**文档版本**：v1.0
**创建日期**：2026-09-23
**最后更新**：2026-09-23
**文档状态**：⏳ 历史归档
