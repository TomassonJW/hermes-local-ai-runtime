# Capability map

Capabilities are versioned product contracts. Engines/models are implementations.

## Foundation

`system.health`, `system.describe`, `capability.list`, `job.submit`, `job.status`, `job.cancel`, `model.list`, `evaluation.run`.

## Text

| Capability | Definition | Priority |
| --- | --- | ---: |
| `text.generate` | Bounded text generation | P1 |
| `text.extract_structured` | Fill caller JSON Schema from text | P0 |
| `text.classify` | Labels with scores/evidence | P0 |
| `text.embed` | Declared vector representation | P0 |
| `search.rerank` | Reorder bounded query/candidate pairs | P0 |

`text.extract_structured` must validate exact schema; JSON-looking prose is not sufficient.

## Vision and documents

| Capability | Definition | Priority |
| --- | --- | ---: |
| `vision.analyze` | Answer open image question | P0 |
| `vision.extract_structured` | Fill JSON Schema from image(s) | P0 |
| `vision.classify` | Bounded labels | P0 |
| `vision.embed` | Image vectors | P1 |
| `vision.detect_objects` | Labels, scores, coordinates | P1 |
| `vision.compare` | Similarity/difference task | P1 |
| `document.text_extract` | Native text/metadata | P0 |
| `document.ocr` | Image-page text | P0 |
| `document.parse` | Layout/tables/reading order | P0 |
| `document.classify` | Document family | P0 |
| `document.extract_structured` | Routed document schema | P0 |

## Audio

`audio.transcribe` P1, `audio.transcribe_stream` P2. Audio embeddings and TTS parked.

## Future disabled

Image generation/editing, video, code-specific generation, agent execution and long-context platform features require amendments.

## Contract requirements

Every capability declares semantic version, media/size limits, sync/async eligibility, input/output schema, profiles `fast|balanced|accurate`, privacy/fallback policy, resource class, timeout/cancellation, provenance, confidence/evidence semantics, warnings/errors and compatibility.

`fast` prefers smallest approved route; `balanced` is default; `accurate` uses strongest approved local route. Accurate never implies cloud.

Direct model override is operator/developer-only for benchmark/debugging.
