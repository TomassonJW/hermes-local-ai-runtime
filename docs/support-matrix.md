# Support matrix

Supported:

- OS: Ubuntu 24.04
- Arch: x86_64
- Listen: 127.0.0.1 only
- Install: prefix via `python3 -m installkit`
- Service: systemd user unit shipped, not enabled

Unsupported: other OS/arch, GPU, public listeners, Windows, macOS,
container images, Proxmox mutation.

Evidence: `packaging/matrix.yaml`.
