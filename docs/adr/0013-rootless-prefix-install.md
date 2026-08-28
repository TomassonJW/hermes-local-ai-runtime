# ADR-0013 - Rootless prefix install, systemd shipped but not enabled

- Status: Accepted
- Date: 2026-08-28
- Decision owners: Hermes (implementation), Thomas Jankowski (lot GO)
- Related gates: G-09

## Context

G-09 requires a fresh supported Linux install, loopback default, explicit
paths and quotas, uninstall/rollback, notices, and upgrade recovery. A
permanent service still needs a later install decision.

## Options considered

1. Native prefix plus optional systemd user unit, not enabled by default.
2. Rootless container as the only install path.
3. System-wide package that enables a service immediately.

## Decision

Option 1. The installer writes a prefix with config, copied control plane,
model-store layout, notices, SBOM and a user unit file. It never enables
systemd, never downloads models, never mutates Proxmox, and refuses
non-loopback listen.

## Consequences

Operators can install and remove a prefix without touching the hypervisor.
A later lot may enable the user unit after an explicit decision.

## Validation

Prefix install, loopback config load, notices/SBOM present, model-store
quota, backup/upgrade/rollback, uninstall, and refusal of /etc/pve and /usr.

## Rollback or amendment

Uninstall the prefix. The shipped unit is unused until a later decision.
