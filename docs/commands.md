# FlowGuard 命令参考

版本：0.1.0 文档 · 状态：插件技能为主，独立 CLI 未完成

## 命令表

| 命令 | 作用 | 状态 |
|---|---|---|
| flowguard install | 接入宿主，不写项目 | 规划 |
| flowguard uninstall | 移除宿主接入 | 规划 |
| flowguard upgrade | 升级自身 | 规划 |
| flowguard version | 版本与协议 | 规划 |
| flowguard doctor | 环境与依赖诊断 | 规划 |
| flowguard status | 当前项目状态 | 规划 |
| flowguard discover | 只读识别项目 | 规划 |
| flowguard init | 建项目配置/基线 | 规划 |
| flowguard check | 只读门禁 | 已有/规划 |
| flowguard report | 读取证据 | 规划 |

完整领域命令：install,uninstall,upgrade,version,doctor,status,discover,init,stage,approve,check,report

## 退出码

0 PASS；1 BLOCK；2 用法/配置错误；3 UNVERIFIED/DESIGN_ONLY；4 内部错误。

## 边界

没有真实执行证据时不得输出 PASS。CodeReview 使用阿里云 OCR 的真实命令，不新增自有 CLI。
