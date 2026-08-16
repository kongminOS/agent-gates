# Governance Glossary / 治理术语表

> Kongmin Rein · 金箍圈（WUKONGQUAN）Governance Layer for AI Agent Workforces
> License: MIT · Maintained by kongminOS
> This glossary defines the Chinese governance terms for AI-agent workflow governance.
> 本表定义 AI 员工治理的中文术语体系（v1.0 · 2026-08-16 首发）。

## Core Slogan / 总纲

**引擎管流程，模型管执行，金箍圈（WUKONGQUAN）管闸门**
*The engine governs the flow, the model governs the execution, and WUKONGQUAN governs the gates.*

Layering: the workflow engine (DeepSeek Harness, MIT open-source base) drives flows at the bottom; the governance scheduling engine (built into 金箍圈/WUKONGQUAN) schedules gates on top of it. They are a base-layer vs governance-layer relationship, not peers.

## Terms / 术语

| # | Concept / 概念 | Term / 术语 | Notes / 说明 |
|---|---|---|---|
| 1 | Workflow Engine / 工作流引擎 | Engine | MIT open-source base driving the flow (e.g. DeepSeek Harness) |
| 2 | Agent Loop / 智能体循环 | Agent Loop | The raw execution loop; object of the three gaps below |
| 3 | Stage / 阶段 | Gate Stage (闸段) | A task card: manual, toolset, release policy, next station |
| 4 | Stage Machine / 阶段状态机 | Governance Scheduling Engine (治理调度引擎) / Gate State Machine (闸门状态机) | Deterministic scheduler; AI cannot skip stages |
| 5 | Gate / 门控 | Release Policy (放行策略) | Auto release / manual release / conditional release |
| 6 | Runner / 执行者 | Credentialed Runner (持证执行者) | An executor holding an AI-employee credential |
| 7 | Sub Agent / 子智能体 | Entrusted Executor (受托执行体) | Delegated independent executor (e.g. independent reviewer) |
| 8 | Signals / 双通道信号 | Machine-Readable Track / Human-Readable Track (机器可读轨/人类可读轨) | Structured signal for the engine; human report for the user |
| 9 | Tool Whitelist / 工具白名单 | Gate-Level Least Privilege (闸级最小权限) | Per-stage dynamic tool locking |
| 10 | Rolling Memo / 滚动备忘录 | Decision Stub (决议存根) | Confirmed decisions injected before each subsequent stage |
| 11 | Runner×Gate Orthogonality | Post-Credential Matrix (岗闸矩阵) | Executor × release-policy combinations |
| 12 | Hard Enforcement / 硬驱动 | Technical Enforcement (技术强制) | Flow control lives in deterministic logic, not prompts |
| 13 | Declarative Pluggable | Governance Tier (治理档位) | Standard / strict / relaxed tiers; swap folder = swap tier |
| 14 | Zero-Intrusion Mounting | Zero-Intrusion Mounting (零侵入挂接) | Standard socket; removing it does not break the core loop |
| 15 | Quality Built-In | Quality Built-In (质量内建) | Review and verification are mandatory stages |
| 16 | Bare-Loop Three Gaps / 裸循环三缺口 | Bare-Run Three Gaps (裸跑三缺口) | No gating / no consistency / no reusability |
| 17 | Fail-Closed | fail-closed | Default-deny on missing evidence |

## Usage Rules / 使用铁律

1. 对外一律使用全称「金箍圈（WUKONGQUAN）」；简称仅限内部。
2. 对外讲清归属：工作流引擎来自开源 Harness（MIT），闸门体系来自金箍圈治理层。
3. 本表为术语定义源；对外材料引用时保持中英对照。

---
*kongminOS · 2026-08-16 · MIT*