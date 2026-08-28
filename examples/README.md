# Consumer embedding examples

Python: `examples/embed_consumer.py`
TypeScript: `examples/embed_consumer.ts`

These helpers run **in the consumer**. The runtime never opens the consumer
database. Persist `id`, `vector`, `dimensions`, `normalisation`, `space_id`.
Never persist a GGUF or ONNX filename. A different `space_id` means re-embed.
