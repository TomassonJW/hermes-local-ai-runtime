# Observability and provenance

## Questions

Is runtime ready? What routes exist? What is loaded/running/waiting? Why route selected? CPU/RAM/GPU pressure? Cold load vs inference time? Degraded? Exact model/revision/engine/preset/transforms? Update merely discovered or approved? Rollback possible?

## Metrics

Job counts by capability/status/consumer/profile; queue depth/age; admission reasons; leases; worker states/restarts; load/unload; cold/warm latency; input buckets; peak/idle memory; CPU pressure; swap delta; cache; output validation; review/abstention; fallback by destination/reason; evaluation by suite.

No payload labels. Avoid unbounded high cardinality.

## Logs

Structured metadata: time, request/job/consumer IDs, capability/profile, route/model aliases/IDs, transition, durations, resource decision, warning/error. Omit prompts/images/text/audio/embeddings/extracted fields.

## Provenance in results

Runtime version/commit, API/capability, route/revision, engine/adapter, immutable model artefacts, preset, transformations, cache, timing, resource/degradation, calibration/evaluator where confidence returned.

## Support bundle

Opt-in, public-safe by default: versions, redacted config, metadata events, resource snapshot and health. No secrets/payload/private paths/network unless explicitly reviewed.

Metadata retention configurable; payload retention none by default. Aggregate evaluation can persist without confidential inputs.
