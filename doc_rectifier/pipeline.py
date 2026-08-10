"""Orchestration: process_pdf(), PipelineReport, and the CLI entrypoint."""
from __future__ import annotations

import argparse
import dataclasses
import json
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import cv2
import fitz
import numpy as np

from . import pdf_io
from . import vision
from .vision import Config


@dataclass
class PageReport:
    page: int
    page_type: str
    confidence: float
    signals: Dict[str, float]
    action: str
    method: str
    corners_px: Optional[List[List[float]]]
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)


@dataclass
class PipelineReport:
    input_path: str
    pages: List[PageReport] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"input_path": self.input_path, "pages": [p.to_dict() for p in self.pages]}

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


def _working_copy(img: np.ndarray, max_dim: int) -> Tuple[np.ndarray, float]:
    h, w = img.shape[:2]
    scale = min(1.0, max_dim / max(h, w))
    if scale >= 1.0:
        return img, 1.0
    work = cv2.resize(img, (max(1, int(w * scale)), max(1, int(h * scale))), interpolation=cv2.INTER_AREA)
    return work, scale


def _process_page(page: fitz.Page, idx: int, config: Config, debug_prefix: str) -> Tuple[PageReport, Optional[np.ndarray]]:

    if pdf_io.has_real_text_layer(page, config.text_layer_min_chars):
        return PageReport(idx + 1, "born_digital", 1.0, {}, "passthrough", "none", None, []), None

    img_info = pdf_io.extract_native_image(page)
    if img_info is None:
        return PageReport(idx + 1, "ambiguous", 0.0, {}, "passthrough", "none", None,
                           ["multi_image_or_extract_failed"]), None

    full_img = img_info.bgr
    work_img, scale = _working_copy(full_img, config.working_max_dim)
    vision.debug_save(config, f"{debug_prefix}_input.png", work_img)

    result = vision.classify_page(work_img, img_info.raw_bytes, config, debug_prefix=debug_prefix)

    if result.page_type != "phone_photo":
        return PageReport(idx + 1, result.page_type, result.confidence, result.signals,
                           "passthrough", "none", None, result.warnings), None

    if result.quad is not None:
        quad, method, warnings = result.quad, result.method, list(result.boundary_warnings)
    else:
        boundary = vision.detect_boundary(work_img, config, debug_prefix=debug_prefix)
        quad, method, warnings = boundary.quad, boundary.method, list(boundary.warnings)

    if quad is None:
        return PageReport(idx + 1, result.page_type, result.confidence, result.signals,
                           "passthrough", "none", None, warnings), None

    if vision.is_noop_quad(quad, work_img.shape, config.noop_guard_frac):
        return PageReport(idx + 1, result.page_type, result.confidence, result.signals,
                           "passthrough", method, None, warnings + ["noop_quad"]), None

    full_quad = vision.scale_quad(quad, 1.0 / scale)
    warped = vision.rectify(full_img, full_quad, config, debug_prefix=debug_prefix)

    corners_px = [[float(x), float(y)] for x, y in full_quad.tolist()]
    page_report = PageReport(idx + 1, result.page_type, result.confidence, result.signals,
                              "rectified", method, corners_px, warnings)
    return page_report, warped


def process_pdf(input_path: str, output_path: str, config: Config) -> PipelineReport:
    doc = fitz.open(input_path)
    try:
        num_pages = doc.page_count
        report = PipelineReport(input_path=input_path)

        if config.single_page_only and num_pages != 1:
            for i in range(num_pages):
                report.pages.append(PageReport(
                    page=i + 1, page_type="ambiguous", confidence=0.0, signals={},
                    action="passthrough", method="none", corners_px=None,
                    warnings=["multi_page_skipped"],
                ))
            pdf_io.rebuild_pdf(input_path, output_path, {}, config.jpeg_quality)
            return report

        stem = os.path.splitext(os.path.basename(input_path))[0]
        replacements: Dict[int, np.ndarray] = {}
        for i in range(num_pages):
            page_report, warped = _process_page(doc[i], i, config, debug_prefix=f"{stem}_p{i + 1}")
            report.pages.append(page_report)
            if warped is not None:
                replacements[i] = warped

        pdf_io.rebuild_pdf(input_path, output_path, replacements, config.jpeg_quality)
        return report
    finally:
        doc.close()


def _find_pdfs(path: str) -> List[str]:
    if os.path.isdir(path):
        return sorted(
            os.path.join(path, f) for f in os.listdir(path) if f.lower().endswith(".pdf")
        )
    return [path]


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Phone-photo document rectification pipeline")
    parser.add_argument("input", help="PDF file or folder of PDFs")
    parser.add_argument("--output-dir", default=None,
                         help="Output folder (default: alongside input)")
    parser.add_argument("--debug-dir", default=None,
                         help="Dump per-stage intermediate images here")
    parser.add_argument("--single-page-only", action="store_true")
    args = parser.parse_args(argv)

    config = Config(single_page_only=args.single_page_only, debug_dir=args.debug_dir)

    inputs = _find_pdfs(args.input)
    if not inputs:
        print(f"No PDFs found at {args.input}", file=sys.stderr)
        return 1

    out_dir = args.output_dir or (args.input if os.path.isdir(args.input) else (os.path.dirname(args.input) or "."))
    os.makedirs(out_dir, exist_ok=True)

    for in_path in inputs:
        base = os.path.splitext(os.path.basename(in_path))[0]
        out_path = os.path.join(out_dir, f"{base}_rectified.pdf")
        report = process_pdf(in_path, out_path, config)
        print(report.to_json())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
