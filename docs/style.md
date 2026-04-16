# neos documentation + code style

Opinionated. Lightweight. The whole project is ~5k lines — we don't get to hide complexity behind sprawling docs.

## READMEs — concise, on point, linkable

**README.md is the repo's entry surface.** A prospective user should be able to skim it in ~60 seconds and decide whether to clone.

Target: **≤150 lines of markdown, ≤500 words of prose.**

What belongs in README:

- Hero: name + one-line pitch + short elevator paragraph.
- Install / quickstart: copy-pasteable commands, not explanations.
- Key properties / differentiators: bullet list, ≤10 items.
- Documentation index: one-line pointers to `docs/*.md`.
- Test command.
- License.
- (Optional) a link to `docs/disclaimer.md`. Never the full legal text.

What does NOT belong in README:

- Legal disclaimers → `docs/disclaimer.md`
- Architecture deep-dives → `docs/architecture.md`
- Rationale essays → `docs/why-*.md` (one per topic)
- Authorship / narrative / drift admissions → `docs/authorship.md`
- Rate-limit economics → `docs/rate-budget.md`
- Full ASCII architecture diagrams → push to a dedicated architecture doc

### Signals that a README is bloating

- More than ~5 H2 sections
- Any one section spans >20 lines of prose
- Historical narrative ("we tried X, pivoted to Y, then Z convinced us to...")
- Multiple emoji-delimited warning sections
- ASCII diagrams taking up a whole screen

When you catch any of these while editing, extract to `docs/` and leave a link.

## docs/ pages — one topic each

Every `docs/*.md` file earns its existence by owning exactly one topic. If you're tempted to write `docs/misc.md` or `docs/notes.md`, split first.

Format:

- Title (`# Topic name`)
- TL;DR (2-3 sentences)
- Body (sections with H2/H3 as needed)
- References / links at the bottom

Avoid:

- Intra-doc forward references ("see §V.4 below") — use H2 anchors and hyperlinks.
- Dated entries in a living doc (that's a journal, not documentation).
- "Planned" sections without a shipping date — either do it or delete it.

## Deployed agents — same rule, recursively

When you run `nex init <agent>`, the agent gets its own `CLAUDE.md` identity scaffold. **That file should follow the same concision rule.** A 400-line CLAUDE.md is a sign the agent's identity has been over-specified; split role-specific guidance into `templates/faculty/*.md` and `templates/principles/*.md` that the agent can pull on demand.

The kernel provides this directly: the `documentation.md` principle (under `templates/principles/`) instructs agents to keep their own project docs concise and link out. Agents deployed with neos inherit this rule.

## Commit messages

- Subject line: ≤72 chars, imperative mood ("rename: agent-kernel → neos"), no trailing period.
- Body: wrap at 72 chars, explain *why* not *what* (diff already shows what).
- One commit, one intent. If you catch yourself typing " and also" mid-message, split the commit.

## Code

- Default to no comments. If you must: WHY the code exists, not WHAT it does.
- Don't re-export, don't add backwards-compat shims, don't leave `// removed` placeholders.
- Never hardcode user-facing strings, paths, thresholds, or secrets. Config or `$HOME/~`.
- No `# TODO(someone-else)` — either fix it or open an issue with a name and a date.

## Names

- Directories / files: `lower-kebab-case.md`
- Python modules / functions: `snake_case`
- CLI tools: `nex-<verb>` or `nex-<noun>-<verb>` (kebab-case, `bin/` prefix-free when invoked)
- Environment variables: `NEX_UPPERCASE`

## Dead-reckoning

If you're unsure whether something belongs in README or `docs/`: it belongs in `docs/`. Defaulting to `docs/` keeps README useful. Defaulting to README turns it into a junk drawer.
