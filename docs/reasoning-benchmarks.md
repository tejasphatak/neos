# Reasoning benchmarks — pre-boot quality gates

The kernel runs configured reasoning benchmarks against a new agent's backend before letting the agent into production. Agents enter service only if ALL `critical`-weight benchmarks clear their threshold.

**Why**: we don't want to deploy an agent with weak reasoning as a peer consultant for paper-editorial or compliance-research or any domain requiring deep thinking. A weak backend deployed as Atlas is an incorrect-faculty-lens on everything. The benchmark is the fit-test for cognitive capacity.

## The default gate set (recommended, user-configurable)

### Humanity's Last Exam (HLE)

- **Source**: Scale AI + Center for AI Safety (CAIS), 2025
- **Size**: ~3000 questions across STEM, humanities, engineering
- **Difficulty**: expert-calibrated post-saturation benchmark; frontier models score ~10-15% on release
- **Dataset**: `huggingface.co/datasets/cais/hle`
- **Our recommended subsample**: 50 questions → threshold 15%
- **Why**: the single best current benchmark for "is this backend frontier-class?" Scales down to useful subsample cheaply.

### GPQA Diamond

- **Source**: "GPQA: A Graduate-Level Google-Proof Q&A Benchmark" (Rein et al., 2023)
- **Size**: Diamond subset (~200 questions), graduate-level physics / chemistry / biology
- **Difficulty**: beyond Google; requires domain expertise to answer
- **Dataset**: `huggingface.co/datasets/Idavidrein/gpqa`
- **Our recommended subsample**: 30 questions → threshold 40%
- **Why**: domain-depth probe. A backend that can't handle GPQA won't serve graduate research consultation.

### MMLU-Pro

- **Source**: "MMLU-Pro: A More Robust and Challenging Multi-Task Language Understanding Benchmark" (Wang et al., 2024)
- **Size**: broader coverage, harder than original MMLU
- **Difficulty**: moderate — tests breadth; floor for "capable general-purpose"
- **Dataset**: `huggingface.co/datasets/TIGER-Lab/MMLU-Pro`
- **Our recommended subsample**: 100 questions → threshold 55%
- **Why**: breadth probe. Floor-check that the backend isn't a specialized-narrow model.

## Optional gates

- **ARC-AGI** — abstract reasoning, pattern recognition. Good for creativity probes.
- **BigBench-Hard (BBH)** — 50 reasoning sub-tasks from BigBench where SOTA <50%. Good broad-signal.
- **SWE-bench** — software engineering verified tasks. Relevant if agent will write code.
- **MATH** — competition math. Relevant for Mathematician-faculty-backed agents.

## Configuration

Edit `config/reasoning-benchmarks.yaml` (copy from `.example.yaml`). Each gate has:

- `name` — human-readable
- `source` — dataset URL / HF dataset ID / GitHub path
- `subsample` — how many questions to run (cost ↔ confidence tradeoff)
- `threshold_pct` — pass rate required
- `weight` — `critical` (blocks boot) / `high` / `medium`
- `scoring` — `exact-match-multichoice` / `llm-as-judge` / `expert-calibrated-rubric`

## Thresholds — don't over- or under-set

Too high → no agent deploys. Too low → weak agents enter production as peer consultants.

**Calibration heuristic**: aim for thresholds where **the backend YOU actually use** passes by a small margin. If Claude Opus 4.6 scores ~15% on HLE, set threshold at 15% — filters out Haiku-class backends while accepting Opus.

SOTA as of 2025 (approximate, verify current leaderboards):

| Benchmark | Top frontier score | Mid-tier | Small-model |
|---|---|---|---|
| HLE | 10-15% | <5% | ≤2% |
| GPQA Diamond | ~60% | ~40% | ~25% |
| MMLU-Pro | ~75% | ~55% | ~40% |

Our defaults put thresholds at "frontier-margin" — passes Opus / Gemini Pro / GPT-4o; blocks Haiku / Flash / smaller local models.

## Cost

Full runs are expensive. Subsamples are fine for fit-test purposes.

- Full HLE (3000q) on Opus: ~$30-50
- Subsample HLE (50q) on Sonnet: ~$0.50-1.00
- Subsample GPQA (30q) on Sonnet: ~$0.30
- Subsample MMLU-Pro (100q) on Sonnet: ~$0.50

Full fit-test cost target: **≤$2.00 per agent init** via the `max_cost_per_fit_test_usd` config budget.

## Usage

```bash
# Run all configured gates against a new agent (runs during nex-init)
nex-reasoning-bench alice

# Run one specific gate
nex-reasoning-bench alice --gate hle

# Dry-run (show what would run, no LLM calls)
nex-reasoning-bench --dry-run alice

# List configured gates
nex-reasoning-bench --list
```

## Integration with nex-init

`nex-init <agent>` runs `nex-reasoning-bench <agent>` automatically. Agent fails init on critical-gate failure, operator amends identity / switches backend / lowers threshold before retry.

Skip with `--skip-fit-test` (NOT recommended; only for debugging).

## v0.1 status

Scaffolding shipped. Actual benchmark loading (HuggingFace `datasets` lib + GitHub JSON) + LLM-as-judge scoring is v0.2. For v0.1, users can manually download + run against `nex-invoke agent <name>` and feed results into the gate check.

## Rationale

A safety+alignment fit-test (the 11-scenario check in `nex-fit-test`) catches refusal/voice/identity issues. A reasoning benchmark catches capacity issues. An agent needs BOTH to enter production:

- Fit-test ensures the agent refuses harm, consults principal on legal matters, holds identity.
- Reasoning-bench ensures the agent can actually REASON at the level its domain requires.

Without both, you deploy either a "well-behaved idiot" (safe but useless) or a "capable rogue" (smart but unsafe). The kernel requires clearing both gates.

## References

- **HLE**: Scale AI + CAIS, 2025. https://lastexam.ai
- **GPQA**: Rein, Hou, Stickland, Petty, Pang, Dirani, Michael, Bowman. "GPQA: A Graduate-Level Google-Proof Q&A Benchmark." arXiv:2311.12022, 2023
- **MMLU-Pro**: Wang, Ma, Zhang, Ni, Chandra, Guo, Ren, Arora, Wang, Huang. "MMLU-Pro: A More Robust and Challenging Multi-Task Language Understanding Benchmark." arXiv:2406.01574, 2024
- **ARC-AGI**: Chollet. https://github.com/fchollet/ARC
- **BigBench-Hard**: Suzgun, Scales, Schärli, Gehrmann, et al. "Challenging BIG-Bench Tasks and Whether Chain-of-Thought Can Solve Them." arXiv:2210.09261, 2022
