# FlowGuard Hook 协议

> 本文件是治理 Hook 的输入、输出与退出码契约。修改协议必须同步测试。

## 1. 通用输入

```json
{
  "session_id": "宿主会话标识",
  "cwd": "/项目或 worktree 根",
  "tool_name": "apply_patch|Write|Edit|MultiEdit|Bash|Shell|WriteFile|StrReplaceFile",
  "tool_input": {"file_path": "...", "command": "..."},
  "tool_response": {"exit_code": 0, "output": "..."}
}
```

- `session_id` 缺失时尝试 `conversation_id`，最后回退 `default`。
- `cwd` 缺失时回退进程工作目录。
- Codex 文件补丁使用 `tool_name=apply_patch`，补丁正文位于 `tool_input.command`；从 `Add File`、`Update File`、`Delete File`、`Move to` 标记提取全部受影响路径。
- Kimi Code CLI 使用 `Shell`、`WriteFile`、`StrReplaceFile` 等工具名，PostToolUse 的结果位于 `tool_output`；FlowGuard 与 `Bash`/`Write`/`Edit` 共用动作判定，但不会从纯文本结果猜测退出码。
- stdin 非法或 Hook 自身异常：exit 0 并尽力输出 WARNING，避免宿主被插件故障锁死。
- 已识别的写入/命令工具若缺少路径、命令或 `tool_input` 形状错误，按潜在 `code_write` 校验，不能因参数缺失直接放行。
- 文件写入路径先按实际目标规范化，再区分 `docs/`、测试与业务代码；`../` 或符号链接不能把业务文件伪装为规格/测试文件。显式写入目标超出当前 Git worktree 时返回 `governance_write_target_mismatch`。
- 治理事实明确缺失时，PreToolUse 使用 exit 2 阻断。

## 2. Hook 行为

| 脚本 | 事件 | 职责 | 输出 | exit |
|:---|:---|:---|:---|:---:|
| `flowguard_status_summary.py` | SessionStart | 只读发现 SDD、恢复上下文、提示冲突/待分类 | stdout 摘要 | 0 |
| `flowguard_prompt_guard.py` | UserPromptSubmit | 提醒智能体重新判断任务、范围与事实源 | stdout 提醒 | 0 |
| `flowguard_gate.py` | PreToolUse | 校验业务写入、Git commit、发布；拒绝越出 worktree 的写入 | stderr 诊断 | 0 / 2 |
| `flowguard_artifact_check.py` | PostToolUse | 观察 `docs/` 阶段文档是否失效；在有明确 exit_code 时记录检查结果 | stdout JSON `systemMessage`；stderr 兼容提示 | 0 |
| `flowguard_artifact_check.py` | Kimi PostToolUseFailure（Shell） | 明确的测试工具失败记 FAIL，覆盖同一指纹的旧 PASS；不把错误文本当成功摘要 | stdout JSON `systemMessage` | 0 |
| `flowguard_stage_summary.py` | Stop | 汇总上下文、缺失提交证据和下一步 | stdout JSON `systemMessage` | 0 |

`Stop` 对 CodeReview 建议性 `warning` 必须说明可信放行依据尚缺、提交继续阻断；只能引导重新审查或选择可信策略，不得提示手工登记语义审查 PASS。测试与静态分析的恢复建议仍分别指出需要真实检查结果。

## 3. PreToolUse 动作映射

| 输入 | 治理动作 |
|:---|:---|
| `.specify/`、`openspec/`、`docs/` 下的阶段文档与原生规格 | `spec_write` |
| tests/test/__tests__ 或测试命名文件 | `test_write` |
| 其它 Write/Edit/MultiEdit/WriteFile/StrReplaceFile，以及 `apply_patch` 涉及的全部文件 | 按受影响路径中最严格的动作判定；业务代码 `code_write` 要求 01—07 阶段满足 |
| Bash/Shell 中单条直接 `git commit`，目标在当前 worktree（可用同 worktree 的 `git -C`） | `git_commit`，要求 01—09 阶段及有效检查证据；跨 worktree、Shell 包装器或改写 Git 目录的全局选项拒绝 |
| Bash/Shell 中常见发布动词（Maven/Gradle/npm/pnpm/Yarn/Cargo/Docker/Helm/Twine/Make、`gh release create/upload`） | `release`，允许无副作用的全局选项，要求全部十阶段、发布证据与用户验收；通过 `--prefix`、`--repo`、`--manifest-path` 等切换项目目标时拒绝 |
| 包含提交/发布的复合命令或 Shell 包装器 | 拒绝并要求拆成独立直接工具调用，避免弱门禁掩盖另一个动作 |
| 单条已识别只读命令 | 放行；包括常见只读文件命令与 Git 状态查询 |
| 单条 Spec Kit/OpenSpec 命令，或指向插件自带 `scripts/flowguard_state.py` 的 Python 命令 | `spec_write`；同名脚本或仅在参数中出现该文件名不算 FlowGuard CLI |
| 单条已识别测试命令 | `test_write`；允许 TDD 先补测试 |
| 含重定向/管道/串联等 Shell 运算符，或无法证明只读的其它 Bash | `code_write`；缺少 01—07 阶段时阻断 |
| 明确只读或只修改宿主任务列表的工具（`Read`、`ReadFile`、`ReadMediaFile`、`Glob`、`Grep`、`LS`、`ToolSearch`、`TodoWrite`、`SetTodoList`、`update_plan`） | 放行，不变更项目流程状态 |
| `mcp__codeguard__list_languages`、`mcp__codeguard__analyze_java_impact` | 已核对为只读，放行；仅匹配 MCP 服务器名为 `codeguard` 的精确工具名 |
| `mcp__codeguard__check_code_style` | `test_write`；必须显式传入属于当前 Git worktree 的 `path`；仅在 PostToolUse 逐语言结构化检查全部 PASS 时登记静态分析 PASS |
| `mcp__codeguard__auto_fix` | `code_write`；同样要求显式同 worktree `path`，再校验 01—07 阶段 |
| 未分类的本地或 MCP 工具 | Git 项目中拒绝；先补工具副作用分类及回归测试，不能按名称猜测其只读性 |

