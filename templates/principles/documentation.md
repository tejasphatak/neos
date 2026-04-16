# Documentation discipline — concise, on point, linkable

A principle for agents deployed with the neos kernel. Applies to any documentation the agent writes: README files in repos it maintains, blog posts, internal project notes, handoff summaries, the agent's own `CLAUDE.md`.

## The rule

**Documentation is terse and linked, not long and self-contained.**

- READMEs ≤150 lines of markdown, ≤500 words of prose.
- Long-form content lives in `docs/<topic>.md` — one topic per file.
- Handoff notes, status summaries, session recaps: lead with the decision or the ask; supporting detail goes under a second-level heading.
- Commit messages: subject ≤72 chars, imperative, explain *why* in the body.

## Why

Documentation is read by people (and agents) operating under time pressure. Dense walls of text get skimmed or ignored; short, link-heavy structure gets read. The goal is not to save characters — it is to maximize the chance that the reader takes away the thing that mattered.

## How to apply

- Before writing a new section, ask: does this belong in a dedicated `docs/*.md` instead? Default to yes.
- When editing existing docs: if you find yourself making a section longer, stop, extract, link.
- Don't restate rationale across documents — link to the single canonical write-up.
- Never inline full legal / licensing / disclaimer text in a README. Link to `docs/disclaimer.md` or `LICENSE`.

## Self-check

Before committing documentation, verify:

1. Did I hit the size target, or is there a section I could extract?
2. Is every claim sourced or grounded in a linkable doc?
3. Am I restating the diff in prose? (If yes, delete the restatement — the diff already shows what.)
4. Would a reader with 30 seconds come away with the right next action?
