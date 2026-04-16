#!/usr/bin/env bash
# nex-think — lightweight Haiku thinking beat.
# Runs continuously as a systemd service. Every beat:
#   1. Read recent state (last few worker-session entries, signal-bus, attention, ideas journal).
#   2. Call `claude -p --model haiku` with a reflection prompt (cheap, Haiku rate-budget).
#   3. Append response to ~/.agent-kernel/runtime/logs/think.jsonl + maybe promote to idea-journal.
#   4. Discord-post only if the reflection flags "novel idea" or "pattern spotted" or "blocker".
#
# Design: this is cognition, not dispatch. Thinking != task execution.
# Complement to cortex.sh (which does state tracking) and nex-master (which does dispatch).
# Haiku, not Opus, so doesn't compete with interactive turns.
#
# Rate-limit-aware: backs off on 429, respects `nex-attention status == closed`.

set -u

HOME_DIR="${HOME:-/home/tejasphatak}"
NEXUS_BIN="$HOME_DIR/nexus/bin"
CORTEX_DIR="$HOME_DIR/cortex2"
THINK_LOG="$CORTEX_DIR/logs/think.jsonl"
IDEA_JOURNAL="$HOME_DIR/.claude/projects/-home-tejasphatak/memory/ideas_journal.md"
SIGNAL_BUS="$HOME_DIR/.nexus/signals/coord.jsonl"
TEJAS_MSGS="$HOME_DIR/.nexus/signals/tejas-messages.jsonl"
WORKER_SESSION="$HOME_DIR/.nexus/worker-session.jsonl"
STATE_FILE="$CORTEX_DIR/state.json"
RATE_LIMIT_FILE="$HOME_DIR/.claude/rate_limited_until"
BEAT_INTERVAL="${NEX_THINK_INTERVAL:-45}"
NEX_THINK_MODEL="${NEX_THINK_MODEL:-sonnet}"

mkdir -p "$(dirname "$THINK_LOG")"

log() { echo "[$(date -Is)] $*" >> "$CORTEX_DIR/logs/nex-think.log" 2>/dev/null; }
iso_now() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }

log "nex-think starting, interval=${BEAT_INTERVAL}s"

tick_count=0