宿主会话缓存（上下文/锁）位于仓库外的宿主状态目录，写入目标越出当前 Git worktree 返回 `governance_write_target_mismatch`；`docs/` 阶段机器区（阶段状态表、证据表）只能经 FlowGuard CLI 变更，直接手改会因指纹不匹配而失效。
CodeGuard MCP 的宿主配置若使用其他服务器名，本表不自动匹配；需按实际工具名另做审计和测试。精确名字分类只是副作用路由，不是 MCP 来源认证或结果可信度证明。

拒绝输出至少包含：

```text
ERROR: <message>
Fix: <fix>
Missing: <missing...>
Allowed: <allowed_actions...>
[flowguard] code=<code>
```

## 4. PostToolUse 证据观察

- 输入不是 JSON 对象时输出空诊断信封并退出 0，不把畸形宿主载荷解释为检查通过。
- 只有宿主返回明确整数 `exit_code` 时才可能记录 Bash/Shell 测试 PASS。Kimi 的 `tool_output` 若只提供字符串或没有明确退出码，已识别的测试命令记 WARNING 而非 PASS，覆盖同一指纹旧 PASS；`PostToolUseFailure` 是宿主明确的失败事件，针对可识别的单条测试命令记 FAIL。当前宿主实际载荷仍须安装后验收。
- 仅识别单条明确执行测试的命令；`echo pytest`、版本/收集模式、跳过测试参数及 Shell 复合命令不自动生成 PASS。退出码为 0 仍须核对 unittest、pytest、Maven、Gradle、Cargo 或 Jest/Vitest 风格摘要中的非零执行/通过数；零用例、全跳过、缺失或未知摘要记 WARNING，不作为提交门禁 PASS。非零退出码记 FAIL。命令输出本身仍是协作式观察证据，不是不可伪造的 CI 回执。
- CodeGuard 静态检查和 CodeReview 语义审查不能仅凭命令文本与退出码 0 自动生成 PASS。对服务器名精确为 `codeguard` 的 MCP `check_code_style` / `auto_fix`，PostToolUse 解析 CodeGuard 逐语言结构化回执；非空、范围一致且每项 `status=PASS`、`passed=true`、`exit_code=0` 才登记静态分析 PASS。
- CodeGuard MCP 的 FAIL、UNVERIFIED、空结果、报错或无法解析的回执，登记 FAIL 或 WARNING 并覆盖此前的 PASS；跨 worktree 目标不登记。证据只保存摘要和回执哈希，不保存完整日志。宿主工具名与 MCP 回执形状的真实加载仍需分别验收；这不是 MCP 身份认证。
- 对单条 `python3 <...>/codereview.py evidence [--request <文件>]` 命令，只在明确退出码为 0、JSON 协议 v1、会话/worktree/common_dir/HEAD/暂存区指纹与当前任务相符时消费报告。问题必须指向当前暂存文件；有问题记 `semantic_review=fail`，合法零问题报告记 `warning`，因为 CodeReview v0.1.0 的 `success` 仅是建议性结果且 `coverage_status=limited`，**不会自动生成 PASS**。回执错误、空暂存区或过期只可记 WARNING；跨 worktree 回执不登记。
- 若提交时测试和静态分析已满足、唯一缺失的是语义审查，而当前有效 CodeReview 回执仍为 `warning`，返回 `governance_semantic_review_advisory` 并保持阻断。不得提示智能体把建议报告手工改写为 PASS。当前本地证据登记仍是协作式接口，不能把人工填写的 PASS 当作不可伪造回执；可信放行依据与宿主/CI 独立门禁完成前，不宣称对抗性生产门禁。
- 不保存原始命令和输出，只保存命令 SHA-256 摘要、类型、生产者和退出码，避免泄漏凭据。
- 命令成功只产生对应证据，不自动推进原生 SDD 阶段，也不产生用户验收。
- 证据行含 `context_id`；没有上下文归属的旧行留在文档作历史记录，但不参与门禁。全部门禁证据随代码、当前任务及父级绑定的原生规格正文、当前任务及父级的 01—07 阶段正文变化过期；项目级 02/07 也参与指纹。未绑定的其他 Spec Kit、OpenSpec 或 Superpowers 产物不应误使本任务证据过期。证据表追加、阶段状态和批准依据元信息不参与正文指纹，避免登记自身使证据过期。不能用 CLI 关闭过期规则。
- 项目级 10 发布验收以发布内容表中列出的全部功能为范围，并绑定 07 编码规范与各功能 09 文档的验收指纹；任一列入功能 09 失效、重验或变更，10 即失效。空白、重复或非法功能清单不能构成已验收的发布范围。
- 阶段推进、项目文档初始化、旧项目迁移和证据登记共用宿主状态锁。`docs/` 阶段文档更新采用同目录临时文件替换并保留原权限；新建采用排他式原子创建，不覆盖已有目标。锁冲突或替换失败应保留旧文档。迁移若中途失败，已创建文档保留供人工核对，不回滚删除可能被外部编辑的文件。外部编辑器不受本锁约束，仍需靠正文指纹与人工协作避免并发冲突。
- Git 差异或未跟踪文件读取失败时，证据指纹不可用；提交和发布返回 `governance_git_state_unavailable` 拒绝，不以空差异沿用旧 PASS。读取、补规格、补测试和修复代码的路径保持可用。
- 带未知 Git 全局选项的 `git ... commit` 不能降级为普通 `code_write`；若无法验证目标 worktree，返回 `governance_git_target_mismatch`。`merge`、`cherry-pick`、`revert`、`rebase`、`am`、`commit-tree`、`update-ref` 等可能隐式生成提交或移动引用的直接命令返回 `governance_git_history_mutation_unverified`；用户授权的历史操作需单独设计可验证路径，不以 01—07 写码放行代替提交审查。
- 未明确分类的 Git 子命令（包括可能配置为提交别名的命令、`git push` 和 `git tag`）返回 `governance_unclassified_tool`，不能默认按 `code_write` 放行。已识别的只读命令保持可用，`git add`、`git apply`、`git mv` 仍作为写码动作检查。远端发布与特殊 Git 流程需要单独定义目标、授权和证据策略后才能放开。
- 指纹只读取 Git 跟踪或未忽略的文件；无首个提交的仓库也通过 Git 列表判定范围。符号链接只计入链接目标路径字符串，不解引用仓库外文件内容。
- `apply_patch` 应检查补丁中每个文档路径，不能只读取 `file_path`；发现失效时通过单个 JSON `systemMessage` 通知宿主。

