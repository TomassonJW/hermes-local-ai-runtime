# UI-01 live console

Date: 2026-08-28

## Authorisation

Thomas: GO runtime allumé + cockpit live (UI-01).

## What runs

- Control plane + static UI on `127.0.0.1:8830` (Tailscale path
  `/apps/local-ai-runtime/` unchanged).
- llama-swap on `127.0.0.1:8840`.
- systemd: not enabled. Processes are session services, not a boot unit.

## Console auth

GET `/api/v1/console/session` sets HttpOnly cookie `hlair_console`.
Bearer tokens remain for apps. Token file is outside Git.

## Not done

systemd enable, UI accepted verdict, Hermes skill install, Sillage wiring,
production support.