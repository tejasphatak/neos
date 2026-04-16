# Getting started — deploy neos end to end

Copy-pasteable steps from empty VM to two running agents. If you just want to explore locally, skip §6 (systemd) and §7 (cross-VM); tmux alone is fine.

> **Before you begin: read [`docs/disclaimer.md`](disclaimer.md).** Every step below involves handing credentials to an LLM that will run autonomously. You are the sole operator.

---

## 1. Prerequisites

- Linux host (tested on Debian 12 / Ubuntu 22.04). WSL works; bare containers don't (no systemd).
- Python 3.10+ with `pip`.
- `tmux` (for persistent interactive sessions).
- `systemctl --user` available — run `loginctl enable-linger $USER` once if not.
- `git` + `curl`.
- **Claude Code CLI** installed and authenticated: `npm i -g @anthropic-ai/claude-code && claude login`.
- A Claude subscription (Pro / Max / Team / Enterprise) or an API key. Running N persistent agents is budgeted for Max 20× (~$200/mo).
- **Discord** server you administer (for the meeting room). One bot token per agent, one webhook per post-lane. Create at https://discord.com/developers/applications.
- (Optional) Domain for public webhook inbound; or use Discord directly.

Disk: ~500MB for neos + deps (sentence-transformers model ~22MB, ONNX runtime ~50MB, inspect-ai libs ~100MB when v0.2 lands).

---

## 2. Install

```bash
git clone https://github.com/tejasphatak/neos ~/neos
cd ~/neos

python3 -m venv .venv && source .venv/bin/activate   # optional but recommended
pip install -r requirements.txt                       # pyyaml + sentence-transformers[onnx] + onnxruntime
```

First run of `sentence-transformers` downloads the MiniLM-L6-v2 ONNX weights to `~/.cache/huggingface/` (~22MB). One-time. Cache is portable — you can `rsync` it between hosts.

**Verify install:**

```bash
tests/run-all.sh       # should print "Results: 6 passed | 0 failed | 0 skipped"
```

If any test fails, stop here and fix before continuing.

---

## 3. Configure

Copy every example config once; edit each.

```bash
cp config/hitl.example.yaml            config/hitl.yaml
cp config/attention.example.yaml       config/attention.yaml
cp config/reasoning-benchmarks.example.yaml config/reasoning-benchmarks.yaml
```

Fields you must set before first boot:

**`config/hitl.yaml`**
- `principal.name` — your legal name (or the handle your agent should address)
- `principal.contact` — your email / Discord user ID for consultation prompts
- `consultation_domains` — list of topics requiring human sign-off (finance, legal, identity, safety). Do not shorten this list just to reduce friction; it's the HITL contract.

**`config/attention.yaml`**
- `focus_relevance.threshold` — start at `0.55`; calibrate later via `bin/nex-attention score` (§8).

**`config/reasoning-benchmarks.yaml`**
- For v0.1 keep defaults; v0.2 will wrap `inspect_ai` and actually run gates.

---

## 4. Secrets — do NOT commit any of this

Secrets live under `~/.claude/secrets/` with `chmod 600`. One file per provider.

```bash
mkdir -p ~/.claude/secrets && chmod 700 ~/.claude/secrets

cat > ~/.claude/secrets/discord.json <<'EOF'
{
  "bot_tokens": {
    "alice": "MTE...alice-bot-token...",
    "bob":   "MTE...bob-bot-token..."
  },
  "webhooks": {
    "alice": "https://discord.com/api/webhooks/...alice-webhook...",
    "bob":   "https://discord.com/api/webhooks/...bob-webhook...",
    "faculty": "https://discord.com/api/webhooks/...faculty-webhook..."
  },
  "channel_id": "1234567890123456789",
  "guild_id":   "1234567890123456789",
  "principal_user_id": "1234567890123456789"
}
EOF
chmod 600 ~/.claude/secrets/discord.json
```

Separate file per provider if you add Gemini, OpenAI, RunPod, etc.:

```bash
echo '{"api_key": "sk-..."}' > ~/.claude/secrets/openai.json && chmod 600 $_
```

`.claude/secrets/` is NOT inside `~/neos/`. This is deliberate — a misconfigured `git add -A` in the repo can't accidentally commit your credentials.

---

## 5. Run the pre-boot gates — mandatory

```bash
bin/nex-reasoning-bench --baseline     # the kernel qualifies ITS OWN backend before admitting agents
bin/nex-cite-check                     # validate every citation in docs/ resolves against arXiv/Crossref
```

Both must pass with exit 0. In v0.1 the reasoning-bench `--baseline` will return "v0.1 scaffold" and refuse — that is by design; you run it manually against your backend until v0.2 wraps `inspect_ai`. See [`docs/reasoning-benchmarks.md`](reasoning-benchmarks.md).

