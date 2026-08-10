"""PDF-specific I/O: page triage, native-resolution image extraction, and
PDF rebuild that leaves untouched pages byte-for-byte alone.
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass
from typing import Dict, Optional

import cv2
import fitz
import numpy as np


@dataclass
class PageImage:
    bgr: np.ndarray
    raw_bytes: bytes   # original embedded image bytes, used for EXIF reading
    xref: int


def has_real_text_layer(page: fitz.Page, min_chars: int) -> bool:
    """S1: real extractable text -> born_digital. Filters out OCR/whitespace noise."""
    text = page.get_text("text")
    words = [w for w in text.split() if any(c.isalnum() for c in w)]
    return len(text.strip()) > min_chars and len(words) > 3


def extract_native_image(page: fitz.Page) -> Optional[PageImage]:
    """Extract the page's single full-bleed embedded image at native resolution.

    Returns None (caller should pass through with a warning) for pages with
    zero or multiple images -- multi-image pages are treated as scans/complex.
    """
    images = page.get_images(full=True)
    if len(images) != 1:
        return None
    xref = images[0][0]
    doc = page.parent
    info = doc.extract_image(xref)
    raw_bytes = info["image"]
    arr = np.frombuffer(raw_bytes, dtype=np.uint8)
    bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if bgr is None:
        return None
    return PageImage(bgr=bgr, raw_bytes=raw_bytes, xref=xref)


def encode_jpeg(bgr: np.ndarray, quality: int) -> bytes:
    ok, buf = cv2.imencode(".jpg", bgr, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        raise RuntimeError("JPEG encode failed")
    return buf.tobytes()


def rebuild_pdf(input_path: str, output_path: str, replacements: Dict[int, np.ndarray],
                 jpeg_quality: int) -> None:
    """Write output_path with only the given 0-indexed pages' images replaced.

    Unmodified pages are never decoded/re-encoded. If nothing was modified at
    all, the input file is copied byte-for-byte (do-no-harm minimum bar).
    """
    if not replacements:
        shutil.copyfile(input_path, output_path)
        return

    doc = fitz.open(input_path)
    try:
        for page_idx, warped_bgr in replacements.items():
            page = doc[page_idx]
            images = page.get_images(full=True)
            if len(images) != 1:
                continue
            xref = images[0][0]
            jpeg_bytes = encode_jpeg(warped_bgr, jpeg_quality)
            h, w = warped_bgr.shape[:2]
            # Page.replace_image() spawns a *new* image xref and leaves the old
            # one dangling (breaks the "exactly one image" invariant we rely on
            # downstream). update_stream() keeps the same xref but doesn't know
            # the payload is JPEG, so /Filter and /Width /Height must be set by
            # hand -- otherwise the page ends up declaring the wrong codec/size.
            doc.update_stream(xref, jpeg_bytes, compress=0)
            doc.xref_set_key(xref, "Filter", "/DCTDecode")
            doc.xref_set_key(xref, "Width", str(w))
            doc.xref_set_key(xref, "Height", str(h))
            doc.xref_set_key(xref, "DecodeParms", "null")
        doc.save(output_path)
    finally:
        doc.close()
