# UI-00 acceptance

## Preconditions

- [ ] Baseline and working tree verified.
- [ ] Pinned UI canon read.
- [ ] `canonical-ui-design` loaded.
- [ ] Local UI contract read.
- [ ] Page registry and state matrix produced.
- [ ] No backend, engine, model, or permanent service started.

## Shell

- [ ] Topbar and navigation are coherent on desktop.
- [ ] Compact/mobile navigation is coherent.
- [ ] Overview, Capabilities, Models, Jobs, Evaluations, Resources, Updates, and Settings exist.
- [ ] Setup gear opens an addressable settings surface.
- [ ] Current location and page purpose are obvious.
- [ ] Keyboard focus and navigation are visible.
- [ ] Responsive layout has no core horizontal overflow.

## Truthfulness

- [ ] Every number and status is visibly simulated.
- [ ] No fake “connected”, “live”, “ready”, or “production” claim.
- [ ] Missing backend states are represented.
- [ ] Loading, empty, failure, degraded, blocked, stale, and permission states exist.
- [ ] Cloud fallback is shown disabled.
- [ ] Candidate/approved/deprecated/blocked model states are distinct.

## Product clarity

- [ ] Capabilities are more prominent than model names.
- [ ] Model detail includes licence, provenance, resource, benchmark, and route impact.
- [ ] Jobs expose queue/load/run/resource/review state.
- [ ] Resource page distinguishes allocation, budget, used, and estimated.
- [ ] Updates require evaluation and promotion.
- [ ] Normal operation does not require raw inference flags.
- [ ] No generic chat page is the default product surface.

## Accessibility and density

- [ ] Status is not colour-only.
- [ ] Text contrast and type scale are legible.
- [ ] Reduced motion works.
- [ ] Comfortable, standard, compact, dense, and data-grid behaviour follows the canon where offered.
- [ ] Tables transform appropriately on mobile.
- [ ] Confirmation and danger text is readable.

## Verification

- [ ] UI tests pass.
- [ ] Build/compile passes.
- [ ] Browser check on desktop.
- [ ] Browser check on mobile viewport.
- [ ] Private official route verified if deployment was authorised.
- [ ] Existing routes unaffected.
- [ ] Anti-secret scan passes.
- [ ] Commit and rollback recorded.
- [ ] `STATE.md` and `HANDOFF.md` updated.

## Absolute stop

After presenting UI-00, stop. Record Thomas's exact verdict. Do not infer acceptance from silence, positive wording, or technical success. No runtime backend or UI-01 before explicit acceptance.
