"""Hermes-shaped consumer: discover then invoke text.generate.

No model filename, no engine name, no database credential.
"""

from __future__ import annotations

from .client import RuntimeClient


def answer(client: RuntimeClient, prompt: str) -> str:
    client.require("text.generate")
    result = client.invoke("text.generate", {"text": prompt})
    body = result.get("result") or {}
    return str(body.get("echo") or body.get("text") or body.get("answer") or "")
