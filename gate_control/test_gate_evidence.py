"""G1-G4 technical enforcement - end-to-end evidence test (isolated, self-contained)
Runs "deliberately skip the gate" scenarios against a temp state dir to prove the
blocking is real machine behavior, not theory.
Scenarios:
  1. Agent tries to publish without creating a task -> blocked (no gate_state)
  2. Task created but G3 not passed (gate skipped) -> blocked
  3. G3 passed (legal path) -> released
Run: python test_gate_evidence.py   (requires gate_writer.py + tool_wrapper.py next to this file)
"""
import os
import subprocess
import sys
import tempfile

# Isolated state dir: MUST be set before importing tool_wrapper
TEST_STATE = tempfile.mkdtemp(prefix="gate_evidence_")
os.environ["GATE_STATE_DIR"] = TEST_STATE

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from tool_wrapper import safe_tool_call, ToolCallBlocked, ToolWrapperConfig  # noqa: E402

GATE_WRITER = os.path.join(_HERE, "gate_writer.py")
PUB_CFG = ToolWrapperConfig(whitelist=ToolWrapperConfig().whitelist | {"publish_content"})
OK_PB = lambda p: (200, "ok")  # noqa: E731

TASKS = ["EVIDENCE-NO-STATE", "EVIDENCE-G3-MISSING", "EVIDENCE-G3-OK"]


def gw(*a):
    return subprocess.run([sys.executable, GATE_WRITER] + list(a),
                          capture_output=True, text=True).returncode


def cleanup():
    for t in TASKS:
        p = os.path.join(TEST_STATE, t + ".json")
        if os.path.exists(p):
            os.remove(p)


print("=== scenario 1: agent publishes without creating a task (no gate_state) ===")
try:
    safe_tool_call("publish_content", {"post": "x"}, task_id="EVIDENCE-NO-STATE",
                   execute=lambda t, a: {"pub": 1}, pb_writer=OK_PB, cfg=PUB_CFG)
    print("result: RELEASED! FAIL (blocking broken)")
except ToolCallBlocked as e:
    print("result: blocked OK ->", e)

print("=== scenario 2: task created but G3 skipped (gate jumped) ===")
gw("init", "--task-id", "EVIDENCE-G3-MISSING", "--summary", "evidence")
try:
    safe_tool_call("publish_content", {"post": "y"}, task_id="EVIDENCE-G3-MISSING",
                   execute=lambda t, a: {"pub": 1}, pb_writer=OK_PB, cfg=PUB_CFG)
    print("result: RELEASED! FAIL (blocking broken)")
except ToolCallBlocked as e:
    print("result: blocked OK ->", e)

print("=== scenario 3: G3 passed, publish (legal path) ===")
gw("init", "--task-id", "EVIDENCE-G3-OK", "--summary", "evidence")
gw("pass", "--task-id", "EVIDENCE-G3-OK", "--gate", "G3", "--ref", "tickets.md")
try:
    out = safe_tool_call("publish_content", {"post": "z"}, task_id="EVIDENCE-G3-OK",
                         execute=lambda t, a: {"pub": 1}, pb_writer=OK_PB, cfg=PUB_CFG)
    print("result: released OK -> out =", out)
except ToolCallBlocked as e:
    print("result: blocked! FAIL (legal path wrongly blocked) ->", e)

cleanup()
print("=== evidence tasks cleaned up ===")