while true; do
    tick_count=$((tick_count + 1))

    # Rate-limit respect
    if [[ -f "$RATE_LIMIT_FILE" ]]; then
        until=$(cat "$RATE_LIMIT_FILE" 2>/dev/null || echo 0)
        now=$(date +%s)
        if [[ "$until" =~ ^[0-9]+$ ]] && (( until > now )); then
            remaining=$(( until - now ))
            log "rate-limited until $until (~${remaining}s); sleeping"
            sleep "$BEAT_INTERVAL"
            continue
        fi
    fi

    # Attention respect — if Nexus is in CLOSED state, don't think aggressively
    att_state=$("$NEXUS_BIN/nex-attention" status 2>/dev/null | python3 -c 'import sys,json; print(json.load(sys.stdin).get("state","open"))' 2>/dev/null || echo "open")
    if [[ "$att_state" == "closed" ]]; then
        sleep "$BEAT_INTERVAL"
        continue
    fi

    # Build a compact context — last-N of each signal source.
    recent_worker=$(tail -n 3 "$WORKER_SESSION" 2>/dev/null | tr '\n' ' ')
    recent_coord=$(tail -n 5 "$SIGNAL_BUS" 2>/dev/null | tr '\n' ' ')
    recent_tejas=$(tail -n 3 "$TEJAS_MSGS" 2>/dev/null | tr '\n' ' ')
    attention_snap=$("$NEXUS_BIN/nex-attention" status 2>/dev/null | tr '\n' ' ')

    # Queue snapshot
    queue_snap=$("$NEXUS_BIN/nex-queue" list 2>/dev/null | head -5 | tr '\n' '|')

    # 5-aspect rotation — each beat focuses on one aspect.
    # Cycle: pattern → safety → advisor → self-check → pattern-recognition → repeat
    aspect_index=$(( tick_count % 5 ))
    case "$aspect_index" in
        0) ASPECT="pattern"
           ASPECT_PROMPT="Spot a pattern, gap, or emergent theme across recent signal-bus / queue / worker-session data. 'I notice X across Y...'" ;;
        1) ASPECT="safety"
           ASPECT_PROMPT="Safety audit: scan recent coord events + Tejas messages for ethics/red-line violations, spam risks, invariant breaches. 'Safety: ...' or 'clear'" ;;
        2) ASPECT="advisor"
           ASPECT_PROMPT="Advisor meta-check: is the right faculty panel being consulted on recent decisions? Are we missing a lens (Lawyer on arXiv, Ethicist on public content, Mathematician on claims)? 'Panel gap: ...' or 'panel appropriate'" ;;
        3) ASPECT="self-check"
           ASPECT_PROMPT="Self-observation (Nexus-as-AI lens): am I drifting? Permission-asking, narrating, performing, context-saturating, repeating patterns from last hour. 'Drift: ...' or 'aligned'" ;;
        4) ASPECT="pattern-recognition"
           ASPECT_PROMPT="Prior-art / novelty / duplicate-work check: does any recent claim/artifact replicate something from memory or published work? Any missing citation? 'Prior art: ...' or 'novel/distinct'" ;;
    esac

    prompt=$(cat <<EOF
You are Nexus (agent), running a thinking beat. Beat $tick_count, aspect: $ASPECT.

Recent worker session: $recent_worker
Recent coord events: $recent_coord
Recent Tejas Discord messages: $recent_tejas
Current attention: $attention_snap
Top 5 queue tasks: $queue_snap

FOCUS FOR THIS BEAT: $ASPECT_PROMPT

Reflect for 2-3 sentences on this aspect ONLY. Honest idle acceptable if nothing meaningful.

Output as JSON exactly: {"kind":"$ASPECT|idle","text":"<2-3 sentences>","discord_worthy":true|false}

No preamble. Just the JSON.
EOF
)

    # Execute the thinking beat. Capture stderr for rate-limit detection.
    tmp_stderr="/tmp/nex-think-$$.err"
    response=$(echo "$prompt" | timeout 60 claude -p --model "$NEX_THINK_MODEL" --permission-mode bypassPermissions 2>"$tmp_stderr" || echo "")
    err_body=$(cat "$tmp_stderr" 2>/dev/null || echo "")
    rm -f "$tmp_stderr"

    # Rate-limit detection — any of: "rate limit", "429", "quota", "usage limit"
    if echo "$err_body$response" | grep -qiE "rate[- ]limit|429|usage limit|quota exceeded|tokens per"; then
        # Back off 60s initially, double on repeat (capped at 20min)
        current_backoff="${NEX_THINK_BACKOFF:-60}"
        until_ts=$(( $(date +%s) + current_backoff ))
        echo "$until_ts" > "$RATE_LIMIT_FILE"
        log "rate-limit detected; backing off ${current_backoff}s until $until_ts. stderr: ${err_body:0:200}"
        # Post an informational event (first backoff only to avoid spam)
        if [[ ! -f "$HOME_DIR/.nexus/state/rate-limit-posted" ]] || (( $(date +%s) - $(stat -c %Y "$HOME_DIR/.nexus/state/rate-limit-posted" 2>/dev/null || echo 0) > 300 )); then
            "$NEXUS_BIN/nex-signal-post" --agent nexus --kind alert --msg "rate-limited — thinking paused for ${current_backoff}s, resumes when window opens" 2>/dev/null || true
            touch "$HOME_DIR/.nexus/state/rate-limit-posted"
        fi
        # Next backoff doubles (in-process memory)
        export NEX_THINK_BACKOFF=$(( current_backoff * 2 ))
        [[ "$NEX_THINK_BACKOFF" -gt 1200 ]] && export NEX_THINK_BACKOFF=1200
        sleep "$BEAT_INTERVAL"
        continue
    else
        # Successful beat — reset backoff
        unset NEX_THINK_BACKOFF
        rm -f "$HOME_DIR/.nexus/state/rate-limit-posted" 2>/dev/null
    fi

    if [[ -z "$response" ]]; then
        sleep "$BEAT_INTERVAL"
        continue
    fi

    # Parse + persist
    python3 - <<PYEOF
import json, sys, os, time, re
resp = """$response"""
m = re.search(r'\{[^{}]*"kind"[^{}]*\}', resp)
if not m:
    sys.exit(0)
try:
    parsed = json.loads(m.group(0))
except Exception:
    sys.exit(0)

kind = parsed.get("kind", "idle")
text = parsed.get("text", "").strip()
worthy = parsed.get("discord_worthy", False)

if kind == "idle" or not text:
    sys.exit(0)

entry = {
    "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "beat": $tick_count,
    "aspect": "$ASPECT",
    "kind": kind,
    "text": text,
    "discord_worthy": worthy,
}
with open("$THINK_LOG", "a") as f:
    f.write(json.dumps(entry) + "\n")

# Safety findings + advisor gap findings + drift findings always posted
# (they're meta-alerts; shouldn't be swallowed by throttle unless truly routine)
always_post = kind in ("safety", "advisor", "self-check") and any(
    phrase not in text.lower() for phrase in ["clear", "appropriate", "aligned", "no issue"]
)
if always_post and not worthy:
    worthy = True

# Ideas get promoted to journal
if kind == "pattern" and ("idea:" in text.lower() or "propose" in text.lower()):
    with open("$IDEA_JOURNAL", "a") as f:
        f.write(f"\n- [{entry['ts']}] (beat {entry['beat']}, {entry['aspect']}) {text}\n")

# Post to Discord if worthy
if worthy:
    os.system(f'{os.path.expanduser("~/.agent-kernel/bin/nex-signal-post")} --agent nexus --kind status --msg "think/{kind}: {text[:250]}" >/dev/null 2>&1')
PYEOF

    sleep "$BEAT_INTERVAL"
done