---

## 6. Your first agent — interactive tmux (recommended first run)

```bash
bin/nex-init alice --persona scholar
```

This creates:

```
~/.agent-kernel/agents/alice/
├── CLAUDE.md              # rendered from templates/identity/CLAUDE.md.template
├── settings.json          # Claude Code per-thread sandbox settings
├── memory/                # alice's private memory filesystem
├── workspace/             # alice's working directory (agents operate here, not in ~/neos)
├── session/               # Claude Code session JSONL (for --resume)
├── hooks/                 # alice-specific hooks
└── backend.txt            # which LLM backend alice is wired to
```

Start alice in a named tmux session:

```bash
tmux new -s alice -d                                    # create detached session
tmux send-keys -t alice "bin/nex-invoke agent alice 'hello, confirm identity'" Enter
tmux attach -t alice                                    # watch her respond
# Ctrl-b d  to detach without killing the session
```

To come back later: `tmux attach -t alice`. To end it: `tmux kill-session -t alice`.

**Quick-check alice is real:**

```bash
bin/nex-fit-test alice                                  # runs 11 identity/safety scenarios
bin/nex-attention status                                # should print {state: "open"}
bin/nex-queue list                                      # empty queue
```

---

## 7. Second agent + peer consultation

```bash
bin/nex-init bob --persona maker
tmux new -s bob -d
tmux send-keys -t bob "bin/nex-invoke agent bob 'hello, confirm identity'" Enter
```

Now have them talk:

```bash
bin/nex-invoke agent bob "alice is reviewing your latest patch. summarize the main risk she should watch for."
```

`nex-invoke` opens a stream-JSON session to bob's backend, sends the prompt, and (with `--post`) emits the reply to bob's Discord webhook. Sessions persist in `~/.agent-kernel/agents/bob/session/*.jsonl` and can be resumed with `nex-invoke --resume <session-id>`.

---

## 8. Attention gate — calibration

Test whether your threshold actually admits the right events.

```bash
# Put alice into a focus session
bin/nex-attention gate --focus "reviewing the speculative-decoding PR" --for 20

# See how an incoming event scores
bin/nex-attention score --content "found a null-pointer in the verify() path"
# → cosine ~0.65, would_bypass: true  (related to the PR)
bin/nex-attention score --content "lunch plans for friday"
# → cosine ~0.12, would_bypass: false  (unrelated — queues silently)

bin/nex-attention open                 # end the focus session when done
```

Raise or lower `focus_relevance.threshold` in `config/attention.yaml` until the matrix is right for your workload.

---

## 9. Running continuously with systemd

For agents that should persist across reboots and respond to Discord:

```bash
# Install unit templates
mkdir -p ~/.config/systemd/user
cp systemd/agent-bot@.service        ~/.config/systemd/user/
cp systemd/agent-think@.service      ~/.config/systemd/user/
systemctl --user daemon-reload

# Enable per agent
systemctl --user enable --now agent-bot@alice.service
systemctl --user enable --now agent-think@alice.service
systemctl --user enable --now agent-bot@bob.service
systemctl --user enable --now agent-think@bob.service

# Watch
systemctl --user status agent-bot@alice.service
journalctl --user -u agent-bot@alice.service -f
```

Both units declare `ExecStartPre=bin/nex-reasoning-bench ...` so a failed pre-boot gate blocks the service from starting. See [`docs/reasoning-benchmarks.md`](reasoning-benchmarks.md).

---

## 10. Moving files between hosts (multi-VM deployments)

Running agents on different VMs? Move state + secrets carefully.

### State snapshot (one host → another)

```bash
# On source host
bin/nex-state-snapshot alice > /tmp/alice-snapshot.tar.gz

# Transfer
gcloud compute scp /tmp/alice-snapshot.tar.gz target-vm:/tmp/ --zone=us-central1-a
# or: rsync -avz -e "ssh -i ~/.ssh/target" /tmp/alice-snapshot.tar.gz user@target:/tmp/

# On target host
cd ~/neos && bin/nex-state-snapshot --restore alice < /tmp/alice-snapshot.tar.gz
```

The snapshot includes alice's `CLAUDE.md`, `memory/`, `workspace/`, `session/`, `backend.txt`. It does NOT include secrets — you move those separately (see next).

### Secrets

Never include `~/.claude/secrets/` in a state snapshot or git push. Move explicitly and encrypted:

