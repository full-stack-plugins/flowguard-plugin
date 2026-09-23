<!-- 元信息 -->
<!-- artifact: 06-lld | feature: journal-restore | modules: scripts -->
# journal-restore 详细设计文档

> **文档说明**：详细设计阶段产出物，明确事件语义、函数明细与异常边界。
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
| 阶段 | 06-lld |
| 阶段状态 | invalidated |
| 规格事实源 | none |
| 原生产物 | - |
| 批准依据 | 待复核；旧状态 in_progress |
| 验收指纹 | - |

| 迁移来源 | .flowguard/features/journal-restore/artifacts/06-lld.md |

## 2. 事件重放语义表 (Event Semantics)

`_replay` 对已知事件的状态贡献（scope 由事件行 `scope` 字段决定：`project` / `feature:<id>`）：

| 事件 (event) | detail 关键字 | 状态贡献 |
| :--- | :--- | :--- |
| `init` | modules | 生成 project 骨架（3 个阶段级 pending、features 空、current_feature None） |
| `feature_new` | modules | features[id] = active；feature 骨架（7 阶段 pending、modules、title） |
| `next` | stage | scope 内该 stage → in_progress |
| `accepted_by_user` | stage | scope 内该 stage → accepted（accepted_at 取事件 ts） |
| `override` | stage, reason | scope 内该 stage → overridden + reason |
| `feature_done` / `feature_drop` | reason? | feature.status → done / dropped |
| `artifact_rework_degrade` | degraded[] | 列出的 stage → in_progress |
| `recover` | rebuilt, forced | 无状态贡献（自身留痕） |
| 未知 event | — | warnings 计 1 条，跳过 |

---

## 3. 函数明细 (APIs)

```python
def rebuild(root, *, dry_run=False, force=False) -> dict: ...   # 见 03-solution 接口契约
def _replay(events) -> tuple[dict, dict]: ...                    # (project, features)
def _classify_conflict(target: Path, rebuilt: dict) -> str: ...  # "absent"|"same"|"conflict"
```

- 目标文件分类：不存在 → rebuilt；内容相同（JSON 归一比较）→ skipped(unchanged)；不同 → `--force` ? rebuilt(forced) : skipped(conflict)。
- 写入顺序：features 先、project.json 后（project 含 features 索引，后写保证一致性）。

---

## 4. 异常与边界 (Edge Cases)

| 情形 | 行为 |
| :--- | :--- |
| journal/events.jsonl 不存在或空 | StateError → CLI 信封 `recover_no_journal`（exit 3） |
| 行 JSON 解析失败（尾部截断） | 计入 missing_events，重放前缀 |
| 事件缺关键 detail 字段 | 按未知事件处理（warning） |
| 锁冲突 | StateError 透传（CLI 信封 state_error） |

---

**文档版本**：V1.0.0
**创建日期**：{{DATE}}
**最后更新**：{{DATE}}
**文档状态**：✅ 待评审
