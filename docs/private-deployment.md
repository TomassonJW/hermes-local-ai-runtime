# Private deployment

Default listen address is `127.0.0.1`. A tailnet or reverse proxy is an
operator choice and is not enabled by the installer.

Do not publish real hostnames, tailnet IPs, or tokens in this repository.

Install:

```text
python3 -m installkit plan --prefix /path/to/prefix
python3 -m installkit install --prefix /path/to/prefix
python3 -m installkit uninstall --prefix /path/to/prefix --purge
```

The prefix installer's own unit stays shipped-not-enabled. The live UI-01
deployment instead runs the units in `packaging/systemd/`, enabled under the
user scope since 2026-08-28 (ADR-0017); see `operations/RUNBOOK-systemd.md`.
