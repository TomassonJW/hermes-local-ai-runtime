# Operational security boundaries

## Green actions

May be automated after takeover when local and reversible:

- read repository and public docs;
- run validation/tests;
- inspect public-safe runtime metadata;
- create synthetic fixtures;
- run unit tests and ephemeral local mocks;
- update code/docs in an isolated branch;
- calculate hashes;
- stop a failed development process started by the current session.

## Orange actions

Require a written plan, impact, and rollback before execution:

- install packages or binaries;
- create users, directories, services, or containers;
- download model weights;
- open a local/tailnet listener;
- alter resource limits;
- migrate state;
- promote/deprecate routes;
- enable payload debug capture;
- integrate a consumer application;
- connect a remote worker;
- use private corpora.

## Red actions

Require explicit human approval:

- public exposure;
- cloud fallback with non-public data;
- delete model/state/backups irreversibly;
- modify Proxmox or unrelated infrastructure;
- handle credentials outside the declared secret mechanism;
- publish private benchmark material;
- accept a restrictive licence with material consequences;
- spend money or acquire hardware;
- automatically update production routes;
- send external messages.

## Secret handling

- environment variable or root-readable secret file;
- never CLI arguments when process list would expose them;
- never config committed to Git;
- never rendered in UI/log/support bundle;
- rotation without route recreation;
- consumer-scoped tokens;
- operator credentials separated.

## Runtime permissions

Control plane may:

- read public config;
- read/write its metadata state;
- create bounded temp inputs;
- invoke registered workers;
- read immutable model artefacts;
- emit metadata logs/metrics.

Control plane may not:

- read arbitrary home directories;
- access Proxmox;
- read Hermes auth/profile/memory;
- access application databases;
- execute arbitrary caller commands;
- modify its own source from API requests.

## Incident response candidate

1. disable non-loopback route;
2. stop admission;
3. drain/cancel jobs;
4. preserve metadata evidence without payload expansion;
5. rotate relevant credentials;
6. identify affected consumers/routes/versions;
7. rollback service/model route;
8. notify through private process;
9. publish public advisory only when safe.
