# AGENTS.md

## Repository mission

This repository is the complete product and engineering authority for **Hermes Local AI Runtime** after the bootstrap handoff. It must become an installable, local-first AI capability runtime that can serve Hermes and independent applications without coupling consumers to model names or inference engines.

The repository must remain understandable and actionable without access to Notion, private conversations, personal memory, or another project.

## Authority order

1. Non-negotiable safety, privacy, legal, and resource constraints.
2. Thomas Jankowski's latest explicit product decision.
3. The active product constitution and gates in this repository.
4. Accepted ADRs for architecture and implementation decisions.
5. Executed behaviour, tests, measurements, logs, and deployed evidence for what actually works.
6. Research notes and candidate model registry as evidence, never as automatic decisions.

A model card, benchmark claim, README, or successful build is not proof that a capability works on the target Hermes VM.

## Required reading at session start

1. `BASELINE.md` when present.
2. `HANDOFF.md`.
3. `STATE.md`, `GATES.md`, and the active roadmap/backlog slice.
4. `provenance/COMPILATION-MANIFEST.yml`.
5. The product and architecture chapters relevant to the current lot.
6. Existing ADRs before making a structural decision.
7. `ui/LOCAL-UI-CONTRACT.md` and the pinned UI canon before any UI work.

Do not return to Notion for ordinary sessions. A strategic product amendment may be brought through ChatGPT/Notion and then compiled as an explicit Git diff.

## Product invariants

- Consumers call stable capabilities; they do not depend on checkpoint filenames.
- No consumer database credential is held by the runtime.
- No result is silently written into a consumer's business data.
- No model download is automatically promoted to production.
- No model, runtime, prompt, quantisation, context size, or provider is hardcoded in a consumer integration.
- No heavy job starts without resource admission.
- No public network listener exists by default.
- No request content is logged by default.
- No cloud fallback occurs unless the consumer and route policy explicitly permit it.
- Low confidence, unsupported input, resource refusal, timeout, and degraded execution are first-class results, not hidden retries.
- A specialist may beat a general VLM on a bounded task; routing must preserve that option.
- The system must remain usable in CPU-only mode and evolve to GPU or remote workers without breaking capability contracts.

## Development discipline

- Distinguish fact, hypothesis, decision, candidate, and unknown.
- Prefer reversible implementation choices until a benchmark proves the need to specialise.
- Create or update an ADR before changing a structural boundary.
- Do not claim implemented, working, fast, safe, private, or production-ready without corresponding evidence.
- Keep `STATE.md`, `HANDOFF.md`, `ROADMAP.md`, and `BACKLOG.md` aligned with facts.
- Keep model statuses honest: `discovered`, `candidate`, `compatible`, `benchmarked`, `approved`, `deprecated`, or `blocked`.
- Record exact engine versions, model revisions, artefact hashes, presets, and hardware profile for benchmark results.
- Maintain the native capability API and OpenAI-compatible facade as separate contracts.
- Prefer small vertical slices that exercise admission, execution, provenance, and cancellation end to end.

## First implementation boundary

The bootstrap authorises repository takeover and read-only preflight only.

Because the product includes an operations interface, the first visible implementation lot is **UI-00**: canonical shell, complete navigation skeleton, truthful simulated states, no inference backend, no permanent runtime service, no model download, and no host or Proxmox mutation.

After UI-00 is served and verified, stop for Thomas's explicit visible-product verdict. Do not begin UI-01 or the runtime backend before that verdict.

Read-only hardware probes, dependency compatibility checks, fixture preparation, and spike design may be prepared during preflight. Any permanent package installation, service activation, model download, network exposure, or resource allocation requires the corresponding gate and documented rollback.

## Git rules

- `main` is the official branch.
- Inspect branch, working tree, remote, and recent commits before mutation.
- Preserve foreign or uncommitted work.
- Use focused commits tied to verified outcomes.
- No force-push, shared-history rewrite, destructive cleanup, or secret-bearing commit.
- Run relevant tests, `git diff --check`, and anti-secret checks before commit.
- After an authorised lot passes its gates, keep `main` and `origin/main` aligned unless an external block is documented.
- Rollback is differential: remove only the change being reverted and preserve legitimate later work.

## Security and public-repository boundary

Never commit API keys, tokens, credentials, private URLs, private IP inventories, `.env`, model-provider auth, database dumps, personal documents, real invoices, audio recordings, private screenshots, user memory, private benchmark corpora, model weights, third-party binaries, or generated logs containing request payloads.

Public fixtures must be synthetic, openly licensed, or irreversibly anonymised. Private evaluation corpora are mounted locally and referenced only through public-safe manifests.

## UI/UX authority

The project pins `TomassonJW/canonical-ui-design` version `1.3.0`, commit `4d720bf20f3c89e9a9d71072f0b76d55d225cb62`.

Before UI work, read the pinned canon and `ui/LOCAL-UI-CONTRACT.md`. Load `canonical-ui-design`. UI-00 is an absolute stop before backend and deeper screens.

The interface is an operations and evaluation console, not a generic chat product. It must expose system truth, uncertainty, loaded models, jobs, resource pressure, provenance, model lifecycle, and update candidates without encouraging parameter fiddling as normal operation.

## Decisions that require Thomas

Escalate only when a choice materially changes user experience or product ambition; public exposure, privacy, data ownership, or cloud fallback; cost, hardware, licence compatibility, or commercial reuse; destructive behaviour; capability contracts; maintenance burden; or visible UI acceptance.

Choose and document ordinary technical details in ADRs.

## Lot closure

A lot closes only when acceptance criteria and limits are documented, tests and benchmarks actually ran, resource/security gates passed, rollback exists, repository state and handoff match reality, no human acceptance is inferred, and public documentation contains no secret or private corpus data.
