# Handoff

- Date: 2026-08-28 10:04 CEST
- Project: Hermes Local AI Runtime
- Path: `/srv/hermes-data/users/hermes/productions/hermes-agency/projects/project--2026-08-27--22-29--local-ai--hermes-local-ai-runtime/hermes-local-ai-runtime`
- Repository: `TomassonJW/hermes-local-ai-runtime`
- Version: baseline `0.1.0`; API/job-core candidate `0.2.0-dev`
- Product baseline: `19070875f0c80e7799f394f6d4d16b481bd9be21` on `baseline/v0.1.0`
- Verified product base (pre-handoff commit): `2da63655a6c5c845111f22e0d0524e6bc33bf492`
- Branch: `main` = `origin/main`, working tree clean, no session worktree

## Handoff status

Authorised work through G-05 is closed. UI-00 is accepted. The Hub exposes a
top-bar shortcut only. This is not a finished daily-use program.

Closed:

- G-00 to G-04: bootstrap, takeover, live probe, llama.cpp `b10662` +
  llama-swap `v251`, LocalAI rejected, resource cap 1-heavy + 2-light.
- UI-00: explicit « ACCEPTÉ » on 2026-08-27 at shell commit `21cb372`.
  Simulated fixture only. Not live.
- G-05: native `/api/v1` jobs, auth, idempotency, admission, cancel,
  provenance, byte ceilings, OpenAI facade. 46 tests. Hardening commit
  `2da6365` (proxy `trust_env=False`, OpenAI wait off the event loop,
  `BEGIN IMMEDIATE` idempotency). CI `validate-bootstrap` run
  `33131398550` passed.
- Hub top-bar button « IA locale » (not a grid card), HermesHub commit
  `a7cd8dc`. Official private Hub root plus `/apps/local-ai-runtime/`.
  Exact hostname stays out of this public file.

Not done (do not infer complete):

- G-06 vision/documents, G-07 retrieval, G-08 audio.
- G-09 packaging/permanent service, G-10 live UI + Hermes skill + two
  consumers, G-11 public release.
- Typed clients, live UI wiring, production consumers.
- GPU / distributed workers (Phase 8). Parked items in `BACKLOG.md`.

## Session inventory

- Runtime Git: one worktree, `main`. No dirty or extra branch.
- HermesHub Git: `main` clean at `a7cd8dc`. Two **foreign** prunable
  worktrees (`/tmp/hermes-ui-lab-complex-shell`,
  `/tmp/hermes-ui-studio-pivot`) - leave untouched.
- Delegations: finished; none running. Do not re-open obsolete FAIL
  reviews on superseded hashes.
- Kanban board `hermes-local-ai-runtime`: does not exist. Authority is
  `BACKLOG.md` / `GATES.md`.
- UI-00 preview: session `python3 -m http.server 8830 --bind 127.0.0.1`
  from `ui/shell/dist/` (PID observed 3107598). Not a systemd unit.
  Restart command is in `ui/shell/README.md`. Hub itself listens on
  loopback 8770 (pre-existing, not this session's to stop).
- No G-05 inference listener is permanently installed.

## Next hard stop

Stop before G-06, permanent service, model download, live UI-01, Hermes
config change, or consumer integration until Thomas gives an explicit
lot decision. Planned next lot: G-06. Mission:
`missions/04-vision-and-document-capabilities.md`.

## Resume from here

1. Read `AGENTS.md`, `STATE.md`, this file, `GATES.md`, `ROADMAP.md`.
2. Verify `git status` / `main` at or after `2da6365`, and Hub `a7cd8dc`
   if touching the shortcut.
3. If the Hub button 404s, restart the UI-00 preview only (loopback
   8830). Do not add a permanent unit.
4. Do not start G-06 without a new explicit GO.

## Do not do

Do not install engines permanently, download weights, expose beyond the
authorised private boundary, mutate Proxmox, add Sillage domain logic,
claim universal vision, start UI-01, choose a GPU vendor, or build a
generic chat product. Do not return to Notion for ordinary sessions.

## Resume prompt

```
Reprends Hermes Local AI Runtime. Lis AGENTS.md, STATE.md, HANDOFF.md et GATES.md. Vérifie que main est propre à 2da6365 ou plus récent. G-00 à G-05 et UI-00 sont clos. N'ouvre pas G-06, n'installe aucun service permanent, ne câble pas l'UI live et ne télécharge aucun modèle tant que je n'ai pas dit GO G-06. Si le bouton Hub IA locale est mort, relance seulement le serveur statique loopback du shell UI-00 (ui/shell/README.md).
```
