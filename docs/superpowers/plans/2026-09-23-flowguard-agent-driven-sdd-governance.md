# FlowGuard 智能体驱动 SDD 治理实施计划

> **文档说明**：对应 `../specs/2026-09-23-flowguard-agent-driven-sdd-governance.md` 的可验证实施步骤。
> **版本**：v1.0
> **最后更新**：2026-09-23

## 1. 文档信息

| 阶段 | 交付物 | 验证 |
|:---|:---|:---|
| 1 | SDD/Git 只读发现模型 | 单元测试覆盖无体系、单体系、冲突与非 Git |
| 2 | 会话/工作树上下文与层级依赖 | 双会话隔离、父子依赖和原子写入测试 |
| 3 | 指纹化证据仓 | 记录、查询、过期与生产者边界测试 |
| 4 | 新策略引擎与 CLI | 动作矩阵、诊断信封和真实 CLI 集成测试 |
| 5 | 五类 Hooks | 子进程协议测试和 fail-open/fail-closed 边界 |
| 6 | 编排技能、文档和兼容层 | 生成 parity、链接、manifest 和全量回归 |

## 2. TDD 执行顺序

1. 写发现与上下文测试并确认因模块缺失失败。
2. 实现 `discovery.py`、`context.py` 的最小行为。
3. 写证据与策略测试并确认因接口缺失失败。
4. 实现 `evidence.py`、`governance.py` 和 CLI 命令。
5. 写 Hook 协议测试并确认缺少 `UserPromptSubmit`、新摘要和 Git commit 分类而失败。
6. 更新 Hook，实现范围变化提醒、证据失效和恢复建议。
7. 重写 `scripts/templates/workflows.py` 的主技能为智能体执行循环；旧阶段技能标记兼容。
8. 更新架构、README、Hook 协议和路线图。
9. 执行目标测试、全量 unittest、生成 parity、插件验证和 `git diff --check`。

## 3. 兼容策略（2026-09-23 更新：兼容线已下线）

- ~~不删除或重写现有 `.flowguard` 产物。~~ v0.4.0 起 `.flowguard` 兼容/迁移线全面下线，旧命令面移除；`docs/legacy-flowguard/` 保留为只读历史归档。
- 不把旧 accepted 状态迁移为新用户批准或新证据。
- ~~旧命令本版本继续可用，但输出兼容提示；~~ 新任务只使用治理命令（init/discover/context/evidence/governance/stage/validate）。
- 版本按仓库发布规则升级。

## 4. 完成定义

- 规格的九项验收标准均有可执行测试或明确的人工验证步骤。
- 所有已有测试通过，新增测试证明门禁既能阻止绕过，也保留解除阻断的路径。
- 生成后的技能与模板源一致。
- 文档明确区分当前实现、兼容能力和后续能力。

---

**文档版本**：v1.0
**创建日期**：2026-09-23
**最后更新**：2026-09-23
**文档状态**：✅ 已实现并验证

## 5. 工程守卫增量实施任务（2026-10-09，全部未实施）

来源：feature: partme-engineering-guard。本节是新增任务的唯一完成账本；上方历史“已实现”不适用于本节。事实源为 [十阶段规格第 7 节](../specs/2026-09-23-flowguard-docs-ten-stage-governance.md)。任务前缀 K/F/H/R/G/W 对应 codeguard/codegraph-plugin/codeguard-plugin/codereview-plugin/gitflow-plugin/flowguard-plugin；跨仓任务状态只在各自账本维护。

### 5.1 P0 流程事实与批准

- [ ] 5.1.1 **EG-W01** 固定十阶段/原生引用/动作矩阵兼容 fixture，验证 docs 是唯一流程源、会话缓存可重建且不会创造批准。依赖：EG-K01。规格：EG-WF-001。
- [ ] 5.1.2 **EG-W02** 扩展 evidence/codereview_evidence 适配共同协议，保留旧投影、当前任务/会话/候选核验和最新失败；先 RED 验证 success/limited 不得成 PASS。依赖：EG-W01, EG-R01。规格：EG-WF-002。
- [ ] 5.1.3 **EG-W03** 增加只读流程事实导出和真实批准引用，统一内核可验证阶段/规格/证据；不得靠命令 exit code 或 accepted 字样提升权威。依赖：EG-W02, EG-K03。规格：EG-WF-003, EG-WF-004。
- [ ] 5.1.4 **EG-W04** 实现 operationId 协调、缺口合并与交互 owner；双宿主/双会话/乱序 Hook 不重复询问已有授权或外发，不直接写兄弟插件状态。依赖：EG-W03, EG-H02, EG-R02。规格：EG-WF-003, EG-WF-005。
- [ ] 5.1.5 **EG-W05** 接可信 receipt 提供者与显式受控动作模式，验证自报 user、撤销/过期、controller 不可用不放行；读/补规格/允许补测试不死锁。依赖：EG-W04, EG-K09, EG-K10。规格：EG-WF-003, EG-WF-004, EG-WF-008。

### 5.2 P1/P2 风险策略与真实宿主

- [ ] 5.2.1 **EG-W06** 将架构/领域规则、API/数据库/权限风险映射成必需证据；父子依赖失效与 incident 恢复后的补规格/发布限制有确定测试。依赖：EG-W05, EG-K14。规格：EG-WF-006。
- [ ] 5.2.2 **EG-W07** 更新模板源 `scripts/templates/workflows.py`、生成流程技能及命令接入说明；保留原生 SDD 所有权与继承/跳过理由。依赖：EG-W06。规格：EG-WF-001, EG-WF-004。
- [ ] 5.2.3 **EG-W08** 完成声明宿主的实际安装、阶段批准、代码写入/Git/发布拦截、取消与恢复；统一协议与旧 Hook 差分回归，真实 receipt 缺失明确 cooperative。依赖：EG-W07, EG-H06, EG-R06。规格：EG-WF-005, EG-WF-008。

### 5.3 P3/P4 演进与发布

- [ ] 5.3.1 **EG-W09** 接入任务语义冲突与对象/方法 REVIEW，风险未决时按批准策略等待审查；AI 评分不得直接改阶段 accepted。依赖：EG-W06, EG-K23。规格：EG-WF-002, EG-WF-006。
- [ ] 5.3.2 **EG-W10** 实现跨仓依赖契约/ADR/候选/批准的可追溯视图，历史基线与当前有效状态分开；不承诺跨仓 Git 原子提交。依赖：EG-W09, EG-K25。规格：EG-WF-006, EG-WF-007。
- [ ] 5.3.3 **EG-W11** 验证平台租户/任务/会话隔离、缓存重建、证据保留和撤销；核心不可用时不将原协作结果升为强制。依赖：EG-W10, EG-K26。规格：EG-WF-003, EG-WF-007。
- [ ] 5.3.4 **EG-W12** 运行 unittest、vendor 离线/在线、技能与命令生成 parity、manifest/协议校验及真实宿主/CI/回滚；不可变发版后才完成本节。依赖：EG-W08, EG-W11。规格：EG-WF-001, EG-WF-008。

每项实施采用行为 RED→最小实现→GREEN→受影响回归；真实宿主和服务端门禁缺证据时保持未完成。原先测试通过记录不可证明新协议集成通过。
