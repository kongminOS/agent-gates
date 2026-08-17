# Agent Gates · AI 员工治理闸门协议

> 给中小企业老板的 AI 员工管理制度：让 AI Agent 干活前先过闸，不自作主张、不烧钱打转。
> 一套开源协议 + 落地文档，任何团队都能抄走直接用的 AI 工作纪律。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Attribution / 来源与致谢

G1–G4 方法论受 **Matt Pocock 的生产级 Skill 体系**启发并汉化落地（学习来源：`mattpocock/grill-me` · `to-spec` · `to-tickets` · `implement`，2026-07 汉化适配为企业场景，四道闸门逻辑逐条对应原 Skill 设计）。G5–G6（对抗性审查+交付验证）概念与 [PerryLink/dsh-doublecheck](https://github.com/PerryLink/dsh-doublecheck) 平行收敛（同源于 Grill-me 方法论家族），实现完全独立。G0 开局上下文装配、G3 垂直工单、KPI 台账整合与记忆护照打通为**本项目的独立增量**。感谢原作者的工程实践。

---

## 一句话

多个 AI Agent（Claude / Codex / Trae / GPT 等）在同一台机器上干活，没人管就互相翻文件、写脏数据、烧 token。**Agent Gates** 是一套开工纪律：每次干活前先过闸门（G0 上下文装配 → G1 盘问 → G2 规格 → G3 工单 → G4 实现 → G5 审查 → G6 验证），跳门自动扣分，不需要人盯着。

## 解决什么问题

| 没有闸门 | 有闸门 |
|---------|--------|
| Agent 睁眼瞎启动，忘带上下文就开干 | G0 自动装配正确档位的上下文，并自检"真加载到了" |
| 不问就动手，方向跑偏烧 token | G1 先分清"我能自己查的" vs "必须问你的"，跳门 -10 分 |
| 干了 8 小时交不出东西 | G2-G6 规格→工单→实现→审查→验证，每步有可验证产出 |
| 出问题找不到是谁干的 | KPI 看板记录每个 Agent 的分数和编制状态 |

## 这套闸门是什么

- **G0 开工闸门**：新任务开始，自动按档位（lite/standard/heavy）装配上下文，自检"真加载到了"，不靠人粘贴。
- **G1 grill-me**：任何可执行指令前，先切"我能自查的事实" vs "必须问你的决策"。规则能判定就直接行动，不能判定不替你猜。
- **G2 to-spec**：需求 → 规格，边界不清不给过。
- **G3 to-tickets**：规格 → 垂直工单，避免拼不起来。
- **G4 implement**：实现 → 证据，交付才算完成。
- **G5 review**：独立审查者对照规格挑刺（对抗性审查），审查后改代码需重审。
- **G6 verify**：按验收标准逐维验证，proven 才算交付完成，不许"我干完了"空口。

跳门自动扣分（-10）写入 KPI 看板，机器检查不需要人发现。这就是"AI 员工治理"——不是给 AI 更多权限，是把 AI 能碰的门口标清楚。

## 文档

| 文档 | 内容 |
|------|------|
| [kongminOS/g0-gate · G0 规格（BSL 1.1）](https://github.com/kongminOS/g0-gate) | G0 开工闸门完整工程规格（分档模型/自检闭环/域路由/Enforcement 三层） |
| [docs/G1-G6.md](docs/G1-G6.md) | G1-G6 任务纪律闸门完整规格（盘问/规格/工单/实现/审查/验证 + 机器检查） |
| [docs/KPI-board.md](docs/KPI-board.md) | KPI 看板"编制状态"三维度设计（编制内/临时/已除名） |

## 快速开始

```bash
git clone https://github.com/kongminOS/agent-gates.git
cd agent-gates
# 读 G0 规格，按你的项目配置三档读取清单
```

## 为什么开源

我们是一人工作室，用这套闸门管着自己的 AI Agent 团队，跑通了才敢开源。
你不需要信我们，GitHub 上代码可查。免费试用装：把协议拿去，先信任、先用上，需要部署/定制/培训再找我们。

## 相关项目

- [kongmin-console](https://github.com/kongminOS/kongmin-console) — Agent 记忆桥接服务（识海MCP），多 Agent 共享记忆的中枢

## License

MIT © 2026 Wang Deyi (DeyiAI / Kongmin)
