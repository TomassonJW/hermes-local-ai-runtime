# Model storage

## Goals

- immutable artefacts;
- deduplication;
- exact provenance;
- atomic promotion;
- quota and disk visibility;
- safe cleanup;
- shared read-only access by workers;
- future CPU/GPU reuse where formats permit.

## Candidate layout

```text
model-store/
  blobs/sha256/<hash>
  manifests/<artefact-id>.json
  aliases/<alias>.json
  staging/<download-id>/
  quarantine/<id>/
  notices/
```

An alias is a small atomic reference to an immutable manifest. Workers never mutate model blobs.

## Download

- stage on same filesystem where possible for atomic rename;
- stream hash;
- enforce expected size/quota;
- verify source and revision;
- preserve original filename in manifest;
- quarantine on mismatch;
- no execute/load before licence and hash gate.

## Conversion

Conversion produces a new artefact identity with:

- source artefact hashes;
- tool repository/revision/version;
- command/parameters;
- environment;
- output hash;
- quantisation;
- validation.

## Quota

Separate:

- approved route artefacts;
- rollback artefacts;
- candidate/staging;
- cache/temp.

Candidate downloads cannot evict approved/rollback artefacts automatically.

## Cleanup

Dry-run lists:

- alias dependencies;
- active leases;
- route dependencies;
- benchmark references;
- disk reclaimed;
- notice retention.

Deletion requires operator scope and a checkpoint when it affects rollback.

## Backup

Back up manifests, aliases, notices, and exact download sources. Model blobs may be excluded only when reproducible redownload is proven.
