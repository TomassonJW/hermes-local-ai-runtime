"""Deterministic CPU specialists for synthetic object and similarity tasks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image


def assess_image(path: Path) -> dict[str, Any]:
    with Image.open(path) as image:
        image = image.convert("RGB")
        width, height = image.size
    too_small = min(width, height) < 48
    return {
        "width": width,
        "height": height,
        "review_required": too_small,
        "unsupported": too_small,
        "warnings": (
            [{"code": "IMAGE_TOO_SMALL", "message": "image is too small to read reliably"}]
            if too_small
            else []
        ),
    }


def average_hash(path: Path, size: int = 8) -> str:
    with Image.open(path) as image:
        grey = image.convert("L").resize((size, size), Image.Resampling.LANCZOS)
        pixels = list(grey.getdata())
    mean = sum(pixels) / len(pixels)
    bits = "".join("1" if pixel >= mean else "0" for pixel in pixels)
    return f"{int(bits, 2):0{size * size // 4}x}"


def hamming_hex(left: str, right: str) -> int:
    return bin(int(left, 16) ^ int(right, 16)).count("1")


def similarity(path_a: Path, path_b: Path) -> dict[str, Any]:
    hash_a = average_hash(path_a)
    hash_b = average_hash(path_b)
    distance = hamming_hex(hash_a, hash_b)
    bits = max(len(hash_a), len(hash_b)) * 4
    score = 1.0 - (distance / bits)
    relation = "near_duplicate" if score >= 0.90 else "different"
    return {
        "hash_a": hash_a,
        "hash_b": hash_b,
        "hamming": distance,
        "score": round(score, 4),
        "relation": relation,
        "engine": "average-hash",
        "warnings": [
            {
                "code": "HASH_NOT_SEMANTIC",
                "message": "perceptual hash is not semantic similarity",
            }
        ],
    }


def detect_saturated_boxes(path: Path, min_pixels: int = 80) -> dict[str, Any]:
    """Label saturated red/blue rectangles on a synthetic canvas."""

    with Image.open(path) as image:
        rgb = image.convert("RGB")
        width, height = rgb.size
        pixels = rgb.load()
        assert pixels is not None
        visited = [[False] * width for _ in range(height)]
        boxes: list[dict[str, Any]] = []

        def colour_of(r: int, g: int, b: int) -> str | None:
            if r >= 180 and g < 80 and b < 80:
                return "red-object"
            if b >= 180 and r < 80 and g < 80:
                return "blue-object"
            return None

        for y in range(height):
            for x in range(width):
                if visited[y][x]:
                    continue
                r, g, b = pixels[x, y]
                label = colour_of(r, g, b)
                if label is None:
                    visited[y][x] = True
                    continue
                stack = [(x, y)]
                visited[y][x] = True
                min_x = max_x = x
                min_y = max_y = y
                count = 0
                while stack:
                    cx, cy = stack.pop()
                    count += 1
                    min_x, max_x = min(min_x, cx), max(max_x, cx)
                    min_y, max_y = min(min_y, cy), max(max_y, cy)
                    for nx, ny in (
                        (cx + 1, cy),
                        (cx - 1, cy),
                        (cx, cy + 1),
                        (cx, cy - 1),
                    ):
                        if 0 <= nx < width and 0 <= ny < height and not visited[ny][nx]:
                            nr, ng, nb = pixels[nx, ny]
                            if colour_of(nr, ng, nb) == label:
                                visited[ny][nx] = True
                                stack.append((nx, ny))
                            else:
                                visited[ny][nx] = True
                if count >= min_pixels:
                    boxes.append(
                        {
                            "label": label,
                            "score": 1.0,
                            "bbox": [min_x, min_y, max_x - min_x + 1, max_y - min_y + 1],
                        }
                    )
    return {
        "objects": boxes,
        "engine": "saturated-box-detector",
        "warnings": [
            {
                "code": "SYNTHETIC_DETECTOR",
                "message": "specialist is limited to saturated red/blue synthetic shapes",
            }
        ],
        "review_required": False,
    }
