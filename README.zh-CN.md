# FlowGuard（研发流程防护）

> 生命周期 CLI 已实现；领域阶段运行时仍为 DESIGN_ONLY。

**版本**：0.5.2 · **许可证**：Apache-2.0 · **技能**：11 个

[English](README.en.md)

## 项目定位

FlowGuard 是 Partme Guard 研发防护体系中的独立插件，命令前缀为 flowguard。它不依赖统一总命令，可独立安装、独立发版、独立执行。

## CLI 命令

| 命令 | 类型 |
| :--- | :--- |
| version | 独立入口 |
| doctor | 独立入口 |
| status | 独立入口 |
| discover | 独立入口 |
| check | 独立入口 |
| init | 独立入口 |

## 安装

~~~bash
codex plugin marketplace add partme-ai/full-stack-plugins
codex plugin add flowguard-plugin@full-stack-plugins
~~~

## 快速开始

~~~bash
flowguard version
flowguard doctor
flowguard status
~~~

## 当前状态

生命周期 CLI 已实现；领域阶段运行时仍为 DESIGN_ONLY。

没有真实执行证据时，不报告 PASS；未实现能力报告 DESIGN_ONLY 或 UNVERIFIED。

## 架构

命令入口、生命周期、只读检查和证据边界见 product-docs/FlowGuard/ 与 docs/。

## 边界

- 不合并为 Partme Guard 总命令。
- 不替代其他 Guard 的专业判断。
- 不自动提交、推送或修改用户代码。

## 验证

~~~bash
python3 -m pytest -q
~~~

## 许可证

Apache-2.0
