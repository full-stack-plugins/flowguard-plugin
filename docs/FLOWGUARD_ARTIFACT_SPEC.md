# FlowGuard 产物格式规范（FLOWGUARD_ARTIFACT_SPEC）

> 本文是十类产物的**格式契约**，与 `scripts/flowguard_lib/validation.py` 的机械校验一一对应。
> 改校验规则必须同步改本文（同 commit）。

## 0. 通用规则

- **元信息头**：产物文件首行注释块 `<!-- artifact: <id> | feature: <来源> | modules: <模块列表> -->`，模板自带，勿删。
- **占位符规则**：含 `<占位符>`（尖括号）的块视为**模板未填写示例**，不参与机械检查。真实内容不得包含 `<...>` 形式文本。
- **代码围栏掩码**：``` 围栏内的 `###`/`####` 头不参与解析。
- **追加式**（项目级产物 02/07/10）：增补条目一律追加并标注来源（`feature: <id>`），禁止改写既有正文；确需修改走回改降级流程。
- **REQ-ID 文法**：`<feature-id>/REQ-<n>`，feature-id 为 kebab（`^[a-z0-9]+(?:-[a-z0-9]+)*$`），全局唯一。

## 1. 01-requirements.md（需求分析）

```markdown
### Requirement: <需求名>
`order-refund/REQ-1` 用户 SHALL 能对已完成订单发起退款申请。

#### Scenario: <场景名>
- **WHEN** <前置与动作>
- **THEN** <可验证结果>
```

机械校验（validate）：
- requirement 头必须恰为 `### Requirement: <名称>`（层级不对报 stray header）；
- scenario 头必须恰为 `#### Scenario:`（三个 # 或列表形式报错——这种写法会静默失败）；
- 正文首行反引号内 REQ-ID 合法且属于本功能；
- 正文含 SHALL/MUST（缺 → WARNING）；每条至少 1 个 Scenario（缺 → WARNING）；
- requirement 名折叠近似（typo）→ WARNING。

## 2. 02-architecture.md（架构设计，项目级）

选型 + ADR 列表 + 模块边界。ADR 逐条追加：`- ADR-<编号>: <决策一句话> —— 背景/备选/后果`，带来源标注。

## 3. 03-solution.md（技术方案）

实现选型 / 接口契约 / 风险清单。无机械格式约束。

## 4. 04-testcases.md（测试用例）

```markdown
### 用例 TC-1: <名称>
- REQ: order-refund/REQ-1
- 测试文件: tests/test_refund.py
- 步骤: <操作序列>
- 预期: <可验证结果>
```

机械校验（追溯矩阵）：
- 每条 REQ 至少被一条用例覆盖（`- REQ: <id>` 行）；
- 每条用例必须有 `- 测试文件: <路径>` 且该文件**已存在于仓库**（执行证据最小版）。

## 5. 05-hld.md / 06-lld.md（概要设计 / 详细设计）

模块/服务划分与交互；类/表/接口明细与异常边界。无机械格式约束。

## 6. 07-standards.md（编码规范，项目级）

按模块栈的规范集 + 追加式增补记录。增补条目标注 `feature: <来源>`。

## 7. 08-review.md（代码审查）

```markdown
### 发现: <标题>
- 证据: <文件:行 或 提交>
- 结论: fix|wontfix|deferred
```

机械校验：每条发现项必须有结论行（三种取值之一）。

## 8. 09-docs.md（文档清单）

API / 用户 / 运维文档的生成记录或链接。无机械格式约束。

## 9. 10-release.md（部署交付，项目级）

版本 / 发布内容（功能清单）/ 校验与证据 / 回滚方案。解锁条件：项目 standards 已验收且全部功能 done|dropped。

## 与校验器的对应

| 规则 | validate 行为 |
|---|---|
| REQ 格式 / REQ-ID 归属 / Scenario 层级 | ERROR（拒验收） |
| SHALL/MUST 缺失、Scenario 缺失、名字近似 | WARNING |
| 追溯缺失 / 测试文件缺失 / 发现项缺结论 | ERROR |
| Tier 2 执行技能未安装 | WARNING（附安装命令） |

含 `<占位符>` 的块全部跳检（§0）。
