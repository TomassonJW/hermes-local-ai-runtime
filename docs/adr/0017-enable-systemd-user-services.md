# ADR-0017 - Enable systemd user services for the runtime

- Status: Accepted
- Date: 2026-08-28
- Decision owners: Thomas Jankowski (explicit request), Hermes (implementation)
- Related gates: UI-01
- Supersedes: the "do not enable systemd" clause of ADR-0016 and ADR-0013

## Context

The runtime and the llama-swap model router ran as shell processes owned by an
interactive session. That kept the bootstrap reversible but had a real cost:
closing the session or rebooting left the console dead, and a crash was
permanent until a human noticed.

The 2026-08-28 outage was exactly this failure mode. llama-swap had died and
nothing restarted it, so four capabilities were down while the controller still
answered `/healthz`.

Thomas explicitly asked to enable systemd, after the two UI-01 live defects
were fixed.

## Decision

Enable **systemd user services**, not system-wide units:

- `hlair-llama-swap.service` - model router on `127.0.0.1:8840`
- `hlair-runtime.service` - capability controller and console on `127.0.0.1:8830`
- `hlair.target` - groups both

User services were chosen because the runtime needs no root, owns no privileged
port, and writes only inside the project tree. `loginctl` lingering was already
enabled, so the units start at boot without an interactive login.
`Restart=on-failure` gives crash recovery. The runtime reads its token from
`state/ui01.token`, so no secret passes through the unit file or the
environment.

The listener stays on loopback. This ADR does not authorise public exposure,
model download, Proxmox mutation, or any system-wide unit.

## Consequences

- The console survives reboot, logout, and crash without human action.
- `journalctl --user -u hlair-runtime` replaces scrollback that died with the
  session.
- Start ordering is declared, so the router precedes the controller by contract
  rather than by luck.
- Accepted cost: a permanent host mutation (reversible via `systemctl --user
  disable --now hlair.target` plus removing three unit files), absolute paths in
  the units, and unattended operation that makes silent degradation easier to
  miss.

## Deviations found while implementing

1. `ProtectKernelModules=yes` cannot be used in a user unit. It requires
   dropping capabilities, which a `systemd --user` manager cannot do; the
   service restart-looped on `status=218/CAPABILITIES`. Removed from both units.
   Remaining hardening matches the working user services on this host.
2. `/usr/bin/python3` is not the project interpreter and has no `uvicorn`. The
   project runs on `../.venv` (CPython 3.11.15 via uv), which was itself missing
   `pillow` and `python-multipart`. Both were installed from the project's own
   pinned `requirements-runtime.txt`, so the venv is self-sufficient and the
   units do not borrow the Hermes agent venv.

## Validation

- Both services `active`; `8830/healthz` and `8840/v1/models` return `200`.
- `SIGKILL` on the controller: systemd restarted it, new PID, `healthz` back to
  `200`.
- Full stop then `start hlair.target` (the boot path) brought both back.
- All three units `enabled`; `Linger=yes`.
- Capability sweep under systemd: 13/13 OK.
