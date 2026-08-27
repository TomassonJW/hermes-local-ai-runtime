# Installation plan

This document is a target design, not an instruction to mutate the current server before gates.

## Installation principles

- runs inside a supported Linux environment;
- no Proxmox dependency;
- loopback listener by default;
- dedicated Unix user or rootless container;
- least privilege;
- separate config, state, cache, logs, temporary work, and immutable model store;
- explicit resource controls;
- no model bundled or downloaded automatically;
- idempotent install;
- complete uninstall;
- upgrade rollback.

## Candidate installation phases

### Probe

Read-only:

- architecture and CPU features;
- allocated CPU/RAM;
- disk paths and free space;
- cgroup/systemd/container support;
- existing port conflict;
- no secret output.

### Plan

Display:

- packages/binaries;
- versions and sources;
- disk impact;
- users/groups;
- paths;
- service and listener;
- resource limits;
- rollback;
- model downloads separately.

### Apply

Only after explicit gate:

- create least-privilege identity/paths;
- install pinned control plane and engine artefacts;
- install config with loopback;
- validate before enable;
- enable/start;
- smoke test;
- record installation manifest.

### Model add

Separate command/action:

- display source, revision, licence, files, size;
- require approval;
- download staging;
- verify hash;
- smoke test;
- no route promotion.

## Candidate deployment shape

The spike chooses among:

### Native/hybrid

- compiled `llama.cpp` and `whisper.cpp` binaries;
- isolated Python environments for control plane and Paddle/ONNX workers;
- systemd services/sockets;
- cgroup v2 controls.

### Rootless containers

- image per worker family;
- persistent model/state volumes;
- explicit CPU/memory;
- loopback or private bridge;
- no privileged container.

### LocalAI substrate

- pinned LocalAI deployment;
- thin HLAIR control plane/adapters;
- same model store, route, evaluation, and policy contracts.

## Verification after install

- service identity and permissions;
- listener only where expected;
- health/readiness;
- resource limits visible;
- no model or route silently active;
- logs contain no payload;
- restart;
- uninstall dry run;
- rollback checkpoint.

## Unsupported shortcuts

- `curl | sudo sh` without pin/review;
- running all workers as Hermes user with broad sudo;
- downloading floating `latest`;
- exposing `0.0.0.0`;
- sharing one writable directory with unrelated applications;
- installing desktop LM Studio as the server authority;
- modifying hypervisor configuration from the app installer.
