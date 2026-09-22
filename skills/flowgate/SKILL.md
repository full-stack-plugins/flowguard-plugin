---
name: flowgate
license: Apache-2.0
description: flowgate 研发流程门禁的路由中心。当用户提到流程/阶段/验收/门禁/推进、或不确定该用哪个 flowgate-* 技能时使用；按意图把工作路由到十个阶段技能，lint/CVE/安全等治理需求路由给 codeguard-plugin。不要用它直接编写需求或测试用例（那是阶段技能的职责）。
compatibility: 需要项目内已运行 /flowgate-init；所有状态查询经由编排核 CLI，只读。
---

# flowgate —— 研发流程门禁 · 路由中心

把研发流程意图路由到正确的阶段技能或执行技能。流水线：需求分析 → 架构设计 → 技术方案 → 测试用例 → 概要设计 → 详细设计 → 编码规范 → 代码审查 → 文档生成 → 部署交付（十阶段）。

## 30 秒开始

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/flowgate_state.py" status        # 流程看板
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/flowgate_state.py" gate          # 四类动作放行状态
```

## REQUIRED ROUTER

- flowgate-requirements → 需求分析（01）
- flowgate-architecture → 架构设计（02，项目级）
- flowgate-solution → 技术方案（03）
- flowgate-testcases → 测试用例（04）
- flowgate-hld → 概要设计（05）
- flowgate-lld → 详细设计（06）
- flowgate-standards → 编码规范（07，项目级）
- flowgate-review → 代码审查（08）
- flowgate-docs → 文档生成（09）
- flowgate-release → 部署交付（10，项目级）
- codeguard-plugin 的 codeguard-* → lint 门禁/CVE/安全审查（npx skills add full-stack-plugins/codeguard）

## 流程操作入口（命令）

/flowgate-init · /flowgate-feature · /flowgate-next · /flowgate-advance · /flowgate-gate · /flowgate-override

## 硬性约束（会被门禁/校验强制）

- 写业务源码前：需求/方案/用例/概设/详设全部 accepted（TDD 门槛），项目规范已生成
- 验收（accepted）只能由用户确认写入；override 必须用户发起 + 理由留痕
- 状态只能经编排核 CLI 变更；手改 state.json 视为破坏

## 软约束（prompt 级契约，靠执行者自觉）

- 产物遵守模板与元信息头；项目级产物增补一律追加式
- 跨技能引用只用「技能名 + 安装命令」
