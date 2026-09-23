<!-- 元信息 -->
<!-- artifact: 04-testcases | feature: journal-restore | modules: scripts -->
# journal-restore 测试用例文档

> **文档说明**：测试用例阶段产出物，建立 REQ 与用例、测试文件的追溯矩阵（TDD 门槛依据）。
>
> **版本**：V1.0.0
> **最后更新**：{{DATE}}

---

## 1. 文档信息 (Document Info)

### 1.1 版本记录

| 版本号 | 修改日期 | 修改人 | 修改内容 | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| V1.0.0 | {{DATE}} | {{OWNER}} | 初始版本 | - |

### 1.2 文档责任人

| 角色 | 姓名 | 职责 |
| :--- | :--- | :--- |
| 责任人 | {{OWNER}} | 本阶段产出、自检与送验 |

---

### 1.3 FlowGuard 阶段信息

| 字段 | 值 |
|:---|:---|
| 任务 | journal-restore |
| 父任务 | - |
| 阶段 | 04-testcases |
| 阶段状态 | invalidated |
| 规格事实源 | none |
| 原生产物 | - |
| 批准依据 | 待复核；旧状态 in_progress |
| 验收指纹 | - |

| 迁移来源 | .flowguard/features/journal-restore/artifacts/04-testcases.md |

## 2. 测试范围 (Scope)

- 覆盖：REQ-1 重建正确性、REQ-2 冲突保护与留痕、REQ-3 dry-run 零落盘；
- 不覆盖：性能 / 压测、跨版本事件迁移（Phase 3）。

---

## 3. 用例与需求追溯矩阵 (Traceability)

### 用例 TC-1: 全量重建
- REQ: journal-restore/REQ-1
- 测试文件: docs/legacy-flowguard/test_recover.py
- 步骤: init + feature + next/advance 造出状态与 journal；删除全部状态文件；运行 rebuild
- 预期: rebuilt 含 project.json 与 feature state.json，内容与删除前一致

### 用例 TC-2: 部分重建
- REQ: journal-restore/REQ-1
- 测试文件: docs/legacy-flowguard/test_recover.py
- 步骤: 同 TC-1 造状态；仅删除一个功能的 state.json；运行 rebuild
- 预期: 仅重建缺失文件，完好的 project.json 未被改写

### 用例 TC-3: 冲突保护
- REQ: journal-restore/REQ-2
- 测试文件: docs/legacy-flowguard/test_recover.py
- 步骤: 删除状态文件后手工放入一个内容不同的 project.json；运行 rebuild（无 `--force`）
- 预期: 该文件列入 skipped（reason=conflict），未被覆盖；`--force` 时重建

### 用例 TC-4: 恢复留痕
- REQ: journal-restore/REQ-2
- 测试文件: docs/legacy-flowguard/test_recover.py
- 步骤: 任意一次成功 rebuild（含 `--force`）
- 预期: journal 末尾新增 recover 事件，detail 含 rebuilt 清单与 forced 标记

### 用例 TC-5: dry-run 预检
- REQ: journal-restore/REQ-3
- 测试文件: docs/legacy-flowguard/test_recover.py
- 步骤: 同 TC-1 场景，运行 rebuild(dry_run=True)
- 预期: 返回将重建清单但磁盘状态零变化（状态文件仍缺失）

---

## 4. 追溯说明 (Notes)

- **已确认：历史追溯，不是通过证据。** TC-1 ~ TC-5 的测试源已归档到 `docs/legacy-flowguard/test_recover.py`；旧 `.flowguard/` 状态恢复方案未实现，且被当前 `docs/` 事实源设计取代。现行恢复验收见 `tests/test_docs_pipeline.py` 与 `tests/test_docs_migration.py`。

---

**文档版本**：V1.0.0
**创建日期**：{{DATE}}
**最后更新**：{{DATE}}
**文档状态**：✅ 待评审
