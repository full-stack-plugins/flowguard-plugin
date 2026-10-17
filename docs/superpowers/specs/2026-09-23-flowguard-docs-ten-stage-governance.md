# FlowGuard 十阶段文档治理规格

> **文档说明**：修正 v0.2.0 的阶段所有权与存储位置，定义智能体推进、`docs/` 承载产物的强制十阶段流程。
> **版本**：v1.0
> **最后更新**：2026-09-23

## 1. 决策与事实源

用户确认十阶段仍是 FlowGuard 的强制流程骨架，智能体负责推进；项目仓库不需要 `.flowguard/` 目录，十阶段文档都在 `docs/`。本规格取代 [v0.2.0 规格](2026-09-23-flowguard-agent-driven-sdd-governance.md) 中“十阶段仅兼容”和“治理数据写入 `.flowguard/`”的规定。其余原生 SDD 发现、任务层级与证据有效性原则继续适用。

正式需求可由 Spec Kit 或 OpenSpec 管理，工程执行可使用 Superpowers；FlowGuard 的十阶段验收文档引用原生产物，不复制规格正文。同一变更仅绑定一套正式规格事实源。

## 2. 十阶段与目录

| 阶段 | 文档 | 所有者 |
|:---|:---|:---|
| 01 需求分析 | `docs/features/<feature>/01-requirements.md` | 功能或独立子功能 |
| 02 架构设计 | `docs/project/02-architecture.md` | 项目，子功能继承 |
| 03 技术方案 | `docs/features/<feature>/03-solution.md` | 功能或独立子功能 |
| 04 测试用例 | `docs/features/<feature>/04-testcases.md` | 功能或独立子功能 |
| 05 概要设计 | `docs/features/<feature>/05-hld.md` | 功能或独立子功能 |
| 06 详细设计 | `docs/features/<feature>/06-lld.md` | 功能或独立子功能 |
| 07 编码规范 | `docs/project/07-standards.md` | 项目，子功能继承 |
| 08 代码审查 | `docs/features/<feature>/08-review.md` | 功能或独立子功能 |
| 09 文档交付 | `docs/features/<feature>/09-docs.md` | 功能或独立子功能 |
| 10 发布交付 | `docs/project/10-release.md` | 项目，汇总功能 |

文档遵循 full-stack-doc 的元信息、版本记录、责任人、章节编号与证据要求。机器可解析的阶段状态、原生引用、批准依据和证据登记必须位于文档内。功能子级通过文档中的父级引用建立关系，不复制项目级文档。普通实现步骤保留在原生 tasks 中。

## 3. 阶段推进

智能体依据用户目标和仓库事实决定任务、当前阶段、适用工具与下一步，并显式申请阶段推进。FlowGuard 校验阶段依赖、文档内容、用户批准和证据，然后记录 `pending / in_progress / pending_acceptance / accepted / inherited / skipped / invalidated`。继承与跳过必须有可审计来源或理由。阶段正文改变后，原验收失效；受影响下游按依赖图失效。

项目级 `10-release.md` 的发布内容表必须逐项列出本次交付的功能；发布验收绑定 07 编码规范与表内各功能 09 文档交付的验收指纹。任一列入功能的 09 阶段失效或重新验收后，旧的 10 发布验收不得继续放行。表内无有效功能时不能验收发布阶段。

写业务代码前，01—07 阶段必须满足；允许提前补测试以遵循 TDD。提交前，08 和 09 阶段须满足，且测试、静态分析、语义审查证据与当前代码匹配。发布前，10 阶段、发布就绪、用户验收、必要子功能及依赖须满足。读取、澄清、补规格、补测试及修复阻断的动作始终可用。

## 4. 数据与信任边界

- 项目仓库中的流程事实源是 `docs/` 文档。会话选择可缓存到宿主状态目录；删除缓存后，可由 Git、`docs/` 和原生规格重建流程事实。
- 证据在阶段文档中登记上下文 ID、生产者、结果、引用、时间与代码指纹；同一功能的不同会话不能互用证据，没有上下文归属的旧记录仅供审计。最新失败结果覆盖旧 PASS。功能级验收记录前置阶段指纹，上游文档变化及重新验收不会自动恢复下游验收。代码或适用规格变化会使全部门禁证据失效，包括发布用户验收；旧的“不随代码过期”记录不得绕过此规则。
- 用户批准不能由智能体自述、`--actor user` 字符串或模型 PASS 伪造。没有宿主提供的不可伪造用户确认回执时，不能宣称提交/发布门禁具备对抗性强制能力。
- Hooks 负责发现、提醒、校验、拦截和回报，不自动决定语义阶段或替用户验收。
- 通用 Shell 写入、不同宿主的 Hook 协议、安装后的实际触发均属于生产验收范围；仅通过单元测试或清单校验不足以证明完整强制门禁。

