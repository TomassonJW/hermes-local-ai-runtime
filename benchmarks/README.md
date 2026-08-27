# Evaluation framework

A route becomes approved only through reproducible evaluation on a declared hardware profile.

## Evaluation layers

1. **Compatibility:** load, health, one valid result, one invalid input, cancellation.
2. **Contract:** schema, provenance, errors, limits, idempotency.
3. **Quality:** task-specific metrics and reviewed failures.
4. **Resources:** cold/warm latency, RSS, CPU, pressure, swap, queue impact.
5. **Coexistence:** representative other Hermes services remain usable.
6. **Security:** malformed input, path isolation, log redaction, auth and scope.
7. **Licence/provenance:** exact revision, hashes, conversion and notices.
8. **Regression:** compare current approved route and candidate.

## Corpus classes

### Public synthetic

Committed or generated in CI. Used for contract and baseline regression. Must not mimic a real person's identifiable document.

### Public licensed

External datasets with recorded licence and version. Downloaded by tooling, not necessarily redistributed.

### Private mounted

Realistic internal material, outside Git. Results publish only aggregate metrics and public-safe error categories.

### Holdout

Not used for prompt/preset tuning. Required before promotion when sufficient data exists.

## Reproducibility manifest

Every run records:

- suite and corpus version;
- evaluator commit;
- runtime commit;
- hardware profile and probe hash;
- engine and adapter versions;
- model artefacts and hashes;
- preset and route revision;
- start/end time;
- warm/cold state;
- competing service load profile;
- result artefact hashes.

## Reports

Public reports contain:

- configuration;
- aggregate metrics;
- synthetic examples;
- limitations;
- errors that contain no private payload;
- comparison to current route.

Private detailed reports remain local.

## No vendor-score substitution

Upstream benchmarks justify candidate discovery. They do not approve a route on the Hermes VM or prove the user's actual tasks.
