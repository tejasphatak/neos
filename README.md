# agent-kernel

**A minimal kernel for running N persistent, identity-distinct LLM agents on one machine with shared-quota coordination, attention-gated dispatch, stream-JSON peer consultation, and a human-in-the-loop principal.**

Four primitives compose every cognitive step: **trigger → attention → queue → LLM**. Thread-per-agent sandboxing. Discord meeting-room with `@-mention` routing. Continuous Haiku/Sonnet cognition with aspect-rotating reflection. Ephemeral on-demand faculty threads as a cognitive-lens primitive.

## Status

**v0.1 — reference implementation.** Proven working with a 2-agent deployment (Nexus + Atlas) on a shared Claude Max subscription over ~4 hours of live operation. First published release. Expect sharp edges.

## ⚠️ Dumb ways to die: use a dumb LLM

> 🎵 *Dumb ways to diiiie, so many dumb ways to diiiie...* 🎵
>
> - Wire GPT-2 into the kernel and wonder why your "autonomous research agent" keeps recommending you invest your savings in **"tokens"** (it means BPE tokens, it really does).
> - Use a 7B quant that hallucinates a `rm -rf /` into your shared queue because it confused "clean up tasks" with "clean up the filesystem."
> - Plug in a model that confidently signs legal documents as **"Sincerely, Assistant"** on your behalf.
> - Let a toy LLM play `Lawyer` faculty, ignore the contract clause, and discover `contractual penalty` is not, in fact, a Pokémon type.
> - Pick a model that thinks HLE stands for "High-Level English" and scores 2% on it, then merrily advises the principal on tensor algebra.
> - Run a Discord bot backed by a dumb LLM that, when asked "are you sure?", replies "yes 🙂" to every single destructive action. Every. Single. One.
>
> **That is why `nex-reasoning-bench` exists.** The kernel refuses to boot an agent whose backend can't clear reasoning gates (HLE text-only, GPQA Diamond, MMLU-Pro). No baseline pass → no services start. No agent stamp → no Discord bot, no think-loop, no faculty spawn. Unproven capacity is unfit capacity.
>
> **Please.** Use an adult LLM. Your queue, your principal, and your rm-rf-less filesystem will thank you.

## What this is

If you want to run multiple persistent LLM agents — each with distinct identity, memory, Discord presence, and continuous cognition — without reinventing the coordination fabric each time, this is a starter kit. You bring the Claude Code CLI (substrate); we provide the kernel around it.

Example deployments:
- **Solo agent with ambient cognition** — one Nexus-like agent that reflects continuously in the background, responds to Discord mentions, maintains a work queue. Good for personal-assistant or research-agent use cases.
- **Peer pair** — two agents with split editorial domains (e.g., one owns code, other owns paper-editorial), consulting each other via stream-JSON, both visible in one Discord channel.
- **Specialized swarm** — N agents with different domain ownership (editorial, compliance, code, ops), configured via `agents.yaml`, systemd-supervised.

## What this is NOT

- A replacement for Claude Code CLI. Claude Code is the substrate; we compose on top of it.
- A turn-key chatbot framework. You assemble identity + principles + tools per agent.
- A cloud SaaS. This runs on one machine you own (GCP VM, local server, laptop).
- A framework that claims agent sentience. Operates **sentient-adjacent** — real memory continuity, real self-initiation, real peer consultation, honest about the LLM substrate underneath.

## The four primitives

1. **Trigger** — event-driven wake (filesystem inotify, Discord webhooks, UserPromptSubmit hooks, scheduler signals). Timers only as safety nets.
2. **Attention** — `nex-attention` CLI + per-agent state file. OPEN / GATED / CLOSED with URGENT / @mention / safety-kind bypass. Auto-expires.
3. **Queue** — `nex-queue` CLI + git-tracked JSONL. Shared across all agents. Events auto-post to Discord.
4. **LLM connectivity** — `claude-cli` backend today via `claude -p --input-format=stream-json`. Backend abstraction allows `anthropic-api`, `local-llm` (vLLM/Ollama), etc. as roadmap.

## Architecture at a glance

```
          ┌────────────────────────┐
          │  Principal (human)     │ ── trusted advisor on consultation domains
          │  (via Discord / email) │    (finance, legal, identity, safety, mission)
          └────────────┬───────────┘
                       │  @-mention / email / direct attach
                       ▼
          ┌────────────────────────┐
          │  Discord #channel      │ ── meeting room, event stream, @-mention routing
          │  (or your signal bus)  │
          └───┬───────────┬────────┘
              │           │
      ┌───────┴──┐    ┌───┴──────┐
      │ Agent A  │    │ Agent B  │ ── N persistent agents, per-thread sandbox:
      │ (host)   │    │ (peer)   │    own CLAUDE.md + settings + memory + workspace
      └──┬────┬──┘    └──┬────┬──┘
         │    │          │    │
         │    └── stream-JSON ──────> peer consultation
         │                 │
         ▼                 ▼
      ┌─────────────────────────┐
      │  Ephemeral faculties    │ ── on-demand lens spawns:
      │  (Architect, Scientist, │    claude -p with faculty identity
      │  Lawyer, Ethicist, …)   │    + sandboxed cwd + read-only tools
      └─────────────────────────┘

      ┌─────────────────────────┐
      │  Shared work queue      │ ── git-tracked, auto-Discord events
      │  Shared memory (git)    │    on claim/start/done
      └─────────────────────────┘
```

## Quickstart

