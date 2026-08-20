#!/usr/bin/env bash
# PreToolUse hook: announce which Skill / subagent (Task) is being invoked,
# so the session transcript shows what is currently active.
# jq-free: parse stdin JSON with Python (same convention as catalog-sync.sh).
set -uo pipefail

# A hook must never block the user's tool call, so a missing or broken
# bootstrap exits quietly instead of erroring.
. "$(cd "$(dirname "${BASH_SOURCE[0]}")/../scripts" && pwd)/_bootstrap.sh" 2>/dev/null || exit 0
[ -z "$PYTHON_CMD" ] && exit 0

INFO=$($PYTHON_CMD -c '
import sys, json
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
tool = d.get("tool_name", "")
ti = d.get("tool_input", {}) or {}
if tool == "Skill":
    name = ti.get("skill") or "?"
    msg = f"[使用中] skill: {name}"
elif tool == "Task":
    name = ti.get("subagent_type") or "?"
    desc = ti.get("description") or ""
    msg = f"[使用中] subagent: {name}" + (f" ({desc})" if desc else "")
else:
    sys.exit(0)
print(json.dumps({"systemMessage": msg}, ensure_ascii=False))
' 2>/dev/null || true)

[ -n "$INFO" ] && printf "%s\n" "$INFO"
exit 0
