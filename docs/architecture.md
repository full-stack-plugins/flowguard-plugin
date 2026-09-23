# FlowGuard 架构文档入口

> 本文件保留为历史稳定链接。当前权威架构文档见 [FlowGuard-Architecture.zh_CN.md](FlowGuard-Architecture.zh_CN.md)。

当前架构保留强制十阶段，由智能体判断和推进；FlowGuard 校验 `docs/` 产物与证据，Hook 阻止绕过。旧版全局 `current_feature` 和 `.flowguard/` 状态仅作迁移输入。
