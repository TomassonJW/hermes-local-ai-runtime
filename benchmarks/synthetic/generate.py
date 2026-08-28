"""Public-safe synthetic fixtures for G-06 vision/document evaluation."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

FONT = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
BOLD = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")

EXPECTED = {
    "invoice_id": "SYN-0042",
    "total_eur": 123.45,
    "date_iso": "2026-08-28",
    "date_fr": "28/08/2026",
    "error_code": "E42",
    "error_text": "Disk is full",
    "chart_q3": 40,
}

INVOICE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["invoice_id", "total_eur"],
    "properties": {
        "invoice_id": {"type": "string"},
        "total_eur": {"type": "number"},
        "date": {"type": "string"},
    },
}


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    path = BOLD if bold and BOLD.is_file() else FONT
    if path.is_file():
        return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def write_text_pdf(path: Path, lines: list[str]) -> None:
    stream = ["BT", "/F1 12 Tf"]
    for index, line in enumerate(lines):
        if index == 0:
            stream.append(f"72 780 Td ({_pdf_escape(line)}) Tj")
        else:
            stream.append(f"0 -16 Td ({_pdf_escape(line)}) Tj")
    stream.append("ET")
    content = "\n".join(stream).encode("latin-1")
    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        (
            b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n"
        ),
        b"4 0 obj << /Length "
        + str(len(content)).encode("ascii")
        + b" >> stream\n"
        + content
        + b"\nendstream\nendobj\n",
        b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
    ]
    header = b"%PDF-1.4\n"
    offsets = []
    body = bytearray(header)
    for obj in objects:
        offsets.append(len(body))
        body.extend(obj)
    xref_at = len(body)
    xref = [b"xref\n0 6\n0000000000 65535 f \n"]
    for offset in offsets:
        xref.append(f"{offset:010d} 00000 n \n".encode("ascii"))
    body.extend(b"".join(xref))
    body.extend(
        b"trailer << /Size 6 /Root 1 0 R >>\nstartxref\n"
        + str(xref_at).encode("ascii")
        + b"\n%%EOF\n"
    )
    path.write_bytes(bytes(body))


def write_image_pdf(path: Path, image: Image.Image) -> None:
    rgb = image.convert("RGB")
    buffer = io.BytesIO()
    rgb.save(buffer, format="JPEG", quality=90)
    jpeg = buffer.getvalue()
    width, height = rgb.size
    image_obj = (
        f"4 0 obj << /Type /XObject /Subtype /Image /Width {width} "
        f"/Height {height} /ColorSpace /DeviceRGB /BitsPerComponent 8 "
        f"/Filter /DCTDecode /Length {len(jpeg)} >> stream\n"
    ).encode("ascii") + jpeg + b"\nendstream\nendobj\n"
    draw = f"q {width} 0 0 {height} 0 0 cm /Im0 Do Q".encode("ascii")
    contents = (
        b"5 0 obj << /Length "
        + str(len(draw)).encode("ascii")
        + b" >> stream\n"
        + draw
        + b"\nendstream\nendobj\n"
    )
    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        (
            f"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 {width} {height}] "
            f"/Resources << /XObject << /Im0 4 0 R >> >> /Contents 5 0 R >> endobj\n"
        ).encode("ascii"),
        image_obj,
        contents,
    ]
    header = b"%PDF-1.4\n"
    body = bytearray(header)
    offsets = []
    for obj in objects:
        offsets.append(len(body))
        body.extend(obj)
    xref_at = len(body)
    xref = [b"xref\n0 6\n0000000000 65535 f \n"]
    for offset in offsets:
        xref.append(f"{offset:010d} 00000 n \n".encode("ascii"))
    body.extend(b"".join(xref))
    body.extend(
        b"trailer << /Size 6 /Root 1 0 R >>\nstartxref\n"
        + str(xref_at).encode("ascii")
        + b"\n%%EOF\n"
    )
    path.write_bytes(bytes(body))


def _invoice_image() -> Image.Image:
    image = Image.new("RGB", (900, 520), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.rectangle((20, 20, 880, 500), outline=(20, 20, 20), width=3)
    draw.text((40, 40), "Facture SYN-0042", font=_font(36, bold=True), fill=(0, 0, 0))
    draw.text((40, 110), "Client: Atelier Fictif", font=_font(24), fill=(0, 0, 0))
    draw.text((40, 160), "Date: 28/08/2026", font=_font(24), fill=(0, 0, 0))
    draw.text((40, 230), "Total TTC: 123,45 EUR", font=_font(32, bold=True), fill=(0, 0, 0))
    draw.text((40, 300), "Reference interne: DEMO-ONLY", font=_font(22), fill=(40, 40, 40))
    draw.text((40, 400), "Document synthetique - aucune identite reelle.", font=_font(18), fill=(80, 80, 80))
    return image


def _ui_error_image() -> Image.Image:
    image = Image.new("RGB", (720, 420), (245, 246, 248))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 720, 48), fill=(25, 35, 55))
    draw.text((16, 12), "Hermes Demo App", font=_font(20, bold=True), fill=(255, 255, 255))
    draw.rectangle((80, 90, 640, 330), fill=(255, 255, 255), outline=(180, 40, 40), width=3)
    draw.text((110, 120), "Error E42", font=_font(32, bold=True), fill=(180, 40, 40))
    draw.text((110, 180), "Disk is full", font=_font(26), fill=(20, 20, 20))
    draw.rectangle((110, 250, 260, 295), fill=(180, 40, 40))
    draw.text((140, 258), "Retry", font=_font(20, bold=True), fill=(255, 255, 255))
    draw.rectangle((280, 250, 430, 295), outline=(120, 120, 120), width=2)
    draw.text((310, 258), "Cancel", font=_font(20), fill=(40, 40, 40))
    return image


def _tiny_image() -> Image.Image:
    image = Image.new("RGB", (36, 24), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.text((1, 1), "E42", font=_font(7), fill=(180, 180, 180))
    return image


def _chart_image() -> Image.Image:
    image = Image.new("RGB", (640, 400), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.text((20, 12), "Units sold (synthetic)", font=_font(22, bold=True), fill=(0, 0, 0))
    draw.text((20, 50), "Q1=10  Q2=20  Q3=40  Q4=15", font=_font(20), fill=(0, 0, 0))
    origin = (80, 340)
    draw.line((origin[0], 80, origin[0], origin[1]), fill=(0, 0, 0), width=2)
    draw.line((origin[0], origin[1], 600, origin[1]), fill=(0, 0, 0), width=2)
    bars = [("Q1", 10), ("Q2", 20), ("Q3", 40), ("Q4", 15)]
    for index, (label, value) in enumerate(bars):
        x = 120 + index * 110
        height = value * 5
        draw.rectangle((x, origin[1] - height, x + 70, origin[1]), fill=(30, 90, 180))
        draw.text((x + 15, origin[1] + 8), label, font=_font(18), fill=(0, 0, 0))
        draw.text((x + 20, origin[1] - height - 24), str(value), font=_font(18), fill=(0, 0, 0))
    return image


def _objects_image(*, shift: int = 0) -> Image.Image:
    image = Image.new("RGB", (480, 320), (245, 245, 245))
    draw = ImageDraw.Draw(image)
    draw.rectangle((40 + shift, 40, 160 + shift, 160), fill=(220, 20, 20))
    draw.rectangle((260, 120, 420, 260), fill=(20, 40, 220))
    return image


def write_suite(dest: Path) -> dict[str, Any]:
    dest.mkdir(parents=True, exist_ok=True)
    invoice = _invoice_image()
    invoice_png = dest / "invoice-fr.png"
    invoice.save(invoice_png)
    invoice_pdf = dest / "invoice-image-only.pdf"
    write_image_pdf(invoice_pdf, invoice)
    native_pdf = dest / "invoice-native.pdf"
    write_text_pdf(
        native_pdf,
        [
            "INVOICE SYN-0042",
            "Date: 2026-08-28",
            "Client: Atelier Fictif",
            "Total TTC: 123.45 EUR",
            "Synthetic document - no real identity.",
        ],
    )
    ui = dest / "ui-error.png"
    _ui_error_image().save(ui)
    tiny = dest / "ui-tiny.png"
    _tiny_image().save(tiny)
    chart = dest / "chart.png"
    _chart_image().save(chart)
    objects = dest / "objects.png"
    _objects_image().save(objects)
    objects_near = dest / "objects-near.png"
    _objects_image(shift=2).save(objects_near)
    unrelated = dest / "unrelated.png"
    noise = Image.new("RGB", (480, 320), (20, 120, 40))
    draw = ImageDraw.Draw(noise)
    for y in range(0, 320, 16):
        for x in range(0, 480, 16):
            if (x + y) // 16 % 2 == 0:
                draw.rectangle((x, y, x + 15, y + 15), fill=(240, 220, 40))
    noise.save(unrelated)
    return {
        "invoice_png": invoice_png,
        "invoice_image_pdf": invoice_pdf,
        "invoice_native_pdf": native_pdf,
        "ui_error": ui,
        "ui_tiny": tiny,
        "chart": chart,
        "objects": objects,
        "objects_near": objects_near,
        "unrelated": unrelated,
        "expected": EXPECTED,
    }


def main() -> None:
    root = Path(__file__).resolve().parent / "generated"
    write_suite(root)
    print(root)


if __name__ == "__main__":
    main()
