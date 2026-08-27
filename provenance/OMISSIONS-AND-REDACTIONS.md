# Omissions and redactions

## Redacted from the public repository

- private Notion URLs, IDs, and workspace structure;
- private GitHub repository contents beyond public-safe decision pins;
- server IPs, tailnet hostnames, credentials, provider configuration, and auth files;
- Hermes memory, profile, sessions, and personal context;
- Sillage documents, suppliers, amounts, and private corpus filenames;
- raw system command output;
- any secret-bearing path or log.

## Deliberately omitted because not decided

- backend framework;
- metadata database;
- exact service/container topology;
- package manager and release packaging;
- object detection and image embedding model families;
- model artefact revisions and hashes;
- exact CPU presets;
- GPU vendor/device/backend;
- cloud provider routes;
- final Hermes configuration keys;
- public release support matrix.

## Why omission is correct

These are implementation or future-hardware decisions whose premature selection would create lock-in or false confidence. Missions and gates define how they become decisions.

## No hidden source dependency

The compiled repository contains enough product, architecture, gates, contracts, and UI detail for Hermes to continue without private source access.
