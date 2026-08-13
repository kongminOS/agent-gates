# Agent Gates — AI Employee Governance: Context, Discipline, Accountability

> **AI 员工治理 · 闸门全家桶**：开局上下文装配（G0）+ 任务纪律（G1–G4）+ 考核问责（KPI）+
> 技术强制层（可运行代码）。让 AI Agent 团队"开局带对上下文、执行不跳闸门、失职有记录"——
> 不靠人粘贴协议，不靠 Agent 自觉。

**Agent Gates** is a production-tested governance kit for running AI employees / AI agent
teams. It is built from four layers that reinforce each other:

```
G0 (context assembly) → G1–G4 (task discipline) → KPI (accountability) → gate_control (machine enforcement)
```

| Layer | What it owns | Where |
|---|---|---|
| **G0** | Session-opening context quality: the system picks the right tier (lite/standard/heavy), verifies it actually loaded, and degrades gracefully when the context budget is low | **[kongminOS/g0-gate](https://github.com/kongminOS/g0-gate)** (BSL 1.1) |
| **G1–G4** | Task discipline: grill-me (facts vs decisions) → to-spec → to-tickets → implement-with-evidence. G1 requires external human confirmation — an agent can't approve its own gate | `docs/G1-G4.md` |
| **KPI** | Accountability over time: score + staffing status (on-roster / off-roster / retired-but-called ⚠️). Gate skips are machine-written to the board (−10) | `docs/KPI.md` |
| **gate_control** | The teeth: `gate_writer.py` (single write entry for gate state) + `tool_wrapper.py` (whitelist, dangerous-op confirmation, fail-closed audit, gate check as step 0). Publish-class tool calls are hard-blocked until G3 passes | `gate_control/` |

> **Note on G0**: the G0 specification, agent-side skill and registry schema are published
> in their own repository — [kongminOS/g0-gate](https://github.com/kongminOS/g0-gate) —
> under the Business Source License 1.1 (free for personal, educational and internal
> organizational use; commercial licensing required for competing paid offerings; converts
> to MIT on 2030-08-13). Everything else in this repository remains MIT.

## Why this matters (the AI employee governance problem)

- **Agents start blind**: without a gate, an agent opens a session with missing/wrong/expired
  context — and *acts confidently on it*.
- **Agents skip discipline**: "we forgot the gate" is not a process bug, it's a *guaranteed*
  outcome when enforcement is a human habit. The fix is machine refusal, not reminders.
- **Accountability evaporates without a roster**: a score with no owner means nobody acts
  on it; a roster with no score is titles, not accountability.
- **Human habit assets don't scale**: relying on someone to paste the right protocol works
  for one operator, impossible for customers running AI employees.

If you're building **AI employees / AI agent teams / multi-agent systems** and care about
governance (discipline, accountability, reproducible behavior), this is the entry kit.

## Core ideas

| Idea | What it does |
|---|---|
| **Tiered manifests (G0)** | `lite` / `standard` / `heavy` — the system picks by task type + context-window budget, humans don't memorize |
| **Window budget guard (G0)** | Constraint = context window, not tokens; low budget → auto-degrade + report what was skipped |
| **Self-check loop (G0)** | Every source returns `ok/stale/missing/unreachable` → aggregate `context_trust: full/partial/none`; never pretend to have read something |
| **Domain routing (G0)** | Load only the protocol sections + ≤3 skills for the task domain; no full scans |
| **Versioned registry (G0)** | Protocol edit → bump version → next session effective; the registry is the sync channel |
| **No self-approval (G1)** | G1 pass requires external human `--confirm`; an agent claiming "G1 passed" on its own behalf is refused (exit code 2) |
| **Publish gate (G3)** | `publish_content` / `publish_video` / `release_dir_write` are hard-blocked until the task's gate state shows G3 passed — skipping becomes *impossible*, not merely discouraged |
| **Forged-file rejection** | Structure validation in `check_gate_passed` rejects hand-written/partial gate files |
| **Fail-closed audit** | Dangerous tool calls must record their intent *before* executing; if even the intent can't be logged, execution is refused |
| **Roster + score (KPI)** | Two axes customers understand: staffing status (who's ours, who's responsible) + KPI score (do we trust them) |

## Quick start

```
repo/
├── docs/
│   ├── G1-G4.md      # task discipline gates (localized from mattpocock/grill-me)
│   ├── KPI.md        # accountability: score + staffing dimensions
│   ├── agent-gate-suite-KPI.md    # SkillHub-format skill copy
│   └── agent-gate-suite-SKILL.md  # SkillHub-format skill copy
├── gate_control/
│   ├── gate_writer.py      # single write entry for gate state (init/pass/show/list)
│   ├── tool_wrapper.py     # tool-call security wrapper (whitelist + gates + audit)
│   ├── test_gate_guard.py  # 6 contract tests
│   └── test_gate_evidence.py
└── LICENSE            # MIT
```

**1. Read the specs** → `docs/G1-G4.md`, `docs/KPI.md` (G0 spec: see
[kongminOS/g0-gate](https://github.com/kongminOS/g0-gate))

**2. Try the enforcement layer** (no dependencies, Python ≥3.10):

```bash
cd gate_control
python test_gate_guard.py    # 6 contract tests: skipped gates blocked, forged files rejected
python test_gate_evidence.py # end-to-end: skip the gate → blocked; pass G3 → released
```

**3. Wire the gates into your runtime** — point `GATE_STATE_DIR` at your state dir
(default `~/.gate_state`), make `gate_writer.py` the only writer, and route tool calls
through `safe_tool_call`:

```python
from tool_wrapper import safe_tool_call, ToolCallBlocked, ToolWrapperConfig

cfg = ToolWrapperConfig()
try:
    safe_tool_call("publish_content", {"post": "..."}, task_id="t-1042", cfg=cfg)
except ToolCallBlocked as e:
    print("blocked:", e)   # "gate blocked: gate G3 not passed for task t-1042 ..."
```

**4. Add session-opening context assembly (G0)** — spec, agent skill and registry schema
live in [kongminOS/g0-gate](https://github.com/kongminOS/g0-gate) (BSL 1.1).

## Roadmap / honest limitations

- Gate state files are **not cryptographically signed** yet (phase 1 = directory-exclusive
  write + structure validation). Signing each state file is the stated upgrade path.
- `tool_wrapper.py` is a **standalone prototype** — integrate it as the single funnel for
  tool calls before trusting it in production.
- Enforcement tiers: A (harness hard-block) + B (machine auto-score) are the strongest
  combination; an embodied voice (C) that narrates "facts I can check vs decisions I need
  from you" makes governance visible to non-technical owners but must never replace A.

## License

MIT — use it, fork it, ship it. Attribution for the G1–G4 concept:
[mattpocock/grill-me](https://github.com/mattpocock/grill-me).

The **G0** specification and reference materials are licensed separately under
**BSL 1.1** in [kongminOS/g0-gate](https://github.com/kongminOS/g0-gate).