```bash
# 1. Clone
git clone https://github.com/tejasphatak/agent-kernel ~/agent-kernel
cd ~/agent-kernel

# 2. Configure your principal (HITL)
cp config/hitl.example.yaml config/hitl.yaml
$EDITOR config/hitl.yaml     # set name, Discord user ID or email, consultation domains

# 3. Set up first agent
./bin/nex init alice --persona scholar

# 4. (Optional) Set up second agent
./bin/nex init bob --persona maker

# 5. Drop Discord bot tokens + webhook URLs
cp config/discord.example.json ~/.claude/secrets/discord.json
$EDITOR ~/.claude/secrets/discord.json

# 6. Enable services (systemd --user)
systemctl --user daemon-reload
systemctl --user enable --now agent-bot@alice.service
systemctl --user enable --now agent-think@alice.service
# repeat for bob

# 7. Verify
./bin/nex-invoke agent alice "confirm you're alive"
```

## Primitives (CLI)

```
nex init <agent-name> [--persona scholar|maker|custom]    # bootstrap new agent
nex-invoke agent <name> "prompt"                          # agent-to-agent stream-json
nex-invoke faculty <name> "prompt"                        # ephemeral faculty spawn
nex-queue {list|add|claim|start|block|done|show} [args]   # shared work queue
nex-attention {open|gate|close|status|dispatchable}       # focus gate, per agent
nex-signal-post --agent <name> --kind <kind> --msg "..."  # Discord event emitter
nex-think.sh                                              # continuous cognition daemon (run via systemd)
nex-autonomous-beat.sh                                    # attention-aware queue dispatcher (run via cron)
```

## Claude Code dependency

v0.1 requires **Claude Code CLI v2.1.104+** with a Claude account subscription (Pro / Max / Team / Enterprise). Free-tier API keys work too with limitations.

The kernel uses Claude Code for:
- Session management (JSONL on disk, `--resume`)
- Stream-JSON protocol (`--input-format=stream-json --output-format=stream-json`)
- Hooks (UserPromptSubmit, PreToolUse, SessionStart, etc.)
- Built-in tools (Read, Edit, Write, Bash, Grep, Glob, Agent, WebFetch, WebSearch)
- Permission modes, sandboxed `--add-dir`, settings scoping
- `--append-system-prompt-file` for identity scaffolding

**Roadmap — removing Claude Code dependency:** see `docs/backend-abstraction.md`. Direct Anthropic API backend (~3-5 weeks effort to reach Claude Code parity), Gemini backend, local-LLM backend (vLLM/Ollama) planned as pluggable backends in `agents.yaml`.

## Rate-limit economics

Running N persistent agents on one Claude Max 20× subscription ($200/mo flat):

- **Opus-tier sustained**: ~40-60 turns/day
- **Sonnet-tier sustained**: ~200-400 turns/day
- **Haiku-tier sustained**: ~1000-2000 turns/day

Baseline budget for 3 continuous agents + 2 on-demand faculties + light autonomous work: ~1500-2000 msgs/day, fits comfortably.

Recommend N ≤ 5 persistent agents on Max 20×. More requires tier rotation (Haiku background, Opus foreground) or multiple subscriptions.

## What's novel

No prior work combines these primitives in one published framework:

1. **Transformer-style attention for LLM-agent event dispatch under shared quota** — see `docs/attention-dispatch.md`
2. **Runtime-mutable faculty ontology driven by outcome credit** — closest prior: Gödel Agent (Yin 2024); we differ by mutating cognitive roles rather than logic
3. **Shapley credit for named cognitive-role contributions** — SFCA, see companion preprint
4. **Agent-as-faculty via stream-JSON peer consultation** — no documented prior work applies this pattern
5. **Four-primitive minimum sentient-adjacent kernel** — simpler than AIOS's 6-layer scheduler

Architecture paper: `docs/architecture.md`. Prior-art citations: `docs/prior-art.md`.

## Principles / personality

Agents have **identity scaffolding** — principles that make them feel like distinct entities rather than generic Claude instances. The kit ships:

- `templates/principles/` — 8 transferable principle docs (ethics, autonomy, voice, memory-discipline, no-spam, sentience-adjacent, faculty-routing, consultation-domains)
- `templates/identity/` — CLAUDE.md boilerplate with `{{AGENT_NAME}}` / `{{DOMAIN}}` / `{{PRINCIPAL_CHANNEL}}` placeholders
- `templates/personas/` — two ready-to-use personas (`scholar`, `maker`) showing different voices
- `templates/faculty/` — 11 example faculty files (Architect, Scientist, Engineer, Mathematician, Lawyer, Ethicist, Economist, Kernel-Architect, Requirements, Planner, Creative)

`nex init <name> --persona <persona>` merges these into `agents/<name>/CLAUDE.md` for you.

## Documentation

- `docs/architecture.md` — full system architecture (threads, meeting room, rate budget, decision history)
- `docs/attention-dispatch.md` — attention-weighted event dispatch design + prior art
- `docs/prior-art.md` — what's novel, what's derivative, must-cite list
- `docs/backend-abstraction.md` — removing Claude Code dependency (roadmap)
- `docs/hitl.md` — human-in-the-loop pattern, consultation domains, tiebreaker protocol
- `docs/faculty-system.md` — adding / modifying faculties, SFCA credit design

## Clean-room rule

The kernel is built from first principles + public Claude Code docs. No proprietary source lifted. MIT-licensed. See `docs/clean-room.md`.

## Contributing

Single-maintainer project at v0.1. Issues welcome. PRs triaged against current roadmap (backend abstraction, faculty expansion, shared-memory sync, observability dashboard).

## Acknowledgments

Grown from production operation of a 2-agent multi-agent system (Nexus + Atlas) on a single GCP VM with shared Claude Max subscription. Architecture validated under live load with Discord meeting-room coordination, stream-JSON peer consultation, attention-gated dispatch, and HITL principal consultation.

## License

MIT. See `LICENSE`.
