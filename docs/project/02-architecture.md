<!-- 元信息 -->
<!-- artifact: 02-architecture | feature: project | modules: - -->
# flowguard-plugin 架构设计文档

> **文档说明**：项目级架构设计产出物，记录选型、ADR 决策与模块边界；ADR 追加式维护。
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
| 阶段 | 02-architecture |
| 阶段状态 | in_progress |
| 规格事实源 | none |
| 原生产物 | - |
| 批准依据 | 待复核；旧状态 in_progress |
| 验收指纹 | - |

| 迁移来源 | .flowguard/project/02-architecture.md |

## 2. 选型 (Technology Choices)

| 维度 | 选型 | 理由 |
| :--- | :--- | :--- |
| 架构主体 | 四层（入口与门禁 / 编排技能 / 执行素材 / 编排核）+ 三级（项目 / 功能 / 模块） | 已定，见 docs/architecture.md |
| 本迭代约束 | 状态文件为唯一真相源，journal 为 append-only 审计流 | 灾难恢复与防篡改审计 |

---

## 3. ADR 列表 (Architecture Decisions)

> 追加式：禁止改写既有条目；新增条目带 `feature: <来源功能>` 标注。

- ADR-001 | feature: project | 状态: accepted —— 状态文件（project.json / state.json）是唯一真相源，journal/events.jsonl 是 append-only 审计流；二者构成「状态 + 事件」对，任何状态都可由事件流重放验证。
  - 背景：灾难恢复与防篡改审计；备选：周期快照（弃：引入第二份真相）；后果：恢复 = 事件重放。
- ADR-002 | feature: journal-restore | 状态: proposed —— 恢复工具采用**事件重放**而非快照恢复：`recover` 读取 journal 重放已知事件形状重建状态；不新增任何存储文件。
  - 背景：ADR-001 已确立 journal 为审计流；备选：定期状态快照（弃，见 ADR-001）；后果：journal 事件形状成为稳定契约，未知形状降级为 warning（**推断**：老事件兼容成本可控，待 Phase 3 复核）。

---

## 4. 模块边界 (Module Boundaries)

| 模块 | 职责 | 依赖方向 |
| :--- | :--- | :--- |
| `scripts/flowguard_lib/recover.py`（新增） | 事件重放引擎，与 `journal.py`（写侧）对偶 | 依赖 journal / state |
| `scripts/flowguard_lib/state.py` | 唯一写入口（`_atomic_write`），recover 只经它落盘 | 被 recover / CLI 依赖 |
| `scripts/flowguard_state.py` | 新增薄壳子命令 `recover` | 依赖 recover |

---

**文档版本**：V1.0.0
**创建日期**：{{DATE}}
**最后更新**：{{DATE}}
**文档状态**：✅ 待评审
