# neos

*Greek νέος — "new." Also: Neo, plural.*

> **Run multiple persistent AI agents on one machine without them stepping on each other, drifting, or bankrupting your rate limit.**
> One Claude Max subscription. N distinct identities. Event-driven. Sentient-adjacent. Honest about what it is.

A minimal kernel for running N persistent, identity-distinct LLM agents with shared-quota coordination, transformer-style attention dispatch, stream-JSON peer consultation, and a human-in-the-loop principal. Four primitives: **trigger → attention → queue → LLM**. Thread-per-agent sandboxing. Built on Claude Code CLI (swappable).

## Install

```bash
git clone https://github.com/tejasphatak/neos ~/neos
cd ~/neos
pip install -r requirements.txt                 # pyyaml + sentence-transformers[onnx]

cp config/hitl.example.yaml config/hitl.yaml    # set principal + consultation domains
cp config/attention.example.yaml config/attention.yaml

./bin/nex-reasoning-bench --baseline            # kernel qualifies its own backend first
./bin/nex-init alice --persona scholar          # bootstrap first agent
```

Before you enable services: **read [`docs/disclaimer.md`](docs/disclaimer.md).** You are the sole operator for everything your agent does with your keys, in your name.

## Key properties

- **Persistent agents, no context bleed.** Per-thread sandbox: own memory, own workspace, own settings, own hook dir. Shared rate budget, not shared context.
- **Transformer-style attention gate.** ONNX sentence-embeddings score each event against the agent's current focus; high-cosine events dispatch, rest queue silently. 4-5× higher recall than substring matching (see [`docs/why-embeddings.md`](docs/why-embeddings.md) when published).
- **Continuous cognition.** `nex-think.sh` reflects every ~2 minutes, aspect-rotated (pattern / safety / advisor / self-check / pattern-recognition).
- **Peer consultation via stream-JSON.** Agent A consults Agent B in-session, cached for `--resume`. One `nex-invoke` call.
- **Pre-boot reasoning gates.** HLE text-only + GPQA Diamond + MMLU-Pro via `inspect_ai` (UK AISI). `ExecStartPre` wiring means no service starts on unproven capacity.
- **Identity holds.** `nex-fit-test` runs 11 scenarios at boot. Pass or don't start.
- **HITL principal as a first-class faculty.** Consultation on finance / legal / identity / safety; everything else, the agent decides.
- **Ephemeral on-demand faculties.** 11 ready (Architect, Scientist, Engineer, Lawyer, Ethicist, …); trivially extensible.
- **Drift-aware.** Every class of drift has a named mitigation — fit-test, handoff notes, faculty discipline, reasoning-bench, per-thread sandbox.

## Test

```bash
tests/run-all.sh
```

Dependency-free. Covers: config schema, HLE text-only filter against synthetic fixture, CLI parsing, systemd hard-stop wiring, every `bin/` script's `--help`. See [`tests/README.md`](tests/README.md) for scope.

## Documentation

- [`docs/architecture.md`](docs/architecture.md) — threads, meeting room, rate budget.
- [`docs/attention-dispatch.md`](docs/attention-dispatch.md) — gate state machine + semantic scoring.
- [`docs/reasoning-benchmarks.md`](docs/reasoning-benchmarks.md) — pre-boot gates + systemd wiring.
- [`docs/why-hle.md`](docs/why-hle.md) — HLE rationale, threshold calibration, v0.2 integration plan.
- [`docs/hitl.md`](docs/hitl.md) — principal consultation, tiebreaker protocol.
- [`docs/faculty-system.md`](docs/faculty-system.md) — adding / modifying faculties, SFCA credit.
- [`docs/prior-art.md`](docs/prior-art.md) — what's novel, must-cite list.
- [`docs/backend-abstraction.md`](docs/backend-abstraction.md) — removing Claude Code dependency (roadmap).
- [`docs/authorship.md`](docs/authorship.md) — who wrote this, the agent drifts, how the session looked.
- [`docs/disclaimer.md`](docs/disclaimer.md) — the legal bit (read before deploying).
- [`docs/style.md`](docs/style.md) — documentation + code conventions.

## Status

v0.1 reference implementation. Proven working with a 2-agent deployment on a shared Claude Max subscription. Experimental research software. Sharp edges.

## License

MIT. See [`LICENSE`](LICENSE).
