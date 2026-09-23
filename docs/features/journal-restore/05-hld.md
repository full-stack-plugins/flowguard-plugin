<!-- 元信息 -->
<!-- artifact: 05-hld | feature: journal-restore | modules: scripts -->
# journal-restore 概要设计文档

> **文档说明**：概要设计阶段产出物，明确模块 / 服务划分、交互与非功能约束。
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
| 阶段 | 05-hld |
| 阶段状态 | invalidated |
| 规格事实源 | none |
| 原生产物 | - |
| 批准依据 | 待复核；旧状态 in_progress |
| 验收指纹 | - |

| 迁移来源 | .flowguard/features/journal-restore/artifacts/05-hld.md |

## 2. 模块 / 服务划分 (Components)

| 单元 | 职责 |
| :--- | :--- |
| `journal.py`（既有） | 事件读取（`read`），写侧不动 |
| `recover.py`（新增） | 重放引擎：事件 → 内存状态；现状对比；冲突策略；报告 |
| `state.py`（既有） | 唯一落盘入口（`_atomic_write`）与锁（`state_lock`） |
| `flowguard_state.py::cmd_recover`（新增） | 薄壳：参数 → rebuild → 诊断信封 / 报告输出 |

---

## 3. 交互 (Interactions)

```text
journal/events.jsonl ──read──▶ 事件序列 ──_replay──▶ 内存 (project, features)
                                                  │
                            现状（磁盘状态文件）───┤ 对比
                                                  ▼
                          RebuildReport ──（非 dry-run 且不冲突）──▶ state._atomic_write
```

---

## 4. 非功能约束 (Non-functional)

- 只读 `journal/`，只写 `.flowguard/` 状态文件；不触业务代码与产物 markdown；
- 失败安全：任何异常不落盘（先算后写）；全程持 `state_lock`；
- 纯标准库，与编排核同栈。

---

**文档版本**：V1.0.0
**创建日期**：{{DATE}}
**最后更新**：{{DATE}}
**文档状态**：✅ 待评审
