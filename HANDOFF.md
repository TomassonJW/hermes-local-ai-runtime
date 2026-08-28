# Handoff

- Date: 2026-08-28 (updated by Hermes after G-05)
- Project: Hermes Local AI Runtime
- Repository: `TomassonJW/hermes-local-ai-runtime`
- Version: baseline `0.1.0`; API/job-core candidate `0.2.0-dev`
- Product baseline: `19070875f0c80e7799f394f6d4d16b481bd9be21`
- Baseline branch: `baseline/v0.1.0`

## Handoff status

G-01 and accepted UI-00 remain the takeover foundation. The authorised Phase 2
and Phase 3 lot is now complete through G-05:

- G-02 current read-only VM probe: passed.
- G-03 engine spike: llama.cpp `b10662` plus llama-swap `v251` selected by
  measurement; LocalAI rejected for profile A; ONNX embedding specialist kept.
- G-04 resource safety: hard cap, pressure refusal, lifecycle, crash recovery,
  cancellation, bounded queue and 1-heavy + 2-light behaviour proven in the
  disposable workspace.
- G-05 API/job core: `runtime/`, `config/g05-runtime.example.yaml`, updated
  OpenAPI/error contracts and `operations/G05-API-JOB-CORE-2026-08-28.md`.
  Forty-six tests pass. Final loopback smoke against the real llama.cpp route
  produced schema-valid structured JSON in 1,900 ms, cancelled a running real
  job in 24 ms and returned a valid OpenAI chat response. Hostile-review
  regressions now cover request/result byte ceilings, unique consumer identity,
  canonical request compatibility, atomic cancellation, worker teardown,
  proxy-environment isolation, non-blocking OpenAI waits and cross-instance
  idempotency.
- G-05 implementation commit `952614e` is pushed on `main`; GitHub Actions
  `validate-bootstrap` run `33130282636` passed.

No inference service is permanently installed or active. No backend listener,
Hermes configuration change, live-UI wiring or production consumer integration
exists. The accepted UI-00 shell remains explicitly simulated.

## Next hard stop

The user-authorised lot ends at G-05. Stop before G-06 until the next explicit
lot decision. The planned next vertical is vision and documents; it must reuse
the capability/job contract and preserve measured specialists, abstention and
review requirements.

## Resume from here

1. Verify `main`, working tree and CI at the G-05 closure commit.
2. Read `STATE.md`, `operations/G05-API-JOB-CORE-2026-08-28.md` and the G-06
   mission before any new implementation.
3. Do not create a permanent service, install models, wire Hermes or connect the
   UI until the corresponding later gate and rollback are authorised.

## Next session

1. Verify `main`, the working tree and the latest CI result.
2. Read `STATE.md`, this handoff, `GATES.md` and the mission for the next
   explicitly authorised lot.
3. Preserve the G-05 native capability/job boundary and its byte, identity,
   cancellation and loopback invariants.
4. Stop before G-06, permanent service activation, UI wiring or consumer
   integration unless Thomas explicitly authorises that lot.

## Do not do

Do not install inference engines permanently, download weights, expose beyond the authorised private boundary, modify Proxmox/unrelated services, add Sillage domain logic, claim universal vision replacement, start backend before UI-00 acceptance, choose NVIDIA/AMD, or create generic chat.

## Key decisions

Capability-first API; OpenAI facade; optional MCP; llama.cpp first candidate not lock-in; LocalAI comparison; specialist OCR/vector/audio; one heavy CPU inference; local-first fallback disabled by default; consumers own data and writes.
