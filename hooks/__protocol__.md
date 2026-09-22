# flowguard 钩子协议（机读契约 · 单源）

> 本文件是四个钩子的 stdout / stderr / exit-code 唯一契约。
> **改动任何钩子的输入输出行为，必须同 commit 更新本文件与 `tests/test_hooks.py`。**
> 对应实现参照：OpenSpec `docs/agent-contract.md`（MIT，见 THIRD-PARTY-NOTICES.md）。

## 输入

所有钩子从 stdin 读取宿主注入的 JSON：

```json
{ "tool_name": "Write|Edit|MultiEdit|Bash", "tool_input": { "file_path": "...", "command": "..." }, "cwd": "/项目根" }
```

- `cwd` 缺失时回退进程工作目录。
- stdin 非法 JSON：一律**放行**（exit 0），stderr 打 `WARNING: ...`。

## 各钩子行为

| 钩子 | 事件 | 行为 | stdout | stderr | exit |
|---|---|---|---|---|---|
| flowguard_status_summary.py | SessionStart | 注入流程状态摘要 | `[flowguard] ...` 多行文本 | 无 | 0（未初始化静默） |
| flowguard_gate.py | PreToolUse | 硬门禁判定 | 无 | 拒绝时 `ERROR: <msg>` + `Fix: <fix>` + `[flowguard] code=<code>`；异常 `WARNING: ...` | 放行 0 / **拒绝 2** / 异常 0 |
| flowguard_artifact_check.py | PostToolUse | 产物校验 + 回改降级 + journal | 无 | `[flowguard] ...` 提示（不阻断） | 恒 0 |
| flowguard_stage_summary.py | Stop | 阶段小结与下一步 | `[flowguard] ...` 文本 | 无 | 0（未初始化静默） |

## 门禁动作映射（flowguard_gate.py）

| tool | 判定 |
|---|---|
| Write / Edit / MultiEdit | `tool_input.file_path` → 动作 `write_code`（产物路径由 gate 内部放行） |
| Bash | `tool_input.command` 含 `registry.RELEASE_CMD_PATTERNS`（mvn deploy / npm publish / docker push 等）→ 动作 `build_release`；其余放行 |
| 其它 | 直接放行 |

## 三端兼容矩阵

| 宿主 | 声明方式 | 已知差异 |
|---|---|---|
| ZCode | `.zcode-plugin/plugin.json` **不写 hooks 键**，由 `hooks/hooks.json` 约定发现 | 无 |
| Kimi | `kimi.plugin.json` 内联 `hooks` 数组 | 无 `${CLAUDE_PLUGIN_ROOT}` 变量，用相对路径 `./hooks/...` |
| Codex / Claude | `hooks/hooks.json`（`${CLAUDE_PLUGIN_ROOT}}` 展开） | 无 |

## 防误伤原则

1. 未初始化项目（无 `.flowguard/project.json`）：全部放行。
2. 钩子自身任何异常：放行 + stderr WARNING（误伤代价 > 漏放）。
3. 拒绝时 stderr 必含诊断信封三行（ERROR/Fix/code），供 agent 与用户自助解锁。
