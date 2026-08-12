"""
tool_wrapper.py  --  Tool Call Wrapper (security prototype)

Behavior contract (adopted from code review v2):
  whitelist check -> dangerous tools require explicit human confirmation ->
  [dangerous ops: pending audit, fail-closed] -> execute -> audit
  Single audit source of truth: an audit backend (e.g. PocketBase detailed_logs) primary,
  daily-log fallback
  Fallback MUST alert (no silent degradation)
  Audit ordering: dangerous ops are written pending -> executed -> completed, linked by call_id
  fail-closed: if a dangerous op cannot even write its pending intent (both channels down) ->
  refuse to execute
  Tiered alerts: ordinary degradation alerts go to stderr; dangerous-op alerts must also
  land in the daily log

NOTE: standalone prototype -- NOT wired into any production runtime call chain yet.
Integrate it as the single funnel for tool calls, then audit everything through it.

Audit endpoints come from env (no hardcoded hosts):
  AUDIT_PB_URL   - primary audit backend (PocketBase-style REST), optional
  AUDIT_DAILY_URL- daily-log append endpoint, optional
If both are unset, auditing degrades to stderr + explicit alert (never silent).
"""
from __future__ import annotations
import json
import os
import sys
import uuid
import urllib.request
from datetime import datetime, timezone

PB_BASE = os.environ.get("AUDIT_PB_URL", "")  # e.g. http://127.0.0.1:8080
BRIDGE_BASE = os.environ.get("AUDIT_DAILY_URL", "")  # e.g. http://127.0.0.1:8000
DETAILED_LOGS = f"{PB_BASE}/api/collections/detailed_logs/records" if PB_BASE else ""
DAILY_APPEND = f"{BRIDGE_BASE}/api/v1/daily/append" if BRIDGE_BASE else ""

# ---- G1-G4 technical enforcement: gates move from "ask the agent" to "check the file" ----
GATE_STATE_DIR = os.environ.get("GATE_STATE_DIR", os.path.join(os.path.expanduser("~"), ".gate_state"))

# Publish / write-to-formal-dirs tools -> minimum required gate (machine-enforced;
# does not depend on the caller/agent remembering to pass required_gate).
GATE_REQUIREMENTS = {
    "publish_content": "G3",
    "publish_video": "G3",
    "release_dir_write": "G3",
}


def check_gate_passed(task_id, gate):
    """Machine-checkable gate: read gate_state/{task_id}.json, validate structure, return (ok, reason).
    Never trust the agent's self-report -- only the file's passed record
    (structure must match gate_writer output). An agent claiming "gate passed"
    without a file is exactly the failure mode this protects against."""
    if not task_id:
        return False, "missing task_id"
    p = os.path.join(GATE_STATE_DIR, f"{task_id}.json")
    if not os.path.exists(p):
        return False, f"gate_state not found for task {task_id} (run gate_writer init first)"
    try:
        with open(p, "r", encoding="utf-8") as f:
            st = json.load(f)
    except Exception as e:
        return False, f"gate_state corrupt: {e}"
    if not isinstance(st, dict) or st.get("task_id") != task_id:
        return False, "gate_state structure invalid (task_id mismatch)"
    gates = st.get("gates")
    if not isinstance(gates, dict) or gate not in gates:
        return False, f"gate_state structure invalid (missing gate {gate})"
    rec = gates[gate]
    if not isinstance(rec, dict) or rec.get("passed") is not True:
        return False, f"gate {gate} not passed for task {task_id}"
    return True, f"gate {gate} passed (task {task_id})"

DEFAULT_TOOL_WHITELIST = {
    "read_file", "write_file", "list_dir", "run_tests",
    "git_commit", "ffmpeg", "curl_get",
    "delete_path", "clear_dir", "batch_modify",
}
DEFAULT_DANGEROUS_TOOLS = {
    "delete_path", "clear_dir", "batch_modify", "rm", "rm_rf", "format_disk",
}


