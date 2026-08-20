#!/usr/bin/env bash
# Status line for Claude Code.
# Displays: [model] branch ctx:NN% 5h:NN% 7d:NN%
# ctx is context_window.used_percentage (higher = more filled).
# 5h/7d are rate_limits.{five_hour,seven_day}.used_percentage (Pro/Max only,
# absent before the first API response). Missing fields are silently omitted.
# Reads JSON from stdin. Uses Python for JSON parsing (no jq dependency).
# Tries python3, then python, then the Windows py launcher, in that order,
# verifying each candidate actually runs a modern (3.7+) interpreter (not
# just exists) since python3 can resolve to a non-functional Windows Store
# alias stub, and an older python found first on PATH would still "work"
# but silently misbehave on newer syntax elsewhere in this repo.
# The interpreter code is written to a temp file and executed as a script
# rather than passed via `-c`, because some launchers (e.g. pyenv-win's
# shims, which are batch-file wrappers) mangle embedded newlines when a
# multi-line `-c` argument crosses the Git Bash -> cmd.exe boundary,
# corrupting the script and failing silently.
# If no working interpreter is found or JSON parsing fails, prints nothing
# (silent fallback) so that the harness does not display garbled text.

set -u

input="$(cat || true)"
if [ -z "$input" ]; then
  exit 0
fi

PYTHON_CMD=""
for cmd in "python3" "python" "py -3"; do
  if $cmd -c "import sys; assert sys.version_info >= (3, 7)" >/dev/null 2>&1; then
    PYTHON_CMD="$cmd"
    break
  fi
done

if [ -z "$PYTHON_CMD" ]; then
  exit 0
fi
# Force UTF-8 output in case a branch name or model name contains non-ASCII.
export PYTHONIOENCODING=utf-8

script_file="$(mktemp)"
trap 'rm -f "$script_file"' EXIT

cat > "$script_file" <<'PYEOF'
import json, os, subprocess, sys

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

def get(path, default=""):
    cur = data
    for key in path.split("."):
        if not isinstance(cur, dict):
            return default
        cur = cur.get(key)
        if cur is None:
            return default
    return cur

model = get("model.display_name") or "claude"
cwd = get("workspace.current_dir") or get("cwd") or os.getcwd()
ctx_used = get("context_window.used_percentage")
rl_5h = get("rate_limits.five_hour.used_percentage")
rl_7d = get("rate_limits.seven_day.used_percentage")

branch = ""
try:
    branch = subprocess.check_output(
        ["git", "-C", cwd, "branch", "--show-current"],
        stderr=subprocess.DEVNULL,
        timeout=2,
    ).decode().strip()
except Exception:
    branch = ""

def fmt_pct(value, label):
    if value in ("", None):
        return None
    try:
        return "{}:{}%".format(label, int(float(value)))
    except Exception:
        return None

parts = ["[{}]".format(model)]
if branch:
    parts.append(branch)
for seg in (fmt_pct(ctx_used, "ctx"), fmt_pct(rl_5h, "5h"), fmt_pct(rl_7d, "7d")):
    if seg:
        parts.append(seg)

sys.stdout.write(" ".join(parts))
PYEOF

printf '%s' "$input" | $PYTHON_CMD "$script_file" 2>/dev/null || true
