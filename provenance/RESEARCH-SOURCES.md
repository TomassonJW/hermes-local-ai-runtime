# Research sources

Accessed 2026-08-27. Official or primary sources are preferred. Candidate discovery does not equal approval.

## Hermes Agent

- Hermes Agent documentation: https://hermes-agent.nousresearch.com/docs/
- Local/custom model configuration: https://hermes-agent.nousresearch.com/docs/user-guide/configuration/
- Vision behaviour and auxiliary model configuration: https://hermes-agent.nousresearch.com/docs/
- MCP integration: https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp/
- Skills system: https://hermes-agent.nousresearch.com/docs/user-guide/features/skills/
- Source repository: https://github.com/NousResearch/hermes-agent

Key architectural use:

- custom OpenAI-compatible endpoints can serve local models;
- auxiliary vision can use a separate model/provider;
- a text-only main model receives a textual vision result, not pixels;
- MCP can expose structured specialised capabilities;
- project/local skills require trust and have a documented frontmatter format.

Exact configuration keys must be tested against the installed Hermes version.

## General inference and lifecycle

- llama.cpp: https://github.com/ggml-org/llama.cpp
- llama.cpp server documentation: https://github.com/ggml-org/llama.cpp/tree/master/tools/server
- llama-swap: https://github.com/mostlygeek/llama-swap
- LocalAI: https://github.com/mudler/LocalAI
- LocalAI documentation: https://localai.io/

Key architectural use:

- `llama.cpp` is the first CPU/general-engine candidate;
- server compatibility, structured output, embeddings, reranking, metrics, and multimodal behaviour are version-tested;
- lifecycle may be delegated to `llama-swap`;
- LocalAI is a required alternative-platform spike.

## Vision and documents

- Qwen3-VL 2B Instruct: https://huggingface.co/Qwen/Qwen3-VL-2B-Instruct
- Qwen3-VL 2B official GGUF: https://huggingface.co/Qwen/Qwen3-VL-2B-Instruct-GGUF
- SmolVLM2 500M: https://huggingface.co/HuggingFaceTB/SmolVLM2-500M-Video-Instruct
- LFM2.5-VL 1.6B: https://huggingface.co/LiquidAI/LFM2.5-VL-1.6B
- PaddleOCR: https://github.com/PaddlePaddle/PaddleOCR
- PaddleOCR documentation: https://www.paddleocr.ai/

Key architectural use:

- Qwen3-VL 2B is the first balanced local VLM candidate because it already proved usable in a CPU experiment and has official GGUF artefacts;
- SmolVLM2 500M is a fast-triage candidate, not a universal replacement;
- LFM is discovery-only until licence review;
- PP-OCR and PaddleOCR-VL remain document specialists.

## Embeddings and reranking

- Qwen3 Embedding and Reranker announcement: https://qwenlm.github.io/blog/qwen3-embedding/
- Qwen3 Embedding 0.6B: https://huggingface.co/Qwen/Qwen3-Embedding-0.6B
- Qwen3 Reranker 0.6B: https://huggingface.co/Qwen/Qwen3-Reranker-0.6B
- FastEmbed: https://github.com/qdrant/fastembed

Key architectural use:

- embeddings retrieve candidates efficiently;
- reranking performs a deeper second-stage query/candidate comparison;
- ONNX candidates must be compared for CPU efficiency.

## Speech

- whisper.cpp: https://github.com/ggml-org/whisper.cpp
- Qwen3-ASR 0.6B: https://huggingface.co/Qwen/Qwen3-ASR-0.6B

Key architectural use:

- `whisper.cpp` is the first CPU baseline;
- model size is selected by measured French quality and real-time factor;
- Qwen ASR is an alternative candidate.

## Source limitations

- upstream benchmarks use different hardware, corpora, prompts, and versions;
- model-card claims are candidate evidence only;
- external pages may change;
- exact source revisions and hashes are recorded at download/evaluation time;
- public research does not substitute for the target VM benchmark.