class ToolCallBlocked(Exception):
    """Raised on whitelist block / user rejection / fail-closed audit failure."""


class ToolWrapperConfig:
    def __init__(self, whitelist=None, dangerous=None, session_id="wrapper-proto",
                 project="default"):
        self.whitelist = set(whitelist) if whitelist is not None else set(DEFAULT_TOOL_WHITELIST)
        self.dangerous = set(dangerous) if dangerous is not None else set(DEFAULT_DANGEROUS_TOOLS)
        self.session_id = session_id
        self.project = project


def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def emit_alert(message: str, sink=None, to_daily=False, cfg=None,
               daily_writer=None):
    """Active alert. Default: stderr. Dangerous scenarios pass to_daily=True so the
    alert also lands in the daily log. `sink` captures alerts for tests."""
    line = f"[WRAPPER-ALERT] {_now_iso()} {message}"
    if sink is not None:
        sink.append(line)
    else:
        print(line, file=sys.stderr)
    if to_daily:
        payload = {
            "agent": "wrapper",
            "project": (cfg.project if cfg else "default"),
            "text": f"[wrapper-alert] {message}",
            "tags": ["wrapper-alert", "dangerous"],
        }
        try:
            dw = daily_writer or (lambda p: _http_post_json(DAILY_APPEND, p))
            dw(payload)
        except Exception as e:
            # alert-to-daily also failed: keep stderr, do not swallow
            if sink is not None:
                sink.append(f"[WRAPPER-ALERT] {_now_iso()} alert-to-daily failed: {e}")
            else:
                print(f"[WRAPPER-ALERT] alert-to-daily failed: {e}", file=sys.stderr)
    return line


def _http_post_json(url: str, payload: dict, timeout=3.0):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, resp.read().decode("utf-8", "replace")


def write_audit(record: dict, cfg: ToolWrapperConfig, alert_sink=None,
                pb_writer=None, daily_writer=None, danger_alert=False):
    """Audit write + fallback alert.
    Primary: audit backend (detailed logs). On failure: degrade to daily log + active alert.
    Returns {"sink":..., "alerted":bool}. sink in {audit-backend, daily-fallback, none}
    danger_alert=True: fallback/failure alerts also land in the daily log."""
    rec = dict(record)
    rec.setdefault("ts", _now_iso())
    full = json.dumps(rec, ensure_ascii=False)
    pb_payload = {
        "conversation_title": f"[audit] {rec.get('tool_name','?')} {rec.get('status','')}".strip(),
        "project": cfg.project,
        "session_id": cfg.session_id,
        "full_content": full,
        "date": _now_iso(),
    }
    try:
        if pb_writer is None and not DETAILED_LOGS:
            raise RuntimeError("AUDIT_PB_URL not configured")
        writer = pb_writer or (lambda p: _http_post_json(DETAILED_LOGS, p))
        status, _ = writer(pb_payload)
        if status == 200:
            return {"sink": "audit-backend", "alerted": False}
        raise RuntimeError(f"audit backend returned {status}")
    except Exception as e:
        emit_alert(f"audit degraded to daily-log fallback | tool={rec.get('tool_name','?')} "
                   f"| status={rec.get('status','')} | reason=audit backend unreachable ({e})",
                   sink=alert_sink, to_daily=danger_alert, cfg=cfg, daily_writer=daily_writer)
        daily_payload = {
            "agent": "wrapper", "project": cfg.project,
            "text": f"[audit-fallback] {full}",
            "tags": ["audit", "fallback", "tool-wrapper"],
        }
        try:
            if daily_writer is None and not DAILY_APPEND:
                raise RuntimeError("AUDIT_DAILY_URL not configured")
            dwriter = daily_writer or (lambda p: _http_post_json(DAILY_APPEND, p))
            dwriter(daily_payload)
            return {"sink": "daily-fallback", "alerted": True}
        except Exception as e2:
            emit_alert(f"audit fallback ALSO failed | reason={e2}",
                       sink=alert_sink, to_daily=danger_alert, cfg=cfg, daily_writer=daily_writer)
            return {"sink": "none", "alerted": True}


