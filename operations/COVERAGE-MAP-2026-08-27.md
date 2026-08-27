# Coverage map — requirements to files and gates

Produced during G-01 takeover (2026-08-27). Maps every bootstrap requirement
class to its authoritative files and controlling gate. Verified by reading the
full corpus at commit `c02810c` (baseline `1907087` present on
`baseline/v0.1.0`).

## Product authority

| Requirement | Authoritative files | Gate |
| --- | --- | --- |
| Mission, authority order, session discipline | `AGENTS.md` | G-00 |
| Baseline anchor | `BASELINE.md` | G-00 |
| Provenance, sources, redactions, omissions | `provenance/COMPILATION-MANIFEST.yml`, `provenance/SOURCE-MAP.md`, `provenance/OMISSIONS-AND-REDACTIONS.md`, `provenance/RESEARCH-SOURCES.md` | G-00 |
| Vision, positioning, kernel definition | `product/01-vision-and-positioning.md` | UI-00→G-11 |
| Users and use cases | `product/02-users-and-use-cases.md` | UI-00, G-05 |
| Capability contracts (P0/P1 map) | `product/03-capability-map.md`, `contracts/capabilities.v1.yaml` | G-05 |
| Scope and non-goals, boundaries | `product/04-scope-and-non-goals.md` | all |
| Success metrics and anti-metrics | `product/05-success-metrics.md` | G-04→G-11 |
| Risk register R-01..R-20 | `product/06-risk-register.md` | all |
| Quality, abstention, fallback policy | `product/07-quality-and-fallback-policy.md` | G-06, G-07 |

## Architecture

| Requirement | Authoritative files | Gate |
| --- | --- | --- |
| Trust zones, data classes | `architecture/01-system-context.md` | G-05 |
| Control plane modules, job/worker states | `architecture/02-control-plane-and-workers.md` | G-03, G-05 |
| Resource budget, admission, residency | `architecture/03-resource-governance.md`, `config/hardware-profiles/*.yaml` | G-04 |
| Network, auth scopes, inputs, logging | `architecture/04-security-and-data-boundaries.md`, `SECURITY.md` | G-04, G-09 |
| Deployment profiles A–D | `architecture/05-deployment-profiles.md` | G-09 |
| Model lifecycle states and promotion | `architecture/06-model-lifecycle.md`, `registry/*.yaml`, `registry/LICENSE-POLICY.md` | G-03+ |
| Hermes integration surfaces | `architecture/07-hermes-integration.md`, `integration/hermes/*`, `config/hermes/*.example.yaml` | Mission 07 |
| Dual API and job envelope | `architecture/08-api-and-job-model.md`, `contracts/openapi.yaml`, `schemas/*.json`, `contracts/error-catalog.md` | G-05 |
| Future GPU/distributed workers | `architecture/09-future-gpu-and-distributed-workers.md` | Phase 8 |
| Observability and provenance | `architecture/10-observability-and-provenance.md`, `operations/OBSERVABILITY.md` | G-05, G-09 |

## Execution and operations

| Requirement | Authoritative files | Gate |
| --- | --- | --- |
| Hard permission boundaries | `GATES.md` | all |
| Phase sequence | `ROADMAP.md` | all |
| Active work slice | `BACKLOG.md`, `STATE.md`, `HANDOFF.md` | G-01 |
| Missions 00–08 | `missions/00..08*.md` | per mission |
| Accepted ADRs 0001–0009 | `docs/adr/*.md`, `DECISIONS.md` | structural changes |
| Installation/backup/rollback/storage plans | `operations/INSTALLATION-PLAN.md`, `operations/BACKUP-ROLLBACK.md`, `operations/MODEL-STORAGE.md`, `operations/SECURITY-BOUNDARIES.md` | G-09 |
| Benchmarks and evaluation matrices | `benchmarks/*` | G-03→G-08 |
| Live VM truth (this takeover) | `operations/LIVE-PROFILE-2026-08-27.md` | G-01 |
| Validation harness | `scripts/validate_bootstrap.py`, `tests/test_bootstrap.py`, `.github/workflows/validate.yml`, `Makefile`, `requirements-dev.txt`, `pyproject.toml` | G-00 |

## UI

| Requirement | Authoritative files | Gate |
| --- | --- | --- |
| Pinned UI canon | `TomassonJW/canonical-ui-design` @ `4d720bf` v1.3.0 (external pin) | UI-00 |
| Local UI contract, 8 pages, state honesty | `ui/LOCAL-UI-CONTRACT.md` | UI-00 |
| UI-00 acceptance checklist | `ui/UI-00-ACCEPTANCE.md` | UI-00 |
| UI-00 mission | `missions/01-ui-00-shell.md` | UI-00 |

## Governance and community

| Requirement | Authoritative files | Gate |
| --- | --- | --- |
| Licence (Apache-2.0) | `LICENSE`, `docs/adr/0007-apache-2.0.md` | G-11 |
| Contribution/security/conduct | `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `.github/*` | G-11 |
| Translation policy | `TRANSLATION_POLICY.md` | G-00 |

## Coverage verdict

- Every file listed in `provenance/COMPILATION-MANIFEST.yml` `files:` exists in
  the working tree. Validator: PASS. Tests: 5/5 PASS (pinned venv).
- Every gate G-00→G-11 + UI-00 has at least one authoritative file; no orphan
  requirement identified.
- Gaps are the ones already declared in the manifest `omissions:` block
  (framework, packaging, metadata DB, GPU vendor, fixtures, artefact hashes,
  live Hermes config keys) — all pending later gates, none blocking UI-00.
