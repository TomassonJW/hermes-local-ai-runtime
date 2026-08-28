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

Do not enable the shipped systemd user unit without a later explicit decision.
