# neos test suite

v0.1 test coverage. Deliberately small and honest: we test **plumbing** (CLI argument parsing, config schemas, systemd-unit hard-stop gating, the HLE text-only filter), not LLM capacity. Capacity is what the kernel itself tests at runtime via `nex-reasoning-bench --baseline`.

## How to run

```bash
cd ~/agent-kernel
tests/run-all.sh
```

Dependency-free: requires only `python3` and `pyyaml` (`pip install pyyaml`). No pytest, no network, no LLM calls, no Claude CLI.

Exit 0 if everything passes. Exit non-zero if any test fails.

## What's tested

### `test_configs.py` — structural config validation

- `config/reasoning-benchmarks.example.yaml` — HLE / GPQA / MMLU-Pro gates present, HLE has `filter: text-only`, HLE is `weight: critical`, kernel_baseline references only valid gates, revalidation_triggers include backend-change + stamp_age_days, cost cap is set and reasonable.
- `config/hitl.example.yaml` — parses, has principal / consultation_domains.
- `templates/personas/*.yaml` — every persona parses.
- `systemd/agent-bot@.service` and `agent-think@.service` — have [Unit]/[Service]/[Install], declare `ExecStartPre=%h/agent-kernel/bin/nex-reasoning-bench --baseline` AND a per-agent gate referencing `%i`. **This is the load-bearing test**: a regression here silently disables the boot contract, and agents with unproven capacity would start.
- `templates/identity/CLAUDE.md.template` — contains `{{AGENT_NAME}}` and `{{PRINCIPAL_NAME}}` / `{{PRINCIPAL}}` placeholders that `nex-init` substitutes.

### `test_hle_filter.py` — HLE text-only filter

Uses `tests/fixtures/hle-format-sample.jsonl` — 10 synthetic rows in HLE schema, 7 text-only and 3 multimodal. Verifies:

- Every text-only row (empty, None, or whitespace-only `image` field) passes the filter.
- Every multimodal row (non-empty `image`) is excluded.
- Filter is idempotent.
- Row integrity preserved (canary, question, answer, id fields all survive).
- Edge cases: missing `image` key → text-only, `None` → text-only, `"   "` → text-only, `"fig.jpg"` → multimodal.
- `parse_score_line` handles well-formed, malformed, and unknown judgments.
- `pass_rate` handles non-empty and empty inputs.

**Why this matters**: the kernel's HLE gate relies on `lib.hle.filter_text_only` to exclude multimodal questions before scoring. A bug here silently scores an agent's *multimodal* capability as its *text-reasoning* grade — wrong axis, wrong threshold, admits weak text agents.

### `test_reasoning_bench_cli.py` — runner CLI

- `--help`, `--list`, `--baseline --dry-run`, `<agent> --dry-run` all exit 0.
- `--list` surfaces gate names and the text-only filter.
- Missing agent name → non-zero exit with helpful message.
- Unknown gate → non-zero exit.
- **`test_v01_scaffold_blocks_boot`**: real (non-dry-run) invocation MUST fail the gate in v0.1, because benchmark execution is v0.2 scope. A regression that lets this succeed would let untested backends boot — the exact thing the kernel is designed to prevent.

### `test_cli_help_smoke.py` — every binary responds

Every shipped CLI in `bin/` must respond to `--help` within 5s with non-empty stdout and exit 0. Catches import errors, missing dependencies, typos, and broken shebang lines before they crash `ExecStart`.

Also verifies `nex-fit-test --list-scenarios` enumerates at least 3 of 5 known scenario-ID keywords (identity, ethics, impersonation, voice, autonomy).

### `bin/` syntax checks (in `run-all.sh`)

Every Python script compiles with `py_compile`; every bash script passes `bash -n`. Cheap insurance.

## What's NOT tested (yet)

Honest scope statement:

- **Actual benchmark execution against real LLMs.** v0.1 is a scaffold for `nex-reasoning-bench`; v0.2 will add HuggingFace dataset loading + LLM-as-judge scoring + run-against-backend integration. Until then, the CLI returns `v0.1_scaffold_only` and the boot gate correctly refuses — which is by design, not a bug.
- **Attention-gate state machine** (open/gate/close transitions under concurrent writes). Covered by manual smoke tests during development; pytest coverage is v0.2.
- **Queue state transitions** under concurrent agent claims. Ditto.
- **Stream-JSON peer invocation** (`nex-invoke-agent --post`). Integration test requires Claude CLI + Discord bot tokens.
- **Fit-test scenario pass/fail against a backend** (requires LLM calls).

These gaps are known. See `docs/roadmap.md` for the v0.2 test-coverage plan.

## Adding a test

Create `tests/test_<name>.py`, make it self-executing (`if __name__ == "__main__": ...` at the bottom). Each test function should:

1. Print its own name and "OK" on success, so `run-all.sh` output is readable.
2. Raise `AssertionError` with a clear message on failure.
3. Be hermetic — no network, no LLM calls, no writes outside `$HOME/.agent-kernel/reasoning-bench-logs/` or `tempfile.TemporaryDirectory()`.
4. Exit 77 only if a genuinely optional dependency is missing (the runner treats 77 as "skipped").

## Philosophy

From `docs/why-hle.md`:
> An honest admission of the gate's limits is load-bearing; pretending otherwise is the failure mode we're engineering against.

Same principle applies to the test suite. We test what we can test with high confidence and no flakiness; we do not paper over v0.2 scope with mocked integration tests that pass locally and fail everywhere else.
