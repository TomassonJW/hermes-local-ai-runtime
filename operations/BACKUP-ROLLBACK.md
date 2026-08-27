# Backup and rollback

## What requires backup

- control-plane metadata database;
- active configuration and route revisions;
- installation manifest;
- model artefact manifests and generated notices;
- evaluation summaries;
- UI/user preferences if server-side;
- service definitions and version pins.

Model binaries may be redownloadable and can be excluded from backup if exact source/revision/hash is retained and restoration time is acceptable.

Payloads and private corpora are not included by default.

## Checkpoints

Create a checkpoint before:

- runtime upgrade;
- metadata migration;
- route promotion;
- model artefact removal;
- engine replacement;
- auth or network change;
- consumer integration change.

A checkpoint records current Git commit, package/image versions, database schema, route config, model manifests, and rollback commands.

## Rollback classes

### Route rollback

Point alias to previous approved route. No binary reinstall if previous artefacts remain.

### Model rollback

Restore previous model/preset/engine compatibility tuple.

### Application rollback

Deploy previous runtime version and run backward-compatible metadata migration or restore checkpoint.

### Installation rollback

Stop and disable services created by the installer, restore config/state checkpoint, remove only paths owned by this installation, preserve user model store unless explicit removal.

## Rules

- differential rollback only;
- no blanket deletion of shared directories;
- validate backup before destructive action;
- test restore on a disposable environment before public release;
- local snapshot is not an independent backup;
- document recovery point and recovery time assumptions;
- state migration must declare forward/backward compatibility.

## Model update safety

An approved model update never deletes the previous artefact until:

- promotion evaluation passes;
- route has run successfully;
- rollback has been tested;
- retention window expires;
- no compatibility consumer depends on it.
