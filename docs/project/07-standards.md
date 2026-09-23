<!-- 元信息 -->
<!-- artifact: 07-standards | feature: project | modules: scripts,hooks -->
# flowguard-plugin 编码规范文档

> **文档说明**：项目级编码规范集，按模块栈选型；增补一律追加式并标注来源。
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
| 任务 | project |
| 父任务 | - |
| 阶段 | 07-standards |
| 阶段状态 | in_progress |
| 规格事实源 | none |
| 原生产物 | - |
| 批准依据 | 待复核；旧状态 in_progress |
| 验收指纹 | - |

| 迁移来源 | .flowguard/project/07-standards.md |

## 2. 规范集 (Standards)

### 2.1 Python（scripts/、hooks/）

- 仅标准库；签名与 03-solution 接口契约一致；
- 错误输出一律诊断信封 `{severity, code, message, fix}`（`flowguard_lib.diag`），禁止裸 raise 到 CLI 边界；
- 测试 `python3 -m unittest discover -s tests`，禁止 pytest；测试文件放 `tests/`；
- 状态文件读写只经 `flowguard_lib.state`；journal 追加只经 `flowguard_lib.journal`；
- SKILL.md 是生成物：改 `scripts/templates/` 模板后跑 `generate_skills.py`。

### 2.2 通用（AGENTS.md 三纪律）

- 编排核单一判定源；accepted 只能用户写入；文档与 commit 中文；
- 文档格式以 full-stack-doc v3.0 为基础（docs/FLOWGUARD_ARTIFACT_SPEC.md §0）。

---

## 3. 项目级增补记录 (Amendments)

> 追加式：禁止改写既有条目；标注来源功能。

<!-- feature: journal-restore -->
- 恢复类工具必须 **dry-run 优先**；默认拒绝覆盖既有内容，覆盖必须显式 `--force` 且留痕（REQ-2 / REQ-3 的规范投影）。

---

**文档版本**：V1.0.0
**创建日期**：{{DATE}}
**最后更新**：{{DATE}}
**文档状态**：✅ 待评审
