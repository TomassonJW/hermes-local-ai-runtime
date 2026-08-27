# Model and engine registry

The registry records candidates and immutable local artefacts. It is not a shopping list and not an approval by popularity.

## Two levels

### Public candidate registry

`candidates.yaml` records:

- upstream family;
- intended capabilities;
- known licence identifier;
- official source;
- why it is worth evaluating;
- known limitations;
- allowed next action.

No candidate file hash exists until an installation downloads an exact artefact.

### Installation registry

Local configuration records:

- exact upstream revision;
- exact downloaded files and SHA-256;
- conversion and quantisation;
- engine compatibility;
- benchmark results;
- route and preset;
- promotion state.

The installation registry may contain local paths but no credentials. Public commits use redacted or synthetic examples.

## Status definitions

- `discovered`: metadata only;
- `candidate`: licence/source review permits isolated evaluation;
- `compatible`: smoke-tested;
- `benchmarked`: measured;
- `approved`: routable;
- `deprecated`: retained for rollback;
- `blocked`: not permitted.

## Rules

- no floating `latest` in an approved route;
- no `trust_remote_code` by default;
- no automatic download;
- no automatic promotion;
- no model licence inherited from this repository;
- no benchmark result without hardware/preset/corpus versions;
- vision projector/tokenizer/template artefacts are part of identity;
- local conversions retain upstream and tool provenance.
