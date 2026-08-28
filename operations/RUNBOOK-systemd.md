# Runbook - systemd user services

Enabled 2026-08-28 (ADR-0017). Both processes run as **user** services under
`hermes`, on loopback only. No root, no system-wide unit.

| Unit | Role | Port |
|---|---|---|
| `hlair-llama-swap.service` | model router (loads/unloads GGUF on demand) | `127.0.0.1:8840` |
| `hlair-runtime.service` | capability controller + console | `127.0.0.1:8830` |
| `hlair.target` | groups both | - |

## Daily commands

```bash
# status of the pair
systemctl --user status hlair-runtime.service hlair-llama-swap.service

# start / stop / restart everything
systemctl --user start hlair.target
systemctl --user stop hlair.target
systemctl --user restart hlair-runtime.service

# live logs
journalctl --user -u hlair-runtime.service -f
journalctl --user -u hlair-llama-swap.service -n 50
```

## Health check

```bash
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8830/healthz      # 200
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8840/v1/models    # 200
```

**Check 8840 too.** A healthy controller with a dead router still answers
`/healthz` while every model-backed capability fails. That is precisely how the
2026-08-28 outage hid itself.

## Boot behaviour

`Linger=yes` is set for the `hermes` user, so the units start at boot without an
interactive login. Verify with:

```bash
systemctl --user is-enabled hlair.target hlair-runtime.service hlair-llama-swap.service
loginctl show-user hermes | grep Linger
```

## Auth token

The runtime reads `state/ui01.token` itself (mode `0600`, gitignored). The token
is **never** placed in the unit file or the environment. If the file is missing
or world-readable, startup refuses with an explicit message; fix the file rather
than exporting a variable.

## Rollback

```bash
systemctl --user disable --now hlair.target hlair-runtime.service hlair-llama-swap.service
rm ~/.config/systemd/user/hlair-runtime.service \
   ~/.config/systemd/user/hlair-llama-swap.service \
   ~/.config/systemd/user/hlair.target
systemctl --user daemon-reload
```

That returns the host to session-owned processes. Reference copies of the units
live in `packaging/systemd/`.

## Known constraints

- **Absolute paths.** The units hardcode the project directory; moving the
  project breaks them. Edit the units and `daemon-reload`.
- **Project interpreter.** `ExecStart` uses the project venv
  (`../.venv/bin/python3`), not `/usr/bin/python3`, which has no `uvicorn`.
- **`ProtectKernelModules` is unusable** in a user unit: it needs capability
  dropping a `systemd --user` manager cannot perform, and the service
  restart-loops on `status=218/CAPABILITIES`. Do not re-add it.
