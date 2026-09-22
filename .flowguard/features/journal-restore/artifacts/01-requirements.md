<!-- 元信息 -->
<!-- artifact: 01-requirements | feature: journal-restore | modules: scripts -->
# journal-restore 需求分析文档

> **文档说明**：需求分析阶段产出物，明确功能需求、用户故事与可验收标准；不涉及技术实现细节。
>
> **版本**：V1.0.0
> **最后更新**：{{DATE}}
>
> 注：`{{...}}` 为跨文档占位符；含占位符的块不参与机械校验。

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

## 2. 需求范围 (Scope)

### 2.1 功能目标

让使用者在状态文件损坏或丢失时，凭 journal 审计流自助恢复，消除「只能人肉重建」的灾难恢复缺口（roadmap Phase 2 欠账）。

### 2.2 边界（包含 / 不包含）

| 包含 | 不包含 |
| :--- | :--- |
| 由 journal/events.jsonl 重建 project.json 与 features/*/state.json | journal 本身的修复 / 重写 |
| 冲突保护（默认拒绝覆盖）与恢复留痕 | 跨仓 / 跨项目恢复 |
| dry-run 预检 | 产物 markdown 的恢复（非状态） |

---

## 3. 用户故事与验收标准 (Requirements)

### Requirement: 状态重建
`journal-restore/REQ-1` 用户 SHALL 能从 `.flowguard/journal/events.jsonl` 重建全部状态文件（project.json 与 features/*/state.json）。

#### Scenario: 全量丢失后重建
- **WHEN** 状态文件全部被删除且 journal 完整
- **THEN** `flowguard_state.py recover` 重建出与丢失前一致的状态（阶段状态、功能状态、current_feature）

#### Scenario: 部分缺失重建
- **WHEN** 仅部分状态文件丢失（如仅某个功能的 state.json）
- **THEN** 重建缺失部分，保留完好的文件不动，报告重建清单

### Requirement: 安全与留痕
`journal-restore/REQ-2` 恢复过程 SHALL 不静默覆盖既有状态，并 SHALL 留痕。

#### Scenario: 冲突保护
- **WHEN** 目标状态文件已存在且与重建结果不同
- **THEN** 默认拒绝写入该文件并在报告中列出，除非显式传 `--force`

#### Scenario: 恢复留痕
- **WHEN** 重建执行完毕（含 `--force` 覆盖）
- **THEN** journal 追加 `recover` 事件（含重建文件清单与覆盖标记）

### Requirement: 可预检
`journal-restore/REQ-3` 用户 SHALL 能以 dry-run 预览恢复结果而不落盘。

#### Scenario: 预检报告
- **WHEN** 传入 `--dry-run`
- **THEN** 输出将重建的文件、将跳过的文件与无法恢复的缺失信息，且磁盘状态零变化

---

## 4. 验收标准汇总 (Acceptance)

- TC-1 ~ TC-5（见 04-testcases 追溯矩阵）覆盖 REQ-1 / REQ-2 / REQ-3，且测试文件 `tests/test_recover.py` 存在；
- validate 对本功能零 ERROR。

---

**文档版本**：V1.0.0
**创建日期**：{{DATE}}
**最后更新**：{{DATE}}
**文档状态**：✅ 待评审
