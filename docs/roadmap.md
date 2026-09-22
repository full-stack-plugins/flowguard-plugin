# FlowGuard 技术路线图

> Phase 1（v0.1.x）已完成：编排核 / 十阶段 DAG / 硬门禁 hooks / 11 技能 / vendor 机制 / e2e 验收。
> 本文跟踪后续分期与开放问题；权威设计见 spec v3.1。

## Phase 2 —— 审查与文档厚化（下一优先）

| 项 | 内容 | 备注 |
|---|---|---|
| 代码审查厚化 | `flowguard-review` 嫁接五语言 *-code-review 的证据化发现项契约与打分维度 | 需先定「审查对象边界」（见开放问题） |
| 文档生成厚化 | `flowguard-docs` 嫁接 full-stack-doc 文档体系 + api-doc-generator | 顺带决定 09-docs 是否细分 API/用户文档 |
| journal 恢复工具 | 从 `journal/events.jsonl` 重建状态文件（灾难恢复） | Phase 1 只留痕不重建 |
| 错误路径测试补强 | hooks 异常分支、并发锁多进程实测 | |

## Phase 3 —— 架构/交付厚化 + 全量按栈路由

| 项 | 内容 |
|---|---|
| 架构设计厚化 | `flowguard-architecture` 嫁接 ddd-architecture-selector 选型决策矩阵 |
| 部署交付厚化 | `flowguard-release` 嫁接 easy4j-deploy / fw-release-gate 发布证据链 |
| 发布范围（版本列车） | 功能 → 版本/里程碑归属，替代「全部功能收敛」的粗粒度解锁 |
| 按栈路由全量 | 各阶段执行技能的完整栈路由表 |
| `flowguard export --openspec` | 功能需求机械导出为 OpenSpec change（格式已兼容） |

## 开放问题（不阻塞迭代）

1. **审查对象边界**（P0 级设计缺口）：08-review 的 diff 范围按功能分支 / journal 写码记录 / 用户圈定文件？Phase 2 前必须定。
2. **发布范围**：功能→版本归属（随 Phase 3）。
3. **功能间依赖**（dependsOn/provides）：Phase 2 视真实项目痛点再定。
4. 功能级文档粒度：09-docs 一份清单 vs 细分。
5. Tier 1 vendor 恢复：给 design/ddd/python/java/rust-skills 五上游仓打不可变 tag → 回填 skills.lock.json → `skill_vendor update`（执行技能由「安装命令引用」升级为「离线快照」）。
