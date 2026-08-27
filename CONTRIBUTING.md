# Contributing

Hermes Local AI Runtime is internal-first and public by design. Contributions are welcome when they preserve the capability-first architecture and do not turn the project into a bundled model catalogue or a generic chat interface.

## Before proposing code

1. Read `AGENTS.md`.
2. Read the product and architecture indexes.
3. Identify the relevant gate and ADR.
4. Search open issues and decisions.
5. State the capability, target profile, evidence, and rollback.
6. Avoid adding a dependency only because it is popular; compare operational cost and licence.

## Pull request evidence

A pull request should include problem and non-goals, affected capability and contracts, tests, target hardware profile, measured quality/latency/memory/CPU when relevant, licence and provenance changes, and rollback.

Use synthetic, generated, or openly licensed material. Never anonymise a private document merely by changing its filename.

Canonical documentation and code identifiers are in English. Make state and uncertainty explicit, prefer replaceable components, avoid hidden global state and silent fallback, and provide typed schemas for cross-component contracts.
