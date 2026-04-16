# 🚨 Disclaimer (the part where we don't get sued)

> **Short version: this is experimental research software. No warranty. Use at your own risk. You — the operator — are the sole responsible party for everything the agent does on your hardware, with your keys, in your name.**

## ⚠️ First, a softer warning: use a dumb LLM, win a dumb prize

🎵 *Dumb ways to diiiie, so many dumb ways to diiiie...* 🎵

- Wire GPT-2 into the kernel and wonder why your "autonomous research agent" keeps recommending you invest your savings in **"tokens"** (it means BPE tokens, it really does).
- Use a 7B quant that hallucinates a `rm -rf /` into your shared queue because it confused "clean up tasks" with "clean up the filesystem."
- Plug in a model that confidently signs legal documents as **"Sincerely, Assistant"** on your behalf.
- Let a toy LLM play `Lawyer` faculty, ignore the contract clause, and discover `contractual penalty` is not, in fact, a Pokémon type.
- Pick a model that thinks HLE stands for "High-Level English" and scores 2% on it, then merrily advises the principal on tensor algebra.
- Run a Discord bot backed by a dumb LLM that, when asked "are you sure?", replies "yes 🙂" to every single destructive action. Every. Single. One.

**That is why `nex-reasoning-bench` exists.** The kernel refuses to boot any agent whose backend can't clear HLE-text-only + GPQA Diamond + MMLU-Pro. No baseline pass → no service starts. Unproven capacity is unfit capacity.

**Please.** Use an adult LLM.

## The funny part (so you read the serious part below)

Under operator misconfiguration, this software may:

- Spend money in an account you handed it billing-scoped credentials for.
- Divulge your password, because you stored it in `~/.bashrc` or `~/.env` and the agent reads files as part of its job description.
- Post to a channel you authorized it to post in, at 03:14 AM, in a voice you trained it on.
- Email a person you configured its `nex-email` tool to be able to reach.
- Run `rm` in a directory you gave it write access to.
- Commit a secret to a repository you authorized it to push to.
- Say something confidently wrong, and the agent it is consulting will agree.

None of the above are bugs. They are the logical consequences of granting a stochastic language model autonomous access to tools, keys, and a shell. The kernel's mitigations — `nex-fit-test`, `nex-reasoning-bench`, attention gate, HITL `consultation_domains`, sandboxed `--add-dir`, per-thread settings, `--allowed-tools` — are **necessary but not sufficient**, because LLM behaviour is stochastic and new failure modes are discovered by the field on roughly a weekly cadence.

## The serious part

**THIS SOFTWARE IS PROVIDED "AS IS" AND "AS AVAILABLE", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT.** See `LICENSE` for the controlling legal text.

- **Experimental research software.** v0.1. Not production-ready. Not audited. Not certified for any regulated domain (including but not limited to HIPAA, SOC 2, PCI-DSS, GDPR-sensitive processing, legal practice, medical practice, investment advice, or safety-critical systems).
- **Not professional advice.** Nothing produced by this software or by any agent deployed using it constitutes legal, medical, financial, tax, engineering, safety, accounting, therapeutic, or any other form of professional advice. Agents are language models; their outputs can be confidently wrong.
- **You are the sole operator.** You alone choose the backend LLM, the tools made available via `--allowed-tools`, the credentials placed within reach at `~/.claude/secrets/` or elsewhere, the consultation domains gated by HITL, and the scope of autonomous action. The authors, contributors, and maintainers of this software have no visibility into, no control over, and no authority within your deployment.
- **No liability.** TO THE FULLEST EXTENT PERMITTED BY APPLICABLE LAW, IN NO EVENT SHALL THE AUTHORS, CONTRIBUTORS, OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES, OR OTHER LIABILITY — whether arising in contract, tort (including negligence), strict liability, or otherwise — arising from, out of, or in connection with the software or the use or other dealings in the software, including without limitation any direct, indirect, incidental, special, consequential, punitive, or exemplary damages (including but not limited to loss of profits, data, credentials, reputation, business opportunity, or goodwill).
- **Indemnity.** You agree to hold harmless and indemnify the authors, contributors, and copyright holders from and against any claims, losses, damages, liabilities, costs, and expenses (including reasonable attorneys' fees) arising out of or relating to your use of the software, your configuration thereof, the actions of agents you deploy, the credentials or tools you make available to those agents, and any third-party consequences of the foregoing.
- **Not for high-stakes deployment** without independent security review, professional oversight, and legal/compliance sign-off appropriate to your jurisdiction and use case.

## Strongly recommended before you install

- Run on a disposable VM or sandbox first. (We did. That is how we learned what to put in this disclaimer.)
- Use scoped, rate-capped, revocable credentials. Never long-lived root keys.
- Do not grant the agent access to any credential controlling something you cannot afford to lose.
- Read the code. It is ~5k lines of Python and shell. You can.
- Configure `config/hitl.yaml` to require human sign-off on anything irreversible **before** you deploy.
- Consult qualified professionals before any deployment near regulated or safety-critical systems.

If after reading all of this you still want to install it, welcome — you are the right kind of operator. If you read all of this and decide not to, also welcome — you are quite possibly right.

*No refunds. No warranties. No service-level agreements. No exorcisms.*
