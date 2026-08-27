# Quality, abstention and fallback policy

## Position

A small CPU vision model can replace many routine bounded vision calls, but cannot be presumed to match frontier multimodal models across all tasks. Quality is a routing decision from evidence, not parameter count or one demo.

## Three-layer local vision

1. Deterministic/native and specialists: PDF text, preprocessing, OCR, layout, object coordinates, image embeddings.
2. General local VLM: open image questions, UI description, semantic interpretation, ambiguity and schema extraction.
3. Escalation: clearer image, crop/split, stronger local route, human review or explicitly authorised remote model.

Remote fallback is never implied by `accurate`.

## Hermes modes

With text-only main model, Hermes auxiliary vision returns text to the main model; pixels are lost. The vision endpoint must answer the actual question, not only caption.

With future multimodal main model served by the runtime, original image remains in the main interaction and is preferable for complex visual reasoning when hardware permits.

## Mandatory abstention

Return review/unsupported for insufficient resolution/crop, unreadable tiny text, page/image count over policy, unsupported cross-image reasoning, poor calibration, specialist/VLM disagreement, deterministic invariant failure, high-stakes task, materially degraded resource preset or unapproved licence/provenance.

## Confidence

Never use model self-confidence alone. Combine OCR/detection score, schema validation, deterministic invariants, route agreement, rerank margin, image quality, benchmark calibration, missing fields and degradation warnings. Runtime returns components; consumer sets business threshold.

## Cloud fallback

Explicit allow boolean, provider allowlist, maximum data class, reason codes, budget, human confirmation and redaction. Default false.

## Promotion

Run the same suite and contract against current stable route; block critical regressions, resource violations, licence uncertainty or incompatible output. Preserve rollback.
