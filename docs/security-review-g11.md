# Security review G-11 - 2026-08-28

Scope: public source candidate on loopback. Not a production support statement.

## Held

- Listen host is `127.0.0.1` in config load.
- Tokens come from the environment, not Git.
- Consumer paths are rejected; uploads use volatile ids.
- Prefix install refuses Proxmox and `/usr`.
- Request payloads are not logged by default.

## Open

- systemd user services are enabled since 2026-08-28 (ADR-0017): the runtime and
  model router run under the `hermes` user on loopback, with crash restart. No
  system-wide unit, no root, no public listener.
- Model weights live outside Git and are not promoted.
- No public listener review (none is shipped).
- Hermes `config.yaml` is untouched.

## Verdict

Safe to publish as source. Not approved as a production service.
