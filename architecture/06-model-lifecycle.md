# Model lifecycle

## States

`discovered -> candidate -> compatible -> benchmarked -> approved -> deprecated -> removed`, with `blocked` reachable from any state.

Discovered is metadata only. Candidate permits isolated evaluation after source/licence review. Compatible loads and passes smoke test. Benchmarked has reproducible quality/resource results on a hardware profile. Approved may serve named routes. Deprecated remains for rollback/compatibility. Blocked cannot download/execute/route.

## Artefact identity

Immutable identity includes family/variant, upstream revision, file hash, format/quantisation, vision projector, tokenizer/template, conversion provenance and licence. Human aliases resolve to immutable routes.

## Download

Operator selects candidate; UI displays size/licence/source/profile/disk; explicit approval; staging/quarantine; hash/manifest verification; isolated smoke; atomic store promotion; no route change.

## Updates

UI may show new upstream revision, engine version, compatibility/licence issue and benchmark opportunity. It must not auto-update an approved route.

## Presets

Bind engine/adapter version, context/output, sampling, threads/batch, KV/cache, image policy, prompt/template, structured output, timeout and resource estimate. Presets are model/capability-specific; one universal LM Studio preset does not exist.

## Promotion

Compare current stable route using same corpus/hardware/evaluator/contract/resource limits. Faster with critical quality loss is not promoted; higher quality violating coexistence becomes future-GPU/specialised route.

## Removal

Requires no lease/route dependency/rollback need, metadata and notice retention, atomic deletion and disk accounting.
