"""Native PDF text, image-only detection, Tesseract OCR and schema fill."""

from __future__ import annotations

import csv
import io
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


class DocumentError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message

INVOICE_ID_RE = re.compile(r"SYN-\d{4}")
AMOUNT_RE = re.compile(r"(\d{1,3}(?:[ .]\d{3})*[.,]\d{2})\s*EUR", re.I)
DATE_ISO_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
DATE_FR_RE = re.compile(r"\d{2}/\d{2}/\d{4}")


def parse_fr_amount(raw: str) -> float:
    token = raw.strip().replace(" ", "").replace("\u00a0", "")
    if "," in token and "." in token:
        token = token.replace(".", "").replace(",", ".")
    elif "," in token:
        token = token.replace(",", ".")
    return float(token)


def _run(args: list[str], timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def extract_pdf_text(path: Path) -> dict[str, Any]:
    if shutil.which("pdftotext") is None:
        raise DocumentError("CAPABILITY_UNAVAILABLE", "pdftotext is not installed")
    data = path.read_bytes()[:5]
    if data != b"%PDF-":
        raise DocumentError("INVALID_INPUT", "document.text_extract requires a PDF")
    proc = _run(["pdftotext", "-layout", "-enc", "UTF-8", str(path), "-"])
    if proc.returncode != 0:
        raise DocumentError("WORKER_CRASHED", "native PDF extraction failed")
    text = proc.stdout or ""
    stripped = text.strip()
    image_only = len(stripped) < 8
    return {
        "pages": [{"page": 1, "text": text, "char_count": len(text)}],
        "image_only": image_only,
        "engine": "pdftotext",
        "engine_version": "poppler",
        "review_required": image_only,
        "warnings": (
            [{"code": "IMAGE_ONLY_PDF", "message": "image-only PDF; OCR is required"}]
            if image_only
            else []
        ),
    }


def _parse_tsv(tsv: str, page: int) -> tuple[str, list[dict[str, Any]], list[float]]:
    reader = csv.DictReader(io.StringIO(tsv), delimiter="\t")
    words: list[str] = []
    regions: list[dict[str, Any]] = []
    confs: list[float] = []
    for row in reader:
        token = (row.get("text") or "").strip()
        if not token:
            continue
        try:
            conf = float(row.get("conf", "-1"))
        except ValueError:
            conf = -1.0
        if conf < 0:
            continue
        confs.append(conf)
        words.append(token)
        regions.append(
            {
                "page": page,
                "text": token,
                "confidence": conf / 100.0,
                "bbox": [
                    int(row.get("left") or 0),
                    int(row.get("top") or 0),
                    int(row.get("width") or 0),
                    int(row.get("height") or 0),
                ],
            }
        )
    return " ".join(words), regions, confs


def ocr_image(path: Path, *, lang: str = "fra+eng", page: int = 1) -> dict[str, Any]:
    if shutil.which("tesseract") is None:
        raise DocumentError("CAPABILITY_UNAVAILABLE", "tesseract is not installed")
    proc = _run(["tesseract", str(path), "stdout", "-l", lang, "tsv"], timeout=90)
    if proc.returncode != 0:
        raise DocumentError("WORKER_CRASHED", "tesseract failed")
    text, regions, confs = _parse_tsv(proc.stdout or "", page)
    mean_conf = sum(confs) / len(confs) / 100.0 if confs else 0.0
    review = mean_conf < 0.60 or not text.strip()
    warnings = []
    if review:
        warnings.append(
            {
                "code": "LOW_OCR_CONFIDENCE",
                "message": "low OCR confidence or empty text; human review required",
            }
        )
    return {
        "text": text,
        "regions": regions,
        "mean_confidence": round(mean_conf, 4),
        "review_required": review,
        "warnings": warnings,
        "engine": "tesseract",
        "engine_version": "5",
        "lang": lang,
    }


def rasterize_pdf(path: Path, dest_dir: Path) -> list[Path]:
    if shutil.which("pdftoppm") is None:
        raise DocumentError("CAPABILITY_UNAVAILABLE", "pdftoppm is not installed")
    dest_dir.mkdir(parents=True, exist_ok=True)
    prefix = dest_dir / "page"
    proc = _run(["pdftoppm", "-png", str(path), str(prefix)], timeout=90)
    if proc.returncode != 0:
        raise DocumentError("WORKER_CRASHED", "PDF rasterization failed")
    pages = sorted(dest_dir.glob("page*.png"))
    if not pages:
        raise DocumentError("WORKER_CRASHED", "PDF rasterization produced no pages")
    return pages


def ocr_file(path: Path) -> dict[str, Any]:
    header = path.read_bytes()[:5]
    pages_out: list[dict[str, Any]] = []
    all_regions: list[dict[str, Any]] = []
    warnings: list[str] = []
    review = False
    if header == b"%PDF-":
        raster_dir = path.parent / f"{path.name}.raster"
        images = rasterize_pdf(path, raster_dir)
        texts: list[str] = []
        for index, image in enumerate(images, start=1):
            page = ocr_image(image, page=index)
            texts.append(page["text"])
            all_regions.extend(page["regions"])
            warnings.extend(page["warnings"])
            review = review or page["review_required"]
            pages_out.append({"page": index, "text": page["text"], "mean_confidence": page["mean_confidence"]})
        text = "\n".join(texts)
        mean = (
            sum(p["mean_confidence"] for p in pages_out) / len(pages_out) if pages_out else 0.0
        )
    else:
        page = ocr_image(path, page=1)
        text = page["text"]
        mean = page["mean_confidence"]
        all_regions = page["regions"]
        warnings = page["warnings"]
        review = page["review_required"]
        pages_out = [{"page": 1, "text": text, "mean_confidence": mean}]
    return {
        "pages": pages_out,
        "text": text,
        "regions": all_regions,
        "mean_confidence": round(mean, 4),
        "review_required": review,
        "warnings": warnings,
        "engine": "tesseract",
        "engine_version": "5",
    }


def extract_invoice_fields(text: str) -> dict[str, Any]:
    invoice = INVOICE_ID_RE.search(text)
    amount = AMOUNT_RE.search(text)
    date = DATE_ISO_RE.search(text) or DATE_FR_RE.search(text)
    fields: dict[str, Any] = {}
    missing: list[str] = []
    if invoice:
        fields["invoice_id"] = invoice.group(0)
    else:
        missing.append("invoice_id")
    if amount:
        fields["total_eur"] = parse_fr_amount(amount.group(1))
        fields["total_raw"] = amount.group(1)
    else:
        missing.append("total_eur")
    if date:
        fields["date"] = date.group(0)
    evidence = [
        {"field": key, "quote": str(value)} for key, value in fields.items() if key != "total_eur"
    ]
    return {
        "fields": fields,
        "missing": missing,
        "evidence": evidence,
        "review_required": bool(missing),
    }
