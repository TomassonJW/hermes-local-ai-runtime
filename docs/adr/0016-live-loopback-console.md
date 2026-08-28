# ADR-0016 - Live loopback console (UI-01)

- Status: Accepted
- Date: 2026-08-28
- Decision owners: Hermes (implementation), Thomas Jankowski (GO runtime + UI-01)
- Related gates: UI-01

## Context

Thomas authorised a running loopback runtime and a live cockpit to try
capabilities with files and text.

## Decision

Serve the UI from the control plane on loopback `127.0.0.1:8830`. Authenticate
the browser with an HttpOnly console cookie. Keep bearer tokens for apps.
Profiles (fast / balanced / accurate) are the operator model choice, not GGUF
filenames. Do not enable systemd. Do not claim production support.

## Validation

`tests/test_runtime_ui01.py`, `ui/shell` vitest, live `/healthz` on 8830.