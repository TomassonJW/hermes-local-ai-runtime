# Evaluation matrix

| Family | Quality | Resources | Contract | Failure/abstention |
| --- | --- | --- | --- | --- |
| Native PDF text | extraction coverage, reading order | latency, memory | pages/metadata | encrypted, malformed, image-only |
| OCR | CER/WER, numbers, accents | page/s, RSS | regions/confidence | blur, rotation, handwriting |
| Document parse | layout/table/entity metrics | doc latency, peak RSS | hierarchy/evidence | complex tables, stamps, scans |
| Structured text | exact fields, schema pass | latency, context | JSON Schema | ambiguity, missing values |
| General vision | task-family accuracy | cold/warm time, RSS | answer/evidence | tiny details, multi-image |
| Object detect | mAP/IoU or task score | image/s | coordinates | unknown class, occlusion |
| Image similarity | retrieval recall/precision | embeddings/s | dimensions | near-duplicate edge cases |
| Text embeddings | retrieval nDCG/recall | texts/s, batch RAM | dimensions/normalisation | language/domain drift |
| Reranking | nDCG/MRR, top-1 | pairs/s, latency | ordered indices | long candidates, ties |
| ASR | WER, timestamps, names | real-time factor, RSS | segments/language | noise, music, long files |
| Text generation | task success, schema/tool | tok/s, time-to-first | compatibility | context overflow, refusal |

## Required comparisons

For each route:

- specialist-only;
- general model-only where applicable;
- routed/ensemble pipeline;
- current approved baseline;
- candidate update;
- degraded resource preset;
- cold and warm execution.

## French coverage

Evaluation must include:

- accents and punctuation;
- French dates and decimal formats;
- administrative vocabulary;
- proper names;
- mixed French/English interfaces;
- noisy spoken French;
- multilingual embeddings with French queries and candidates.

## Decision table

| Outcome | Promotion |
| --- | --- |
| Better quality, safe resources | eligible |
| Equal quality, materially lower cost/resources | eligible |
| Better aggregate score, critical regression | blocked or specialised route only |
| Faster but poor abstention | blocked |
| High quality but violates VM budget | future GPU route |
| Licence unclear | blocked |
| Incomplete provenance | blocked |
