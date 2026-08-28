# API compatibility policy

The native `/api/v1` capability/job API is the contract. The OpenAI-compatible
facade is an adapter, not the source of truth.

## Compatibility

- Additive OpenAPI fields may appear.
- Removing or renaming a native field marked `implemented-g05` or later is a
  breaking change and needs an ADR.
- Consumers must select `capability` + `profile`, never a checkpoint filename.
- `accurate` never means cloud.

## Tests

`tests/test_runtime_g05.py` checks that implemented OpenAPI routes match the
running app. G-07 and G-08 adapters are included in that set.
