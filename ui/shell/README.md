# UI-00 operations shell

Static operations console for Hermes Local AI Runtime, delivered as the UI-00
gate artefact. Simulated fixture data only (`src/fixture/ui00.ts`) — no backend,
no live metric, no system probe.

## Stack

Vite 8 · React 19 · TypeScript · react-router (hash routing) · Vitest +
Testing Library. Node ≥ 22, pnpm 10.

## Commands

```bash
pnpm install     # once
pnpm test        # 14 UI tests
pnpm typecheck
pnpm build       # emits dist/ (relative base → servable from any path)
pnpm dev         # local dev server on 127.0.0.1:8830
```

## Serving the built shell (UI-00 preview)

Any static file server pointed at `dist/` works. The UI-00 preview uses:

```bash
cd ui/shell/dist && python3 -m http.server 8830 --bind 127.0.0.1
```

with a private tailnet path `/apps/local-ai-runtime` proxying to
`127.0.0.1:8830`. Loopback bind only; no public exposure. The exact private
hostname stays out of this public repository. This preview server
is a session process, not an installed service — restart it with the command
above if the machine reboots.

## Verification probe

`scripts/viewport-probe.mjs` drives a headless Chromium over CDP against the
served URL (desktop 1280×900 + mobile 390×844): checks every route renders,
the demo banner is present everywhere, the mobile nav dialog works, no
horizontal overflow, and no console errors. Screenshots land in
`scripts/shots/` (synthetic data only).

```bash
node scripts/viewport-probe.mjs                          # against 127.0.0.1:8830
node scripts/viewport-probe.mjs "$PRIVATE_UI_URL"        # against the private route
```

## Boundaries

This shell must not gain a real API client, model download, or backend
assumption before UI-00 acceptance and the corresponding gates. The fixture is
the single data source.
