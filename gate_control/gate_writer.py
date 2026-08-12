#!/usr/bin/env python3
"""
gate_writer.py -- G1-G4 gate state writer (single write entry for gate state)

Principles:
  - "Did the agent pass the gate?" changes from "ask the agent" to "check the file":
    gate_state/{task_id}.json is the only source of truth.
  - This script is the ONLY entry allowed to write gate_state; other scripts/agents read only.
  - G1 pass REQUIRES --confirm (external human y/n). An agent cannot self-approve its own
    G1 -- if it could, the gate would be theater.
  - Phase 1 deliberately has no cryptographic signing; it uses "directory-exclusive write +
    structure validation" as a pragmatic start. Upgrade path: sign each state file.

Usage:
  gate_writer.py init  --task-id <id> [--summary "..." ] [--force]
  gate_writer.py pass  --task-id <id> --gate G1|G2|G3|G4 --ref "artifact ref" [--by user|agent] [--confirm]
  gate_writer.py show  --task-id <id>
  gate_writer.py list

State dir: $GATE_STATE_DIR (default: ~/.gate_state). All commands honor it.
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone

STATE_DIR = os.environ.get(
    "GATE_STATE_DIR",
    os.path.join(os.path.expanduser("~"), ".gate_state"),
)
GATE_ORDER = ["G1", "G2", "G3", "G4"]


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _path(task_id):
    return os.path.join(STATE_DIR, f"{task_id}.json")


def _new(task_id, summary):
    return {
        "task_id": task_id,
        "created_at": _now(),
        "summary": summary or "",
        "gates": {
            "G1": {"passed": False, "timestamp": None, "summary": None, "confirmed_by": None},
            "G2": {"passed": False, "timestamp": None, "spec_ref": None},
            "G3": {"passed": False, "timestamp": None, "ticket_ref": None},
            "G4": {"passed": False, "timestamp": None, "evidence_ref": None},
        },
        "current_gate": "G1",
        "locked": False,
    }


def cmd_init(args):
    os.makedirs(STATE_DIR, exist_ok=True)
    p = _path(args.task_id)
    if os.path.exists(p) and not args.force:
        print(f"ERROR: task {args.task_id} already exists at {p} (use --force to overwrite)")
        return 1
    with open(p, "w", encoding="utf-8") as f:
        json.dump(_new(args.task_id, args.summary), f, ensure_ascii=False, indent=2)
    print(f"OK: gate_state created for task {args.task_id} (current_gate=G1)")
    return 0


def cmd_pass(args):
    p = _path(args.task_id)
    if not os.path.exists(p):
        print(f"ERROR: task {args.task_id} not found (run init first)")
        return 1
    gate = args.gate.upper()
    if gate not in GATE_ORDER:
        print(f"ERROR: gate must be one of {GATE_ORDER}")
        return 1
    with open(p, "r", encoding="utf-8") as f:
        st = json.load(f)
    if st.get("locked"):
        print(f"ERROR: task {args.task_id} is locked")
        return 1
    g = st["gates"][gate]
    if g["passed"]:
        print(f"WARN: gate {gate} already passed for {args.task_id}")
    # G1 requires external human confirmation -- an agent claiming "G1 passed" on
    # its own behalf is exactly the failure mode this gate exists to prevent.
    if gate == "G1" and not args.confirm:
        print("ERROR: G1 pass requires --confirm (external user y/n). Agent cannot self-approve G1.")
        return 2
    by = args.by or ("user" if gate == "G1" else "agent")
    if gate == "G1":
        g.update({"passed": True, "timestamp": _now(), "summary": args.ref, "confirmed_by": by})
    elif gate == "G2":
        g.update({"passed": True, "timestamp": _now(), "spec_ref": args.ref})
    elif gate == "G3":
        g.update({"passed": True, "timestamp": _now(), "ticket_ref": args.ref})
    elif gate == "G4":
        g.update({"passed": True, "timestamp": _now(), "evidence_ref": args.ref})
    idx = GATE_ORDER.index(gate)
    st["current_gate"] = GATE_ORDER[idx + 1] if idx + 1 < len(GATE_ORDER) else "DONE"
    with open(p, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=2)
    print(f"OK: {gate} passed for {args.task_id} (ref={args.ref or ''}, by={by})")
    return 0


def cmd_show(args):
    p = _path(args.task_id)
    if not os.path.exists(p):
        print(f"ERROR: task {args.task_id} not found")
        return 1
    with open(p, "r", encoding="utf-8") as f:
        st = json.load(f)
    print(json.dumps(st, ensure_ascii=False, indent=2))
    return 0


def cmd_list(args):
    if not os.path.isdir(STATE_DIR):
        print("(no gate_state dir)")
        return 0
    for fn in sorted(os.listdir(STATE_DIR)):
        if not fn.endswith(".json"):
            continue
        try:
            with open(os.path.join(STATE_DIR, fn), "r", encoding="utf-8") as f:
                st = json.load(f)
            lock = "LOCKED" if st.get("locked") else ""
            print(f"{st.get('task_id', fn[:-5]):40s} current_gate={str(st.get('current_gate', '?')):6s} {lock}")
        except Exception:
            print(f"{fn[:-5]:40s} current_gate=CORRUPT")


def main():
    ap = argparse.ArgumentParser(prog="gate_writer", description="G1-G4 gate state writer (single write entry)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_init = sub.add_parser("init")
    p_init.add_argument("--task-id", required=True)
    p_init.add_argument("--summary", default="")
    p_init.add_argument("--force", action="store_true")
    p_pass = sub.add_parser("pass")
    p_pass.add_argument("--task-id", required=True)
    p_pass.add_argument("--gate", required=True)
    p_pass.add_argument("--ref", default="")
    p_pass.add_argument("--by", default=None)
    p_pass.add_argument("--confirm", action="store_true")
    p_show = sub.add_parser("show")
    p_show.add_argument("--task-id", required=True)
    p_list = sub.add_parser("list")
    args = ap.parse_args()
    fn = {"init": cmd_init, "pass": cmd_pass, "show": cmd_show, "list": cmd_list}[args.cmd]
    sys.exit(fn(args))


if __name__ == "__main__":
    main()
