# UI-00 — Page registry and state matrix

Shell delivered 2026-08-27. Stack: Vite 8 + React 19 + TypeScript, hash router,
static build servable by any file server. Fixture: `ui00-fixture/1.0.0`
(`ui/shell/src/fixture/ui00.ts`). All data simulated; banner on every page:
`Demo state — no runtime connected`.

## Official private surface

`https://<private-tailnet-host>/apps/local-ai-runtime/` — tailnet-only route to
a loopback static server on the built `ui/shell/dist/`. The exact hostname is
private infrastructure and stays out of this public repository; it is delivered
to Thomas directly.

## Registry

| # | Destination | Route | UI-00 status | Purpose (plain language) |
| - | --- | --- | --- | --- |
| 1 | Overview | `#/` | Prototype | Is the runtime ready, what can it do, what needs attention |
| 2 | Capabilities | `#/capabilities` (+ `/:id` detail) | Prototype | Contracts applications call; routes, limits, fallback |
| 3 | Models | `#/models` (+ `/:id` detail) | Prototype | Lifecycle discovered→approved, licences, provenance |
| 4 | Jobs | `#/jobs` (+ `/:id` detail) | Prototype | Executions with queue/load/run, refusals, hidden payloads |
| 5 | Evaluations | `#/evaluations` | Prototype | Quality/resource comparisons gating promotions |
| 6 | Resources | `#/resources` | Prototype | Allocated vs budget vs used vs estimated; admission events |
| 7 | Updates | `#/updates` | Prototype | Detected candidates; no automatic promotion |
| 8 | Settings | `#/settings` | Prototype | Live interface prefs; read-only planned runtime policy |

All 8 destinations are navigable (no `À développer` placeholder needed at this
stage — every contract page has a real prototype). Detail surfaces are
deep-linkable (`#/capabilities/vision.analyze`, `#/models/sim-vlm-2b-q4`,
`#/jobs/job_sim_0195`).

## State matrix (explicit non-nominal states shown in the shell)

| State | Where represented |
| --- | --- |
| Runtime unavailable | Overview "Not connected" + reasons; StateBox on Overview/Resources |
| Empty | Capabilities (no consumer), Jobs (no live stream), Updates (no engine updates) |
| Blocked by gate | `audio.transcribe` (G-08), blocked model detail explanation |
| No route approved | `text.extract_structured`, `search.rerank` |
| Resource refusal | Job `job_sim_0195` + Resources admission event, plain-language "Why refused?" |
| Degraded/warning | Queued job cold-load warning; no-swap callout |
| Permission | Payload hidden (privileged action disabled); runtime policy locked |
| Stale | Evaluations "no real benchmark has run" |
| Failure/unknown id | Unknown capability/model/job detail routes render an honest error |
| Loading | Skeleton component available in the design system (used by future live pages) |

## Preferences (live in UI-00)

Theme light/dark/system · text size 90–120% · density dense/compact/comfortable/
spacious (`density-profile/v1`) · stronger contrast · reduced motion · reset.
Stored in `localStorage` (browser-local), applied immediately.

## Verification evidence (2026-08-27)

- `pnpm test`: 14/14 pass (`ui/shell/tests/shell.test.tsx`).
- `pnpm typecheck` and `pnpm build`: pass.
- Headless browser probe on the **official private URL**, desktop 1280×900 and
  mobile 390×844 (`ui/shell/scripts/viewport-probe.mjs`): all 11 routes render,
  demo banner everywhere, zero console errors, mobile nav dialog opens/navigates/
  closes, no horizontal overflow, dark theme applies. Screenshots in
  `ui/shell/scripts/shots/` (synthetic data only).
- All pre-existing tailnet routes re-checked 200 after adding the new path.
- Bootstrap validator + pytest still pass at repo root.

## Absolute stop

UI-01 and any runtime backend remain blocked until Thomas's explicit verdict on
this shell (`ui/UI-00-ACCEPTANCE.md`).
