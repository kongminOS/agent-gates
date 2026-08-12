# KPI — Accountability & Staffing Dimensions for AI Employees

> **Status**: Production-tested. The KPI board runs inside the studio's control console;
> this doc is the portable, de-identified spec.
> **Position**: G0–G4 answer "did the agent behave correctly *this task*?"; KPI answers
> "is this agent *accountable over time*, and what is its *staffing status*?"

---

## The two axes (don't collapse them)

| Axis | Question | What it tracks |
|---|---|---|
| **KPI score** | How well does this agent perform? | Task outcomes, gate discipline, quality, on-time delivery |
| **Staffing status (编制状态)** | Is this agent *on the roster*? Who is responsible for it? | Three states below |

Customers (non-technical owners) understand "roster + score" instantly:
the score says *trustworthy or not*, the roster says *who's ours and who's responsible*.

## Staffing status — three states

| State | Meaning | Behavior |
|---|---|---|
| **On-roster (编制内)** | Standing agent with a role, KPI, and accountability | Normal operations; scores accumulate |
| **Off-roster temporary (编制外临时)** | Pulled in per task, not standing | Scoped to the task; no standing score |
| **Retired but still called (已除名仍调用)** ⚠️ | A removed agent is being invoked anyway | **Exception flag** — forces a human decision: re-roster, keep temporary, or block |

The third state exists because "we removed the agent but the workflow still calls it"
is a silent drift. The board surfaces it as an anomaly instead of letting it run.

## How gates feed the KPI board (machine-written, no human policing)

- Skipping G0/G1 → **−10** recorded automatically to the board (who, when, which task)
- The board's gate-skip feed is read from the same gate-state store as the enforcement
  layer — the "did it really happen" check is the file, not an agent's self-report
- Roster registry can share its source with the G0 protocol registry (one source of truth,
  board auto-syncs)

## Example record shape

```json
{
  "agent_id": "example-agent",
  "staffing": "on-roster",
  "role": "content-writer",
  "kpi_score": 87,
  "gate_penalties": [
    {"date": "2026-08-12", "task_id": "t-1042", "reason": "g1_skipped", "delta": -10}
  ],
  "updated_at": "2026-08-12T05:00:00.000Z"
}
```

## Anti-patterns

| Anti-pattern | Why it fails |
|---|---|
| KPI without roster | A score with no owner/responsibility means nobody acts on it |
| Roster without KPI | "On the team" with no performance signal is a title, not accountability |
| Human-policed enforcement | The human forgets; the machine doesn't (that's the whole point of the gates) |
| Hiding ex-roster calls | Retired agents still being invoked is exactly the drift you want to *see*, loudly |
