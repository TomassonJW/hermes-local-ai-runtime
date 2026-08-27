# Security policy

## Supported state

The repository is currently a design and engineering bootstrap. No runtime release is supported yet.

Security reports about repository content, planned architecture, dependency selection, or future implementation are still useful. Do not attach secrets, private documents, model-provider credentials, or production request payloads to a public issue.

## Reporting

Use a private GitHub security advisory when available. Otherwise contact the repository owner through a private channel already known to you. Public issues may be used only for non-sensitive security hardening ideas.

Include the affected version or commit, threat model, a synthetic reproduction, expected and observed behaviour, and whether exploitation exposes data, executes code, changes routing, bypasses admission, or creates public access.

## Security baseline

- bind to loopback only;
- explicit authentication for any non-loopback listener;
- no request-content logging by default;
- secrets supplied at runtime, never in Git;
- model artefacts verified by revision and hash;
- no arbitrary command templates from API callers;
- no arbitrary filesystem path access;
- bounded upload size, decoded-image size, page count, audio duration, token budget, and execution time;
- consumer-scoped credentials and rate limits;
- no automatic cloud fallback;
- no model auto-promotion;
- least-privilege workers and writable directories;
- explicit licence acceptance where required;
- documented rollback before service activation.

## Public disclosure boundary

Do not publish real Hermes network coordinates, private benchmark corpora, personal documents, invoices, audio, screenshots, extracted fields, auth files, or raw production-like logs.

A model is code-adjacent supply-chain data. Promotion requires a pinned source revision, hash, licence record, compatible runtime version, conversion provenance when applicable, and benchmark evidence on the target hardware profile.
