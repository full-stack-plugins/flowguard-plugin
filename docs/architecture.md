# flowguard-plugin 架构

> 权威设计文档：工作区 `docs/superpowers/specs/2026-09-22-devflow-plugin-design.md`（v3.1）。本文是其实现版摘要。

## 四层结构

```
入口与门禁层   /flowguard-* 命令族（commands/*.json）+ hooks 硬门禁（hooks/）
编排技能层     flowguard 路由 + 10 阶段技能（scripts/templates/workflows.py 生成，parity 测试防漂移）
执行素材层     Tier 1 vendor（skills.lock.json；当前空锁）+ Tier 2 引用（技能名 + npx skills add 安装命令）
编排核         scripts/flowguard_state.py + scripts/flowguard_lib/*（stdlib；单一判定源）
```

## 编排核模块

| 模块 | 职责 |
|---|---|
| `diag.py` | 诊断信封 `{severity, code, message, fix}` 单源 |
| `ids.py` | kebab / REQ-ID 文法 + typo 近失折叠 |
| `yamlmini.py` | config.yaml 子集解析（stdlib-only） |
| `journal.py` | 追加式审计日志（events.jsonl，scope: project / feature:<id>） |
| `state.py` | 三级状态机（迁移矩阵单源）+ 降级瀑布 + fcntl 锁 |
| `registry.py` | 10 artifact DAG（requires/拓扑/环检测）+ 动作解锁表 + Tier2 清单 |
| `gate.py` | 门禁判定链入口（路径分类 → 解锁表） |
| `validation.py` | 产物校验（Requirement/Scenario/追溯矩阵/测试文件存在/Tier2 缺失） |
| `detect.py` | 技术栈与模块探测 + init 委托 |
| `instructions.py` | 机读指令（config.yaml context/rules 注入） |

## 三级模型与门禁

- 项目级阶段 `architecture / standards / release`（project.json）；功能级 `requirements → solution → testcases → hld → lld → review → docs`（features/<id>/state.json）；模块只是 src_roots 标注。
- 写码判定链：路径 → 模块 → current_feature 声明 → 五个前置阶段 accepted（TDD 门槛）→ standards ≥ in_progress。
- 状态机：`pending → in_progress → pending_acceptance → accepted`，出侧 `skipped/overridden` 必须留痕；产物回改触发下游降级。
- 与 OpenSpec 的分歧（有意 fork）：显式状态机 vs 状态派生；单源合并 vs 双路径；硬门禁 vs fluid。保留其三个工程出口：依赖是使能器不是枷锁、条件性产物（薄阶段）、显式 opt-out 标记。

## 并发与恢复

- 状态写入：fcntl 独占锁（`.flowguard/.lock`），锁冲突快速失败。
- journal：全局唯一 `journal/events.jsonl`，每行 {ts, scope, event, detail}；Phase 1 只留痕不重建（恢复工具 = Phase 2 开放问题）。

## 发布

市场仓 `full-stack-plugins` catalog.json 登记；`scripts/bump-plugin.mjs`（市场仓分发副本）同步四 manifest；发布 = PR 合并 + tag `vX.Y.Z`。
