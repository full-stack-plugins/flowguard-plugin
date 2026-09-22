# FlowGuard · 研发流程门禁

[![skills-check](https://github.com/full-stack-plugins/flowguard-plugin/actions/workflows/skills-check.yml/badge.svg)](https://github.com/full-stack-plugins/flowguard-plugin/actions/workflows/skills-check.yml)
[![license](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

四端同源插件（ZCode / Codex / Kimi / Claude），把完整研发生命周期编排为**带硬门禁的十阶段流水线**：需求分析 → 架构设计 → 技术方案 → 测试用例 → 概要设计 → 详细设计 → 编码规范 → 代码审查 → 文档生成 → 部署交付。

## 定位

flowguard 是**流程编排器**而非工具箱：管理多功能、多模块项目的阶段推进、产物传递与门禁执行。实现参照 [OpenSpec](https://github.com/Fission-AI/OpenSpec)（MIT，见 THIRD-PARTY-NOTICES.md）；与它的根本差异 = 硬门禁 + 显式验收 + 审计留痕。

## 一图速览

- **十阶段**，每阶段产出一份可追溯产物，落在项目 `.flowguard/` 目录
- **三级结构**：项目级阶段（架构/规范/交付）走一次全项目生效；功能级流水线（需求→方案→用例→概设→详设→审查→文档）每功能独立、可并行；模块（src_roots）负责写码归属判定
- **硬门禁**：写业务码前，需求+方案+用例+概设+详设须全部验收（TDD 门槛）且规范已生成；PreToolUse 钩子以 exit 2 阻断，输出诊断信封 `{severity, code, message, fix}`
- **人在环中**：`accepted` 只能由用户经 `/flowguard-advance` 写入；唯一逃生口 `/flowguard-override` 必须用户发起 + 理由 + journal 留痕
- **追溯**：每条用例标注 REQ-ID 与测试文件；覆盖率与文件存在性机械检查

## 快速开始

```bash
/flowguard-init                                      # 生成 .flowguard/、探测技术栈与模块
/flowguard-feature new order-refund --modules order  # 创建功能并声明涉及模块
/flowguard-next                                      # 进入当前阶段，取回机读指令
# ……产出该阶段产物（技能自动路由到执行技能）……
/flowguard-advance                                   # 用户验收 → accepted
```

AI 入口还有：`/flowguard-status`（看板）、`/flowguard-gate`（门禁自检）、`/flowguard-override`（留痕逃生）。

## 命令与钩子

命令：`/flowguard-init | -feature | -status | -next | -advance | -gate | -override`。

CLI 子命令（`python3 scripts/flowguard_state.py <cmd>`，退出码 0 成功 / 2 门禁拒绝 / 3 错误）：

| 子命令 | 作用 |
|---|---|
| `init` | 建 `.flowgate/` 骨架（幂等） |
| `status [--feature X]` | 流程看板（单功能详情用 --feature） |
| `feature new <id> --modules <m...>` / `list` / `done` / `drop --reason R` | 功能生命周期 |
| `next [--feature X \| --stage S]` | 开始阶段并取回机读指令 |
| `advance [--feature X] [--stage S]` | 用户验收（accepted 唯一写入点） |
| `override --reason R [...]` | 留痕逃生 |
| `gate [--action A --path P]` | 门禁自检 / 定向判定 |
| `validate [--feature X]` | 产物机械校验 |
| `instructions <artifact> [--feature X]` | 阶段指令（context/rules/模板/Tier2） |
钩子：SessionStart（状态摘要）、PreToolUse（硬门禁，exit 2）、PostToolUse（产物校验 + 回改降级）、Stop（下一步提示）。契约见 [hooks/\_\_protocol\_\_.md](hooks/__protocol__.md)。

## 文档

- [docs/architecture.md](docs/architecture.md) — 架构（四层/三级模型/门禁）
- [docs/FLOWGUARD_ARTIFACT_SPEC.md](docs/FLOWGUARD_ARTIFACT_SPEC.md) — 产物格式契约（十类产物 + 占位符规则）
- [docs/roadmap.md](docs/roadmap.md) — Phase 2/3 路线图与开放问题

## 验证

```bash
python3 -m unittest discover -s tests            # 状态机/门禁矩阵/hooks/parity……
python3 scripts/vendor/skill_vendor.py check --offline
python3 scripts/generate_skills.py && git diff --exit-code skills/
```

## 兼容性

ZCode（hooks 约定发现）、Kimi（manifest 内联 hooks）、Codex 与 Claude（hooks.json）。仅 POSIX（fcntl 锁）。Python 仅标准库。

## 许可证

Apache-2.0。OpenSpec（MIT）实现参照——见 [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md)。相关技能：执行层用 `npx skills add full-stack-skills/<pkg> --skill <name>` 安装；lint 治理用 `npx skills add full-stack-plugins/codeguard`。