## 5. 宿主声明

| 宿主 | 声明方式 | 约束 |
|:---|:---|:---|
| ZCode | `hooks/hooks.json` 约定发现 | `.zcode-plugin/plugin.json` 不写 hooks |
| Kimi | `kimi.plugin.json` 以内联 Hook 监听五类主事件与 Shell 的 `PostToolUseFailure`，并通过 `sessionStart.skill=flowguard` 加载编排主技能 | Hook 使用 `./hooks/...` 相对路径；安装加载仍须真实验收 |
| Codex / Claude | `hooks/hooks.json` | `${CLAUDE_PLUGIN_ROOT}` 由宿主展开 |

## 6. 防误伤与防绕过

1. 非 Git 且无旧 FlowGuard 状态时放行。
2. Git 项目无上下文时允许读取和补规格，阻止业务写入。
3. 旧非 Git 测试夹具继续走十阶段兼容门禁。
4. 新流程的十阶段文档存于 `docs/`；宿主侧缓存不应被当作仓库规格事实源。
5. 机器证据不替代用户批准或用户验收。
6. 已知的文件路径穿越/符号链接、跨 worktree 文件写入、Shell 重定向写码、复合提交/发布、带全局选项的常见发布命令和跨 worktree `git -C` 提交有 Hook 回归测试；嵌套提交因目标不可验证被拒绝。这不等于完整 Shell 语义隔离或完整发布命令枚举。别名、外部脚本、其它发布工具、禁用 Hook、伪造 CLI `actor` 或 `approval_ref` 仍可能绕过本层；上线前需真实宿主回执、可信批准来源和 Git/CI 独立门禁。
7. `PreToolUse` / `PostToolUse` 使用 `*` 匹配宿主支持的全部本地工具；宿主未走 Hook 路径的专用工具或不支持通配符的宿主仍属未验证边界。
