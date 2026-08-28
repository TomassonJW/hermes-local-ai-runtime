#!/usr/bin/env python3
"""Consumer-side example: persist embeddings without model filenames.

The runtime never opens this database. A different space_id means re-embed.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.vectors import persist_records, retrieve


def main() -> int:
    db = Path("consumer-vectors.sqlite")
    space = "text.embed@1.0.0/balanced"
    records = [
        {
            "id": "invoice-42",
            "vector": [0.9, 0.1, 0.0],
            "dimensions": 3,
            "normalisation": "l2",
            "space_id": space,
        },
        {
            "id": "recipe-7",
            "vector": [0.0, 0.1, 0.9],
            "dimensions": 3,
            "normalisation": "l2",
            "space_id": space,
        },
    ]
    persist_records(db, records)
    hits = retrieve(db, [1.0, 0.0, 0.0], space_id_value=space, top_k=1)
    print(json.dumps({"top": hits[0]["id"], "space_id": space}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
