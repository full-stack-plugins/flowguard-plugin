# FlowGuard · 研发流程门禁

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
钩子：SessionStart（状态摘要）、PreToolUse（硬门禁，exit 2）、PostToolUse（产物校验 + 回改降级）、Stop（下一步提示）。契约见 [hooks/\_\_protocol\_\_.md](hooks/__protocol__.md)。

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
