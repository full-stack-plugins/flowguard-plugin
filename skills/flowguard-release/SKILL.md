---
name: flowguard-release
license: Apache-2.0
description: 部署交付阶段（项目级收口）。当所有功能 done 后做交付收口、写发布清单时使用。不要在还有 active 功能时尝试发布（门禁会阻断）。
compatibility: 需要项目内已运行 /flowguard-init 且存在 current_feature（项目级阶段除外）；阶段推进经由编排核 CLI。
---

# flowguard-release —— 产出发布清单 10-release.md：版本/校验和/回滚方案/证据。

项目级阶段：全项目走一次。

## 30 秒开始

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/flowguard_state.py" next                       # 进入当前阶段并取回机读指令
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/flowguard_state.py" instructions 10-release --json  # 本阶段 context/rules/模板/依赖/Tier2 技能
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/flowguard_state.py" validate --json            # 产物自检
```

## 产物

写入 `.flowguard/` 下 `10-release` 对应产物，模板见 `references/templates/10-release.md`。

## 能力边界

✅ 本技能负责：本阶段产出的结构、自检与验收条件
⚠️ 前置：前置阶段未验收时门禁会阻断（诊断信封给出解锁命令）
❌ Out of Scope（REQUIRED ROUTER）：

- easy4j-deploy → 发布 SOP（npx skills add full-stack-skills/java-skills --skill easy4j-deploy）
- fw-release-gate → 发布门禁参照（npx skills add full-stack-skills/firmware-skills --skill fw-release-gate）
- codeguard-cve → 发布前 CVE 扫描（npx skills add full-stack-plugins/codeguard）

## 自检清单

- [ ] 产物按模板元信息头填写完整
- [ ] 内容与前置产物一致（追溯）

## 验收条件

validate 无 ERROR 且用户确认验收。验收由用户执行 /flowguard-advance 写入 accepted。

## 硬性约束（会被门禁/校验强制）

- 产物必须满足上方自检清单（validate 机械检查）
- 回改已验收产物会触发下游阶段自动降级（journal 留痕）
- 项目级产物增补一律追加式 + 来源标注

## 软约束（prompt 级契约）

- 遵守 instructions 返回的 context/rules（约束，不是产物内容）
- 引用 Tier 2 执行技能时给出安装命令
