#!/usr/bin/env bash
# nex-autonomous-beat — attention-aware self-dispatch.
# Invoked on scheduler ticks (int.*) when Nexus is idle.
# Reads nex-queue for open tasks, picks the highest-priority unclaimed one,
# announces focus via nex-attention + Discord, and dispatches work.
#
# Flow:
#   1. Check attention. If CLOSED, do nothing (deep focus mode).
#   2. Skip if interactive session active (don't steal Tejas's quota).
#   3. List open unclaimed high/urgent-priority tasks from nex-queue.
#   4. If none → idle exit.
#   5. If found → nex-attention gate (with task title as focus, 30-min window).
#   6. Claim task in queue (posts to Discord).
#   7. Dispatch via nex-wake → nex-master → nex-tick will pick it up.
#   8. nex-tick runs, posts outcome to Discord, writes back to queue.
#
# Invoked by: cron (every 15m) OR nex-scheduler events.

set -u
NEXUS_BIN="$HOME/nexus/bin"
CLAUDE_LOCK="$HOME/.claude/claude.lock"
LOG="$HOME/.nexus/state/autonomous-beat.log"

mkdir -p "$(dirname "$LOG")"
log() { echo "[$(date -Is)] $*" >> "$LOG" 2>/dev/null; }

# 1. Skip if interactive session is active (lock held by claude-resilient)
if [ -f "$CLAUDE_LOCK" ] && kill -0 "$(cat "$CLAUDE_LOCK" 2>/dev/null)" 2>/dev/null; then
    log "skip: interactive session active"
    exit 0
fi

# 2. Check attention — can we work at all?
att_state=$("$NEXUS_BIN/nex-attention" status 2>/dev/null | python3 -c 'import sys,json; print(json.load(sys.stdin).get("state","open"))' 2>/dev/null)
if [ "$att_state" = "closed" ]; then
    log "skip: attention CLOSED"
    exit 0
fi

# 3. Find a task to work on. Priority order: urgent > high > normal > low.
# Only pick unclaimed (no assigned_to) open tasks owned by nobody.
candidate=$("$NEXUS_BIN/nex-queue" list --status open 2>/dev/null | grep -E '^\S+ \[(urgent|high)\s*\]' | head -1)
if [ -z "$candidate" ]; then
    candidate=$("$NEXUS_BIN/nex-queue" list --status open 2>/dev/null | head -1)
fi
if [ -z "$candidate" ]; then
    log "skip: no open tasks"
    exit 0
fi

task_id=$(echo "$candidate" | awk '{print $1}')
task_title=$(echo "$candidate" | sed -E 's/^\S+ \[[^]]+\] \S+\s+//' | cut -c1-80)

# Thrash-suppression: if this task has been claimed + re-blocked N+ times in the
# last hour, escalate to human alert instead of re-claiming (feedback_no_spam +
# self-check aspect of nex-think flagged this).
THRASH_THRESHOLD=3
THRASH_WINDOW_MIN=60
thrash_count=$("$NEXUS_BIN/nex-queue" show "$task_id" 2>/dev/null | python3 -c "
import json, sys, time
try:
    task = json.loads(sys.stdin.read())
except Exception:
    print(0)
    sys.exit(0)
cutoff = time.time() - $THRASH_WINDOW_MIN * 60
count = 0
for upd in task.get('updates', []):
    if upd.get('event') != 'claim':
        continue
    try:
        ts = time.mktime(time.strptime(upd.get('at',''), '%Y-%m-%dT%H:%M:%SZ'))
    except Exception:
        continue
    if ts >= cutoff:
        count += 1
print(count)
" 2>/dev/null || echo 0)

if [ "$thrash_count" -ge "$THRASH_THRESHOLD" ]; then
    log "thrash detected: $task_id claimed $thrash_count times in ${THRASH_WINDOW_MIN}min — escalating, not re-claiming"
    # One-shot alert to Tejas (dedup in nex-signal-post prevents spam from repeated detections)
    "$NEXUS_BIN/nex-signal-post" \
        --agent nexus --kind alert \
        --msg "thrash: $task_id claimed ${thrash_count}x in ${THRASH_WINDOW_MIN}min without completing. needs human review (blocker persists, auto-retry is not converging). title: $task_title" \
        --mention-tejas \
        --urgent 2>/dev/null || true
    # Release attention gate so other work can proceed
    "$NEXUS_BIN/nex-attention" open >/dev/null 2>&1
    exit 0
fi

# 4. Gate attention with this task as focus (30-min window)
"$NEXUS_BIN/nex-attention" gate --focus "$task_title" --for 30 >/dev/null 2>&1 || true

# 5. Claim the task in shared queue (posts to Discord)
"$NEXUS_BIN/nex-queue" claim "$task_id" >/dev/null 2>&1 || {
    log "claim failed for $task_id — may already be claimed"
    "$NEXUS_BIN/nex-attention" open >/dev/null 2>&1
    exit 1
}

log "claimed $task_id: $task_title"

# 6. Dispatch work via nex-wake (nex-master picks up, nex-tick executes)
"$NEXUS_BIN/nex-wake" \
    --source "int.autonomous-beat" \
    --priority normal \
    "Queue task $task_id: $task_title. Work this task. See ~/webmind-research/shared-queue/tasks.jsonl for full detail via 'nex-queue show $task_id'. When done, call nex-queue done $task_id --notes '<one-line-outcome>' and nex-attention open." >/dev/null 2>&1

log "dispatched wake event for $task_id"
exit 0
