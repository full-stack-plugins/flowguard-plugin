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

## 5. 工程守卫集成任务（2026-10-17）

来源：2026-10-17 按既有总体规划重建，feature: engineering-guard-integration。当前检出未包含旧引用的 EG-W 定义；以下是新重建内容，不声称恢复历史原文。依据为 [traceability](https://github.com/full-stack-plugins/codeguard/blob/8d7c0e997bf21b3306573b3be89ff8c312c9de38/docs/engineering-guard/traceability.md)、[acceptance](https://github.com/full-stack-plugins/codeguard/blob/8d7c0e997bf21b3306573b3be89ff8c312c9de38/docs/engineering-guard/acceptance.md)、[protocol](https://github.com/full-stack-plugins/codeguard/blob/8d7c0e997bf21b3306573b3be89ff8c312c9de38/docs/engineering-guard/protocol.md) 和本规格既有十阶段约束。不建立 OpenSpec 或第二套阶段事实源，不修改现有用户验收语义。

本节全部待实施，不继承上文旧计划的“已实现并验证”状态。EG-W任务及完成状态仅在此处维护。W03/W05/W08/W13 为固定provider的兼容义务，W12为完整产品/真实宿主及owner交接的最终验收；二者都必须完成，不用拆分规避最终义务。

- [ ] 5.1 **EG-W01** [owner=flowguard-plugin] 固定十阶段、docs布局和原生SDD选择及现有provider版本；供FlowGuard产品入口接入，不声称已纯Rust。 依赖：EG-M01, EG-K01。规格：EG-WF-001。

- [ ] 5.2 **EG-W02** [owner=flowguard-plugin] 接独立领域证据与实际候选身份，保留原始报告与限制；CodeReview success/limited、Git allow质量未评价均不能推进。 依赖：EG-W01, EG-K04。规格：EG-WF-002。

- [ ] 5.3 **EG-W03** [owner=flowguard-plugin] 提供现有流程provider的批准/动作决策兼容接口，公共内核只执行通用策略；与产品最终迁移分开验收。 依赖：EG-W02, EG-K08。规格：EG-WF-003, EG-WF-004。

- [ ] 5.4 **EG-W04** [owner=flowguard-plugin] 核验scope/期限/撤销/意图及跨会话批准，保持MUTED/既有授权复用；伪造actor和范围扩大反例拒绝。 依赖：EG-W03, EG-K09。规格：EG-WF-003, EG-WF-005。

- [ ] 5.5 **EG-W05** [owner=flowguard-plugin] 接最小全域技术证据与真实批准门禁provider；缺任一契约必需域/义务/审查处置仍阻断，供首批联合验收消费。 依赖：EG-W03, EG-W04, EG-K07。规格：EG-WF-003, EG-WF-004, EG-WF-008。

- [ ] 5.6 **EG-W06** [owner=flowguard-plugin] 固定功能/任务/阶段依赖及需求增量范围，先写漏任务/跨功能影响反例，再验证独立任务合法路径。 依赖：EG-W01, EG-K03。规格：EG-WF-006。

- [ ] 5.7 **EG-W07** [owner=flowguard-plugin] 接FlowGuard产品的动作/阶段规则包，旧provider阶段语义继续单一拥有；生成技能模板与呈现面一致，不新增第二判定核。 依赖：EG-W05, EG-L02。规格：EG-WF-001, EG-WF-004。

- [ ] 5.8 **EG-W08** [owner=flowguard-plugin] 完成宿主能力、CLI/MCP/Hook协议与N/N-1兼容资格；实际安装/取消/重入每格留证，缺宿主明确unverified。 依赖：EG-W05, EG-K18。规格：EG-WF-005, EG-WF-008。

- [ ] 5.9 **EG-W09** [owner=flowguard-plugin] 接符号/API影响和当前候选证据，双会话/双worktree及不同文件语义冲突验证；风险不冒充确定事实。 依赖：EG-W06, EG-K23。规格：EG-WF-002, EG-WF-006。

- [ ] 5.10 **EG-W10** [owner=flowguard-plugin] 实现ADR/契约/依赖变化的阶段失效及逐仓发布恢复追踪，保留旧批准与原始报告，不承诺跨仓原子事务。 依赖：EG-W09, EG-K25。规格：EG-WF-006, EG-WF-007。

- [ ] 5.11 **EG-W11** [owner=flowguard-plugin] 接平台身份、租户隔离、证据保留与撤销端口，跨租户/任务读取拒绝且日志脱敏，单机不冒充平台身份。 依赖：EG-W04, EG-K26。规格：EG-WF-003, EG-WF-007。

- [ ] 5.12 **EG-W12** [owner=flowguard-plugin] 完成真实宿主、六守卫阶段联验、跨仓恢复和版本/市场发布回滚；十阶段规则正式移交后旧插件只委托产品。 依赖：EG-W07, EG-W08, EG-W10, EG-W11, EG-L04, EG-K20。规格：EG-WF-001, EG-WF-008。

- [ ] 5.13 **EG-W13** [owner=flowguard-plugin] 准备十阶段规则与批准/失效/恢复/allowed_actions的版本固定导出和黄金差分provider，供L04接收；最终owner切换仍由W12验收，不提前双写。 依赖：EG-W03, EG-W06。规格：EG-WF-004, EG-WF-008。

验证：遵循既有TDD与单一治理核纪律；测试须包含目标反例、受影响回归、模板parity、vendor与真实宿主/受保护执行证据。无环境或授权时保留未验收，不以本地Hook重放替代。全部证据齐备后才勾选；不自动发布或推进项目阶段。
