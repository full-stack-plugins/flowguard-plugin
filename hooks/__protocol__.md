# FlowGuard Hook 协议

> 本文件是五类 Hook 的输入、输出与退出码契约。修改协议必须同步测试。

## 1. 通用输入

```json
{
  "session_id": "宿主会话标识",
  "cwd": "/项目或 worktree 根",
  "tool_name": "Write|Edit|MultiEdit|Bash",
  "tool_input": {"file_path": "...", "command": "..."},
  "tool_response": {"exit_code": 0, "output": "..."}
}
```

- `session_id` 缺失时尝试 `conversation_id`，最后回退 `default`。
- `cwd` 缺失时回退进程工作目录。
- stdin 非法或 Hook 自身异常：exit 0 并尽力输出 WARNING，避免宿主被插件故障锁死。
- 治理事实明确缺失时，PreToolUse 使用 exit 2 阻断。

## 2. Hook 行为

| 脚本 | 事件 | 职责 | 输出 | exit |
|:---|:---|:---|:---|:---:|
| `flowguard_status_summary.py` | SessionStart | 只读发现 SDD、恢复上下文、提示冲突/待分类 | stdout 摘要 | 0 |
| `flowguard_prompt_guard.py` | UserPromptSubmit | 提醒智能体重新判断任务、范围与事实源 | stdout 提醒 | 0 |
| `flowguard_gate.py` | PreToolUse | 校验业务写入、Git commit、发布；保护治理状态 | stderr 诊断 | 0 / 2 |
| `flowguard_artifact_check.py` | PostToolUse | 使旧证据过期；在有明确 exit_code 时观察测试/检查结果；兼容旧产物降级 | stderr 提示 | 0 |
| `flowguard_stage_summary.py` | Stop | 汇总上下文、缺失提交证据和下一步 | stdout 摘要 | 0 |

## 3. PreToolUse 动作映射

| 输入 | 治理动作 |
|:---|:---|
| `.specify/`、`openspec/`、`docs/superpowers/`、旧 artifact Markdown | `spec_write` |
| tests/test/__tests__ 或测试命名文件 | `test_write` |
| 其它 Write/Edit/MultiEdit | `code_write` |
| Bash `git commit` | `git_commit` |
| Bash 发布模式 | `release` |
| 读取和其它 Bash | 不阻断 |

`.flowguard/contexts`、`.flowguard/evidence`、journal、`project.json` 禁止通过文件编辑工具直接修改，返回 `governance_state_protected`。

拒绝输出至少包含：

```text
ERROR: <message>
Fix: <fix>
Missing: <missing...>
Allowed: <allowed_actions...>
[flowguard] code=<code>
```

## 4. PostToolUse 证据观察

- 只有宿主返回明确整数 `exit_code` 时才记录 Bash 证据。
- 首批识别测试、静态检查和显式 CodeReview 命令。
- 不保存原始命令和输出，只保存命令 SHA-256 摘要、类型、生产者和退出码，避免泄漏凭据。
- 命令成功只产生对应证据，不自动推进原生 SDD 阶段，也不产生用户验收。

## 5. 宿主声明

| 宿主 | 声明方式 | 约束 |
|:---|:---|:---|
| ZCode | `hooks/hooks.json` 约定发现 | `.zcode-plugin/plugin.json` 不写 hooks |
| Kimi | `kimi.plugin.json` 内联五类 Hook | 使用 `./hooks/...` 相对路径 |
| Codex / Claude | `hooks/hooks.json` | `${CLAUDE_PLUGIN_ROOT}` 由宿主展开 |

## 6. 防误伤与防绕过

1. 非 Git 且无旧 FlowGuard 状态时放行。
2. Git 项目无上下文时允许读取和补规格，阻止业务写入。
3. 旧非 Git 测试夹具继续走十阶段兼容门禁。
4. 治理状态只能通过 CLI 修改，直接文件编辑被阻止。
5. 机器证据不替代用户批准或用户验收。
