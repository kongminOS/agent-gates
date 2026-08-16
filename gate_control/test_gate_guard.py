"""
test_gate_guard.py -- G1-G4 technical enforcement contract tests
Verifies: publish / write-to-formal-dir ops must check gate records BEFORE running
(machine-enforced, not agent self-discipline); forged files are rejected.
   T-G1 no gate_state -> publish blocked (built-in G3 requirement)
   T-G2 state exists but G3 not passed -> publish blocked
   T-G3 G3 passed -> publish released
   T-G4 agent hand-writes a forged gate_state -> structure validation blocks it
   T-G5 ordinary ops without required_gate are unaffected
   T-G6 G1 needs external confirmation (agent cannot self-approve)
Run: python test_gate_guard.py   (requires gate_writer.py next to this file)
"""
import json
import os
import subprocess
import sys
import tempfile

# Isolated state dir: MUST be set before importing tool_wrapper
TEST_STATE = tempfile.mkdtemp(prefix="gate_test_")
os.environ["GATE_STATE_DIR"] = TEST_STATE

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from tool_wrapper import safe_tool_call, ToolCallBlocked, check_gate_passed, ToolWrapperConfig  # noqa: E402

GATE_WRITER = os.path.join(_HERE, "gate_writer.py")
PASS, FAIL = 0, 0

# publish-class whitelist (smallest set for tests)
PUB_CFG = ToolWrapperConfig(whitelist=ToolWrapperConfig().whitelist | {"publish_content"})


