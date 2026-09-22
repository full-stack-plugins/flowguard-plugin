# FlowGuard 技术路线图

> 当前规格：`docs/superpowers/specs/2026-09-23-flowguard-agent-driven-sdd-governance.md`。
> 旧十阶段 Phase 1 已完成并进入兼容维护，不再作为功能扩张主线。

## v0.2 —— 智能体驱动 SDD 治理

| 能力 | 状态 | 证据 |
|:---|:---|:---|
| Git / SDD 只读发现 | ✅ | `discovery.py` + 无体系/单体系/冲突测试 |
| session + worktree + task 绑定 | ✅ | `context.py` + 双会话隔离测试 |
| 父子任务与 depends_on | ✅ | 父任务完成阻断测试 |
| 指纹化证据与 stale | ✅ | `evidence.py` + 代码变化测试 |
| 六类动作门禁 | ✅ | `governance.py` + commit 证据矩阵 |
| 五类 Hooks | ✅ | 子进程协议测试 |
| 主技能改为智能体循环 | ✅ | 生成 parity 测试 |
| 旧十阶段兼容 | ✅ | 原有回归测试 |

## v0.3 —— 原生工具状态适配

- Spec Kit：读取 constitution、feature、plan、tasks 的真实阶段和一致性结果。
- OpenSpec：读取 change 状态、proposal/spec/design/tasks、verify/sync/archive 结果。
- Superpowers：识别正式规格、计划与必要执行技能，不创建冲突任务表。
- 提供只读 `adapter doctor`，区分 CLI、Skills、项目初始化和当前变更状态。

## v0.4 —— 可信回执与三插件协同

- 定义 CodeGuard / CodeReview / CI 通用 evidence envelope 与签名 receipt。
- FlowGuard 只消费检查报告，不调用检查实现。
- 建立 `git commit` 前统一裁决：流程归属 → 确定性检查 → 语义审查 → 用户策略。
- 加入证据生产者版本、配置摘要和覆盖范围，减少“错误 PASS”。

## v0.5 —— 风险策略与迁移

- 仓库级风险策略：公共 API、数据库、权限、安全、发布动作的差异化门槛。
- 可选/必要子任务和父级集成验收。
- 旧十阶段到原生 SDD 的可逆迁移器；迁移前不移除旧命令和产物。
- 四宿主真实安装/加载/回执矩阵和性能预算。

## 开放问题

1. 宿主如何提供不可由 Agent 伪造的用户确认 receipt？
2. CodeReview 插件的报告 Schema、模型置信度和失败策略如何定义？
3. 大型 monorepo 的代码指纹应按上下文文件集还是整个 worktree 计算？
4. incident 恢复后补规格的最大时间窗口和发布限制如何配置？
5. 旧十阶段兼容层何时满足移除条件？
