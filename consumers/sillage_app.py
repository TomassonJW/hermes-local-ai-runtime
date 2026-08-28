"""Sillage-shaped consumer: extract invoice fields, persist locally.

The runtime never receives a database credential. This module never names a
model file. Sillage does not define the runtime product.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from .client import RuntimeClient


def ingest_invoice(client: RuntimeClient, pdf: Path, db: Path) -> dict:
    client.require("document.extract_structured")
    upload_id = client.upload(pdf.read_bytes(), "application/pdf")
    result = client.invoke("document.extract_structured", {"upload_id": upload_id})
    fields = dict((result.get("result") or {}).get("data") or {})
    invoice_id = str(fields.get("invoice_id") or "")
    amount = fields.get("total_eur")
    db.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS invoices (invoice_id TEXT PRIMARY KEY, amount TEXT)"
        )
        conn.execute(
            "INSERT OR REPLACE INTO invoices(invoice_id, amount) VALUES (?, ?)",
            (invoice_id, "" if amount is None else str(amount)),
        )
        conn.commit()
    return {"invoice_id": invoice_id, "amount": amount, "persisted": True}


def load_invoice(db: Path, invoice_id: str) -> dict | None:
    if not db.is_file():
        return None
    with sqlite3.connect(db) as conn:
        row = conn.execute(
            "SELECT invoice_id, amount FROM invoices WHERE invoice_id = ?",
            (invoice_id,),
        ).fetchone()
    if row is None:
        return None
    return {"invoice_id": row[0], "amount": row[1]}
