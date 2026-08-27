# Product constitution index

Read in order:

1. [`01-vision-and-positioning.md`](01-vision-and-positioning.md)
2. [`02-users-and-use-cases.md`](02-users-and-use-cases.md)
3. [`03-capability-map.md`](03-capability-map.md)
4. [`04-scope-and-non-goals.md`](04-scope-and-non-goals.md)
5. [`05-success-metrics.md`](05-success-metrics.md)
6. [`06-risk-register.md`](06-risk-register.md)
7. [`07-quality-and-fallback-policy.md`](07-quality-and-fallback-policy.md)

## Product sentence

Hermes Local AI Runtime is a local-first capability kernel that gives Hermes and independent applications stable access to replaceable AI engines under explicit quality, privacy, licence, provenance, and resource policies.

## Ambition level

This is an **internal-first platform component with public installability**, not a prototype hidden inside one application and not yet a universal public platform.

Maturity transitions are explicit: compiled bootstrap; internal prototype; useful internal tool; shared internal runtime after two consumers; public product only after install, security, API, evaluation and licence gates.

## Product owner

Thomas Jankowski owns product intent, material trade-offs and visible acceptance. Hermes owns ordinary technical execution after takeover.

## Non-negotiable boundaries

- no Sillage coupling;
- no model-name coupling for consumers;
- no hidden cloud fallback;
- no uncontrolled server saturation;
- no silent business-data writes;
- no private corpus in the public repository;
- no universal-quality claim for small local models;
- no GPU-vendor lock-in before hardware exists.