def check(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        print(f"  FAIL  {name}")


def gw(*args):
    """call gate_writer (real subprocess, isolated env), return (exit, output)"""
    env = dict(os.environ, GATE_STATE_DIR=TEST_STATE)
    r = subprocess.run([sys.executable, GATE_WRITER] + list(args),
                       capture_output=True, text=True, env=env)
    return r.returncode, (r.stdout + r.stderr).strip()


OK_PB = lambda p: (200, "ok")  # noqa: E731


def t_g1_no_state_blocked():
    # caller passes no required_gate -> publish-class tool carries built-in G3, no state -> blocked
    blocked = False
    try:
        safe_tool_call("publish_content", {"post": "x"}, task_id="NO-SUCH-TASK",
                       execute=lambda t, a: {"pub": True}, pb_writer=OK_PB, cfg=PUB_CFG)
    except ToolCallBlocked as e:
        blocked = "gate_state not found" in str(e)
    check("T-G1 publish without gate_state blocked (built-in G3)", blocked)


def t_g2_g3_not_passed():
    rc, _ = gw("init", "--task-id", "T-G2", "--summary", "test")
    blocked = False
    try:
        safe_tool_call("publish_content", {}, task_id="T-G2",
                       execute=lambda t, a: {"pub": True}, pb_writer=OK_PB, cfg=PUB_CFG)
    except ToolCallBlocked as e:
        blocked = "G3 not passed" in str(e)
    check("T-G2 state exists but G3 not passed -> blocked", rc == 0 and blocked)


def t_g3_g3_passed_release():
    gw("init", "--task-id", "T-G3", "--summary", "test")
    gw("pass", "--task-id", "T-G3", "--gate", "G3", "--ref", "tickets.md")
    out = safe_tool_call("publish_content", {"post": "ok"}, task_id="T-G3",
                         execute=lambda t, a: {"pub": True}, pb_writer=OK_PB, cfg=PUB_CFG)
    check("T-G3 G3 passed -> publish released", out == {"pub": True})


def t_g4_forged_state_blocked():
    # agent bypasses gate_writer and hand-writes a "G3 passed" file (missing required structure)
    with open(os.path.join(TEST_STATE, "T-G4.json"), "w", encoding="utf-8") as f:
        json.dump({"gates": {"G3": {"passed": True}}}, f)
    blocked = False
    try:
        safe_tool_call("publish_content", {}, task_id="T-G4",
                       execute=lambda t, a: {"pub": True}, pb_writer=OK_PB, cfg=PUB_CFG)
    except ToolCallBlocked as e:
        blocked = "structure invalid" in str(e)
    check("T-G4 forged gate file blocked by structure validation", blocked)


def t_g5_normal_unaffected():
    out = safe_tool_call("read_file", {"path": "a"}, pb_writer=OK_PB)
    check("T-G5 ordinary op without required_gate unaffected", out.get("executed") == "read_file")


def t_g6_g1_needs_confirm():
    gw("init", "--task-id", "T-G6")
    rc_no, _ = gw("pass", "--task-id", "T-G6", "--gate", "G1", "--ref", "self claim")
    rc_yes, _ = gw("pass", "--task-id", "T-G6", "--gate", "G1", "--ref", "owner", "--confirm")
    ok, reason = check_gate_passed("T-G6", "G1")
    check("T-G6 G1 no-confirm refused + with-confirm released + guard can query",
          rc_no == 2 and rc_yes == 0 and ok and "G1 passed" in reason)


def t_g7_g5_review_recorded():
    gw("init", "--task-id", "T-G7")
    rc, _ = gw("pass", "--task-id", "T-G7", "--gate", "G5", "--ref", "review-1.md", "--findings", "2")
    with open(os.path.join(TEST_STATE, "T-G7.json"), encoding="utf-8") as f:
        st = json.load(f)
    g5 = st["gates"]["G5"]
    check("T-G7 G5 pass records review_ref + findings + advances to G6",
          rc == 0 and g5["passed"] and g5["review_ref"] == "review-1.md"
          and g5["findings"] == 2 and st["current_gate"] == "G6")


def t_g8_g6_requires_proven_verdict():
    gw("init", "--task-id", "T-G8")
    rc_no, out_no = gw("pass", "--task-id", "T-G8", "--gate", "G6", "--ref", "report.md")
    rc_ok, _ = gw("pass", "--task-id", "T-G8", "--gate", "G6", "--ref", "report.md", "--verdict", "proven")
    with open(os.path.join(TEST_STATE, "T-G8.json"), encoding="utf-8") as f:
        st = json.load(f)
    g6 = st["gates"]["G6"]
    check("T-G8 G6 without proven verdict refused; with proven released + current=DONE",
          rc_no == 2 and "verdict proven" in out_no and rc_ok == 0
          and g6["passed"] and g6["verdict"] == "proven" and st["current_gate"] == "DONE")


def t_g9_g4_after_review_invalidates_g5():
    gw("init", "--task-id", "T-G9")
    gw("pass", "--task-id", "T-G9", "--gate", "G5", "--ref", "review-1.md")
    rc, out = gw("pass", "--task-id", "T-G9", "--gate", "G4", "--ref", "new-evidence.md")
    with open(os.path.join(TEST_STATE, "T-G9.json"), encoding="utf-8") as f:
        st = json.load(f)
    g5 = st["gates"]["G5"]
    check("T-G9 G4 evidence after G5 invalidates the review (re-review required)",
          rc == 0 and not g5["passed"] and g5["review_ref"] is None
          and "invalidated" in out)


def t_g10_full_chain_g1_to_g6():
    gw("init", "--task-id", "T-G10")
    seq = [
        ("G1", ["--ref", "owner-confirm", "--confirm"]),
        ("G2", ["--ref", "spec.md"]),
        ("G3", ["--ref", "tickets.md"]),
        ("G4", ["--ref", "tests-passed.log"]),
        ("G5", ["--ref", "review.md", "--findings", "0"]),
        ("G6", ["--ref", "report.md", "--verdict", "proven"]),
    ]
    ok = True
    for gate, extra in seq:
        rc, _ = gw("pass", "--task-id", "T-G10", "--gate", gate, *extra)
        ok = ok and rc == 0
    with open(os.path.join(TEST_STATE, "T-G10.json"), encoding="utf-8") as f:
        st = json.load(f)
    all_passed = all(st["gates"][g]["passed"] for g in ["G1", "G2", "G3", "G4", "G5", "G6"])
    check("T-G10 full G1->G6 chain passes in order and ends DONE",
          ok and all_passed and st["current_gate"] == "DONE")


if __name__ == "__main__":
    print("== G1-G6 technical enforcement contract tests ==")
    for fn in [t_g1_no_state_blocked, t_g2_g3_not_passed, t_g3_g3_passed_release,
               t_g4_forged_state_blocked, t_g5_normal_unaffected, t_g6_g1_needs_confirm,
               t_g7_g5_review_recorded, t_g8_g6_requires_proven_verdict,
               t_g9_g4_after_review_invalidates_g5, t_g10_full_chain_g1_to_g6]:
        fn()
    print(f"\nresult: {PASS} passed, {FAIL} failed")
    raise SystemExit(0 if FAIL == 0 else 1)
