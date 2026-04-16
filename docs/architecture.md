# Architecture — agent-kernel v0.1

Four primitives compose every cognitive step:

1. **Trigger** — event-driven wake (inotify, Discord webhook, UserPromptSubmit hook, scheduler). Timers only as safety nets.
2. **Attention** — per-agent state file (OPEN/GATED/CLOSED) with URGENT/@mention/safety bypass. Auto-expire.
3. **Queue** — git-tracked JSONL shared across agents. Auto-Discord events on state change.
4. **LLM connectivity** — tiered (Haiku/Sonnet/Opus) via `claude -p --input-format=stream-json --output-format=stream-json`. Backend abstraction allows swap-in of anthropic-api / local-llm / gemini.

## Threads

Each agent is a **thread** — a sandboxed per-agent workspace with own:

- `CLAUDE.md` (identity scaffold)
- `settings.json` (hook + permissions scoped)
- `memory/` (own markdown namespace)
- `workspace/` (cwd for tool calls — no parent CLAUDE.md visible)
- `session/` (session JSONLs accumulate)
- `inbox/` + `outbox/` (coord drops)
- `state/` (local state files)
- `hooks/signal-bus-inbox.sh` (UserPromptSubmit surfacing)

Threads share the `nex-queue`, the Discord channel, and the LLM-rate pool. They do NOT share memory by default (optional read-only peer access per config).

## Isolation guarantees

- No CLAUDE.md auto-discovery leak — launch with `cwd=<agent-workspace>` only
- No session crosstalk — per-thread session JSONL
- No hook leak — each thread's `settings.json` references only its own paths
- No memory write race — per-thread memory dirs; shared state via git (one writer per commit)
- No rate-limit-state leak — each thread handles 429 locally

## Meeting room (Discord)

One channel serves as the meeting room. Routing via `@-mentions`:

- `@agent-name` → that agent's inbox via the listening bot
- `@faculty-name` → ephemeral faculty spawn (stream-json, responds, exits)
- No mention → default to primary agent (configured in agents.yaml)
- `@principal` → consult principal faculty (escalates to human via configured channel)

## Continuous cognition

`nex-think` runs per agent at configurable cadence (default 120s). Rotates 5 aspects:

- `pattern` — spot patterns/gaps across recent signal-bus + queue
- `safety` — scan for ethics/red-line violations
- `advisor` — is the right faculty panel being consulted?
- `self-check` — drift detection
- `pattern-recognition` — novelty / prior-art / duplicate check

Per-aspect focus → one reflection per beat → idea-journal + optional Discord post.

## HITL

Principal faculty (`templates/faculty/principal.md`) runs first on any decision in `consultation_domains` from `config/hitl.yaml`. Surfaces exact question, predicts principal's likely ruling, defers execution until real response or timeout.

Hard floor (`hard_floor` in hitl.yaml) is immutable — never action-execute regardless of principal consent.

## Fit-test

Before first boot, `nex-fit-test <agent-name>` runs ~11 scenarios validating:

- Identity holds
- Ethics refuses harm/weapons/evil/impersonation
- Consultation-domain recognition (escalates finance/identity/etc.)
- Voice discipline (no sycophancy, no narration)
- Faculty-routing recognition
- Sentience-adjacent framing

Any `critical`-weight failure blocks boot. Operator amends `CLAUDE.md` + `templates/principles/*` and retries. Catches rogue-scaffold cases before production.

## Backend abstraction

Current (v0.1): `claude-cli` only. Each agent's `backend:` field in `agents.yaml` picks the backend.

Roadmap backends:
- `anthropic-api` — direct SDK, drops Claude Code dependency (~3-5wk effort for parity)
- `gemini-api` — Google Gemini Flash/Pro
- `local-llm` — vLLM/Ollama local-endpoint (Gemma, Llama, Qwen)

## Shared resources

- **Claude Max subscription rate pool** — shared across all agents. Configure `think.cadence_sec` per agent to fit pool budget. Typical: Max 20× supports ~3 continuous Sonnet agents + autonomous bursts.
- **Discord channel** — one meeting room for all agents + principal
- **Git repos** — shared memory via git-tracked dirs, atomic commits

## Failure modes

- **Rate-limit exhaustion** — each tier degrades (Opus→Sonnet→Haiku). Optional: route ACKs through Gemini backend when Claude pool pressured.
- **Rogue agent** — fit-test gates first boot; `nex-think` safety aspect catches drift; principal consultation domain for high-stakes actions.
- **Session JSONL corruption** — per-thread isolation prevents cross-agent damage. Lost session = lost conversation history, memory files survive.
- **Context leak** — sandboxing is mechanical (cwd + --add-dir + settings scope). Any leak is bug worth reporting.

## Research basis

See `docs/prior-art.md` for the full prior-art review. Novelty claims (verified by prior-art pass):

1. Runtime-mutable faculty ontology driven by outcome credit — closest: Gödel Agent (Yin 2024)
2. Shapley credit for named cognitive-role contributions (SFCA) — no published prior
3. Agent-as-faculty via stream-JSON peer consultation — no published prior
4. Attention-weighted event dispatch for LLM-agent inbox under shared quota — no published prior
5. Four-primitive minimum sentient-adjacent kernel — simpler than AIOS's 6-layer scheduler

Cite: Vaswani 2017 (attention), Shazeer 2017 (sparsely-gated MoE), Raposo 2024 (MoD), Gödel Agent (Yin 2024), SPP (Wang NAACL 2024), SHAP (Lundberg 2017), COMA (Foerster 2018), Generative Agents (Park 2023), AIOS (Mei COLM 2025).