## 5. 迁移与兼容（已下线）

**变更（2026-09-23，v0.4.0）**：`.flowguard/` 兼容/迁移线全面下线——不再提供 `migrate`/`legacy-init`，旧状态机命令（feature/next/advance/override/status/gate）与旧 gate 解锁矩阵一并移除，仓库内不得出现 `.flowguard/`。`docs/legacy-flowguard/` 仅是本仓迁移前状态的只读历史归档，不构成迁移承诺。

## 6. 验收行为

1. 在全新 Git 仓绑定功能并创建十阶段文档后，仓库内不存在 `.flowguard/`。
2. 删除宿主会话缓存后，扫描 `docs/` 能恢复项目、功能、父子关系和阶段状态。
3. 01—07 未满足时阻断业务写入；08/09 未满足或证据过期时阻断提交；10 和用户验收未满足时阻断发布。
4. 十阶段文档按 full-stack-doc 结构生成，原生 SDD 正文只被引用。
5. 测试、CodeGuard、CodeReview 结果进入对应阶段文档；最新失败不能被旧 PASS 掩盖。
6. 旧 `.flowguard/` 命令面不存在，仓库内不出现 `.flowguard/` 目录。
7. Codex、ZCode、Kimi 至少各有一个真实安装与 Hook 触发回执；缺失的宿主能力必须明确为未验证或降级，而非宣称强制门禁。

---

**文档版本**：v1.0
**创建日期**：2026-09-23
**最后更新**：2026-09-23
**文档状态**：🔧 实施中

## 显示名称统一（2026-10-03，来源：用户命名要求）

插件各宿主清单与市场入口的 `displayName` 统一为 `FlowGuard`，英文国际化名称同步为 `FlowGuard`。插件 id、命令前缀与中文本地化翻译保持兼容。

## 7. 工程守卫协议集成增量（2026-10-17）