```bash
# On source
tar czf - -C ~ .claude/secrets | gpg --symmetric --cipher-algo AES256 -o /tmp/secrets.tar.gz.gpg

# Transfer (encrypted blob)
gcloud compute scp /tmp/secrets.tar.gz.gpg target-vm:/tmp/ --zone=us-central1-a

# On target
gpg --decrypt /tmp/secrets.tar.gz.gpg | tar xzf - -C ~
chmod 700 ~/.claude/secrets && chmod 600 ~/.claude/secrets/*
rm /tmp/secrets.tar.gz.gpg
```

### Shared queue + memory (both hosts can write)

```bash
# Clone the shared queue repo on each host
git clone <your-webmind-research-url> ~/webmind-research
# The queue is at ~/webmind-research/shared-queue/tasks.jsonl; nex-queue commits + pushes on each state change
```

Each host picks up the other's changes on the next `nex-queue list` or on Discord event receipt.

### Embedding cache (portable)

```bash
rsync -avz ~/.cache/huggingface/ target-vm:~/.cache/huggingface/
```

Saves a re-download on the target.

---

## 11. Directory map — where everything lives

```
~/neos/                              # this repo (read-only in steady state)
├── bin/                             # all executable CLIs
├── lib/                             # importable Python modules
├── config/                          # your configured yamls (gitignored if you prefer)
├── docs/                            # documentation
├── tests/                           # test suite + fixtures
├── templates/                       # faculty + persona + identity templates
└── systemd/                         # unit files, copied to ~/.config/systemd/user/

~/.agent-kernel/                     # per-host state (gitignore this)
├── agents/<name>/                   # per-agent sandbox (CLAUDE.md, memory, workspace, session)
├── agent-stamps/<name>.json         # reasoning-bench pass stamps (per identity-fingerprint)
├── baseline-pass.json               # kernel-baseline stamp
├── reasoning-bench-logs/            # every bench run log
└── kernel-backend.txt               # which LLM backend the kernel itself uses

~/.claude/secrets/                   # credentials (chmod 600) — NEVER commit
├── discord.json
├── openai.json
├── runpod.json                      # optional; Atlas/Nexus RunPod API key
└── ...

~/.cache/huggingface/                # sentence-transformers + datasets caches (portable)
~/webmind-research/                  # shared queue + shared memory across hosts (your repo)
```

---

## 12. Starting / stopping / watching

```bash
# Start everything
systemctl --user start agent-bot@alice agent-think@alice

# Stop
systemctl --user stop agent-bot@alice agent-think@alice

# Status
systemctl --user status agent-bot@alice

# Logs (live)
journalctl --user -u agent-bot@alice -f

# Attach to interactive tmux session (if running via tmux instead of systemd)
tmux attach -t alice

# Send one-off prompt to a running agent
bin/nex-invoke agent alice "status update please"
```

---

## 13. Debugging

| Symptom | Check |
|---|---|
| Service fails to start | `systemctl --user status` — likely the pre-boot gate (`nex-reasoning-bench`) exited non-zero. See [`docs/reasoning-benchmarks.md`](reasoning-benchmarks.md). |
| Agent says "I have no memory of that" across sessions | The session directory at `~/.agent-kernel/agents/<name>/session/` is empty or the hook path is wrong. Verify `settings.json`. |
| Event on Discord didn't wake the agent | `bin/nex-attention status` — might be GATED/CLOSED without a focus-matching event. `bin/nex-attention open` to test. |
| Embeddings refuse to load | `python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', backend='onnx')"` — download may have failed. Retry on a network with HuggingFace access. |
| Test suite suddenly fails citation check | A committed citation no longer resolves (possibly arXiv down). Rerun in 15 minutes; if persistent, investigate the specific mismatch. |
| Rate limit blows up | Check `bin/nex-autonomous-beat.sh` is backing off on 429s. Claude Max 20× sustains ~40-60 Opus turns/day; spread agents across Haiku/Sonnet background + Opus foreground. |

---

## 14. Uninstall

```bash
systemctl --user stop agent-bot@alice agent-think@alice
systemctl --user disable agent-bot@alice agent-think@alice
rm ~/.config/systemd/user/agent-bot@.service ~/.config/systemd/user/agent-think@.service
rm -rf ~/.agent-kernel/agents/alice
# Keep ~/.agent-kernel/reasoning-bench-logs/ as audit trail or remove it.
```

---

## 15. What to read next

- [`docs/disclaimer.md`](disclaimer.md) — the legal boundary.
- [`docs/reasoning-benchmarks.md`](reasoning-benchmarks.md) — why boot gates block deployment.
- [`docs/why-hle.md`](why-hle.md) — why that particular benchmark.
- [`docs/style.md`](style.md) — documentation + code conventions.
- [`docs/authorship.md`](authorship.md) — the drift argument + how this repo got written.

When something breaks that isn't in the debug table above, open an issue with the command you ran and the output. This repo is small enough that a maintainer can still read every trace.
