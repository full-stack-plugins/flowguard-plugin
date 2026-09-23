<!-- 元信息 -->
<!-- artifact: 03-solution | feature: journal-restore | modules: scripts -->
# journal-restore 技术方案文档

> **文档说明**：技术方案阶段产出物，明确实现选型、接口契约与风险预案。
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

## 2. 实现选型 (Approach)

- 新增 `scripts/flowguard_lib/recover.py`：事件重放引擎（`_replay` + 现状对比 + 冲突策略），与 `journal.py` 对偶；
- CLI 子命令 `recover [--dry-run] [--force] [--json]` 为薄壳，逻辑全在 recover.py（编排核单一判定源纪律）；
- 事件语义表见 06-lld；journal 读取复用 `journal.read(root)`；落盘只经 `state._atomic_write`。

---

## 3. 接口契约 (Interfaces)

```python
def rebuild(root: Path, *, dry_run: bool = False, force: bool = False) -> dict:
    """返回 RebuildReport:
    {"rebuilt": [相对路径],            # 实际重建（dry-run 下为将重建）
     "skipped": [{"path", "reason"}],  # conflict / unchanged
     "missing_events": int,            # 解析失败被跳过的事件行数
     "warnings": [str]}
    journal 缺失 → raise state.StateError（CLI 转诊断信封 recover_no_journal）
    """
```

---

## 4. 风险清单 (Risks)

| 风险 | 缓解 |
| :--- | :--- |
| journal 事件形状演进，老事件不认识 | 只重放已知形状，未知计 warning 不中断（ADR-002 后果） |
| journal 尾部截断（半行 JSON） | 解析失败行计入 missing_events，重放到可用前缀 |
| 与并发写竞争 | 全程持 `state.state_lock(root)`，锁冲突快速失败 |
| 误覆盖人工修正过的状态 | 默认拒绝覆盖内容不同的目标文件，`--force` 才覆盖并留痕 |

---

**文档版本**：V1.0.0
**创建日期**：{{DATE}}
**最后更新**：{{DATE}}
**文档状态**：✅ 待评审