来源：2026-10-17 按既有总体规划重建，feature: engineering-guard-integration。当前检出未包含旧引用的 EG-W 定义；以下是新重建内容，不声称恢复历史原文。依据为 [traceability](https://github.com/full-stack-plugins/codeguard/blob/8d7c0e997bf21b3306573b3be89ff8c312c9de38/docs/engineering-guard/traceability.md)、[acceptance](https://github.com/full-stack-plugins/codeguard/blob/8d7c0e997bf21b3306573b3be89ff8c312c9de38/docs/engineering-guard/acceptance.md)、[protocol](https://github.com/full-stack-plugins/codeguard/blob/8d7c0e997bf21b3306573b3be89ff8c312c9de38/docs/engineering-guard/protocol.md) 和本规格既有十阶段约束。不建立 OpenSpec 或第二套阶段事实源，不修改现有用户验收语义。

状态：规划待实施。原有1—6节及显示名称要求继续适用；增加职责明确的版本化交接，不把生成文件或模型结论视为用户批准。

### Requirement: EG-WF-001 保留十阶段与原生事实源

系统 SHALL 十阶段仍由智能体推进，项目/功能文档继续存放于既定 docs 布局；Spec Kit/OpenSpec 正文只引用，普通实现步骤留在原生任务中，不创建第二套规格事实源。

#### Scenario: EG-WF-001 reject unsafe or incomplete input

- **WHEN** 项目同时含多套规格且当前变更归属不明
- **THEN** 报告冲突，不初始化或自动迁移体系

#### Scenario: EG-WF-001 preserve supported behavior

- **WHEN** 已绑定唯一原生变更及既定阶段文档
- **THEN** 按原有阶段归属读取与校验，保留历史引用

### Requirement: EG-WF-002 独立证据与实际候选

系统 SHALL 消费独立生产者的精确候选证据，分开执行/结论/覆盖/信任，保留原件和限制；CodeReview success、Git allow 和测试局部通过不能代替全部必需义务。

#### Scenario: EG-WF-002 reject unsafe or incomplete input

- **WHEN** 报告limited或属于其他候选/任务
- **THEN** 保留审计线索并标记缺口，不推进阶段

#### Scenario: EG-WF-002 preserve supported behavior

- **WHEN** 所有必需证据均匹配当前批准范围和候选
- **THEN** 仅评价技术就绪，用户验收仍独立核验

### Requirement: EG-WF-003 批准的来源与有效期

系统 SHALL 批准必须核验独立来源、身份、角色、意图、scope、audience、期限和撤销；同范围已有授权可复用，agent 自述或候选可写字段不构成批准。

#### Scenario: EG-WF-003 reject unsafe or incomplete input

- **WHEN** 输入伪造actor=user、accepted或trusted
- **THEN** 拒绝认可，不能签发或消费grant

#### Scenario: EG-WF-003 preserve supported behavior

- **WHEN** 已验证授权范围未扩大且未过期撤销
- **THEN** 复用已有授权，候选变化仍要求新证据

### Requirement: EG-WF-004 唯一流程判定与统一动作决策

系统 SHALL 流程语义在迁移前仅由 flowguard_lib 判定，Rust FlowGuard 对等验收接收后插件委托产品；公共内核只执行通用策略，不持有十阶段或其他领域规则。

#### Scenario: EG-WF-004 reject unsafe or incomplete input

- **WHEN** 测试通过但缺必需代码/架构/规格/审查结果
- **THEN** 动作结果incomplete并列出义务，不从阶段文字推断通过

#### Scenario: EG-WF-004 preserve supported behavior

- **WHEN** 语义迁移前后同一输入完成差分
- **THEN** 结果及恢复动作等价且只保留一个规则owner

### Requirement: EG-WF-005 跨插件协调与有界恢复

系统 SHALL 同事件可单飞，不同session/worktree/task隔离；取消、失败、断连与迟到报告按受信序列和当前输入处理。MUTED与必需审查冲突只解释缺口，不擅自外发。

#### Scenario: EG-WF-005 reject unsafe or incomplete input

- **WHEN** 最新失败后收到旧PASS或另一会话批准
- **THEN** 旧记录只供审计，不恢复放行或串用批准

#### Scenario: EG-WF-005 preserve supported behavior

- **WHEN** 相同事件安全重试且已有授权覆盖范围
- **THEN** 有界复用受管运行，保留恢复路径而不重复副作用

### Requirement: EG-WF-006 任务依赖与风险范围

系统 SHALL 冻结任务/阶段依赖、需求和候选影响范围；跨功能或API变化必须使受影响下游证据失效，不能只按改动文件判断无冲突。

#### Scenario: EG-WF-006 reject unsafe or incomplete input

- **WHEN** 不同文件任务存在API契约冲突
- **THEN** 保留语义风险并要求实际合入候选验证

#### Scenario: EG-WF-006 preserve supported behavior

- **WHEN** 独立任务没有实际依赖冲突
- **THEN** 不误阻，披露图谱覆盖与未知范围

### Requirement: EG-WF-007 历史与平台治理

系统 SHALL 阶段/ADR/契约修订与历史证据可追溯，发布按逐仓状态恢复；平台模式实施租户/任务隔离及保留/撤销，不能用本地可写文件自证生产身份。

#### Scenario: EG-WF-007 reject unsafe or incomplete input

- **WHEN** 上游契约变化或跨租户读取证据
- **THEN** 旧验收失效或拒绝读取，保留审计且不泄密

#### Scenario: EG-WF-007 preserve supported behavior

- **WHEN** 授权范围内查询历史并恢复分阶段发布
- **THEN** 保留真实逐仓状态，不声称跨仓原子事务

### Requirement: EG-WF-008 宿主与受控门禁验收

系统 SHALL 逐宿主/平台验证实际安装、事件、正常/拒绝/取消/重入及升级回滚；本地Hook可绕过，完整强制声明须绑定受保护CI、独立身份与精确授权执行证据。

#### Scenario: EG-WF-008 reject unsafe or incomplete input

- **WHEN** 只有单元测试或伪造用户回执通过
- **THEN** 保持未验收，不宣称对抗性强制

#### Scenario: EG-WF-008 preserve supported behavior

- **WHEN** 真实宿主与受控执行矩阵全部满足
- **THEN** 仅对经过证据证明的版本组合声明支持