def safe_tool_call(tool_name: str, args: dict, cfg: ToolWrapperConfig = None,
                   confirm=None, execute=None, alert_sink=None,
                   pb_writer=None, daily_writer=None,
                   required_gate=None, task_id=None):
    """Core wrapper.
    Normal ops: validate -> execute -> audit (single post-write).
    Dangerous ops: validate -> confirm -> pending audit (fail-closed) -> execute -> completed audit.
    Gated ops (required_gate set): step 0 checks the gate_state file; missing/not-passed -> reject
    (no human prompt, no agent self-report).
    Raises ToolCallBlocked on block / reject / audit-failure."""
    cfg = cfg or ToolWrapperConfig()
    call_id = uuid.uuid4().hex[:12]
    is_danger = tool_name in cfg.dangerous
    base = {"call_id": call_id, "tool_name": tool_name, "args": args, "dangerous": is_danger}

    # 0) gate check (machine-checkable, independent of agent self-report; publish tools
    #    carry a built-in G3 requirement)
    effective_gate = required_gate or GATE_REQUIREMENTS.get(tool_name)
    if effective_gate:
        ok, reason = check_gate_passed(task_id, effective_gate)
        if not ok:
            write_audit({**base, "status": "rejected", "result": f"gate_blocked: {reason}"},
                        cfg, alert_sink, pb_writer, daily_writer, danger_alert=is_danger)
            raise ToolCallBlocked(f"gate blocked: {reason} (required gate={effective_gate})")

    # 1) whitelist
    if tool_name not in cfg.whitelist:
        write_audit({**base, "status": "rejected", "result": "blocked_not_whitelisted"},
                    cfg, alert_sink, pb_writer, daily_writer, danger_alert=is_danger)
        raise ToolCallBlocked(f"'{tool_name}' not in whitelist, blocked")

    # 2) dangerous ops require explicit confirmation
    if is_danger:
        approver = confirm or (lambda t, a: False)
        if not approver(tool_name, args):
            write_audit({**base, "status": "rejected", "result": "user_rejected"},
                        cfg, alert_sink, pb_writer, daily_writer, danger_alert=True)
            raise ToolCallBlocked(f"dangerous op '{tool_name}' not confirmed, aborted")

        # 2b) pending audit + fail-closed: if even the intent cannot be recorded -> refuse
        pend = write_audit({**base, "status": "pending", "result": "intent_before_execute"},
                           cfg, alert_sink, pb_writer, daily_writer, danger_alert=True)
        if pend["sink"] == "none":
            emit_alert(f"FAIL-CLOSED: dangerous op '{tool_name}' pending audit both channels down, refusing",
                       sink=alert_sink, to_daily=True, cfg=cfg, daily_writer=daily_writer)
            raise ToolCallBlocked(
                f"dangerous op '{tool_name}' cannot be audited (both channels down), fail-closed refused")

    # 3) execute
    runner = execute or (lambda t, a: {"executed": t, "args": a})
    out = runner(tool_name, args)

    # 4) audit (dangerous: completed; normal: single)
    status = "completed" if is_danger else "executed"
    write_audit({**base, "status": status, "result": "ok"},
                cfg, alert_sink, pb_writer, daily_writer, danger_alert=is_danger)
    return out


if __name__ == "__main__":
    cfg = ToolWrapperConfig()
    print(safe_tool_call("read_file", {"path": "a.txt"}, cfg, pb_writer=lambda p: (200, "ok")))
    try:
        safe_tool_call("rm_rf", {"path": "/tmp/example"}, cfg, pb_writer=lambda p: (200, "ok"))
    except ToolCallBlocked as e:
        print("BLOCKED:", e)
