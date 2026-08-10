"""Synthetic ground-truth data generator + eval CLI (SS8).

No real failure samples exist, so this builds a mixed dataset (procedural
phone-photo composites with degradations/occlusions, clean scans, and a real
born-digital PDF) with recorded ground truth, and evaluates the pipeline
against it -- covering the SS8 metrics without a separate pytest suite.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Optional

import cv2
import fitz
import numpy as np

from . import pdf_io
from . import pipeline
from . import vision
from .vision import Config


# --------------------------------------------------------------------------
# Ground-truth page + PDF helpers
# --------------------------------------------------------------------------

_LOREM_WORDS = [
    "lorem", "ipsum", "dolor", "sit", "amet", "consectetur", "adipiscing", "elit",
    "sed", "do", "eiusmod", "tempor", "incididunt", "ut", "labore", "et", "dolore",
    "magna", "aliqua", "enim", "minim", "veniam", "quis", "nostrud", "exercitation",
    "ullamco", "laboris", "nisi", "aliquip", "ex", "ea", "commodo", "consequat",
    "duis", "aute", "irure", "voluptate", "velit", "esse", "cillum", "fugiat",
    "nulla", "pariatur",
]


def make_clean_page(w: int = 1240, h: int = 1754, rng: Optional[np.random.Generator] = None) -> np.ndarray:
    """Procedural white page of real rendered words (cv2.putText), roughly
    uniform density top-to-bottom.

    Earlier versions drew solid word-shaped rectangles instead of glyphs; at
    the ~200px downscale S5 (illumination uniformity) uses, those blocks were
    coarse enough to survive the sigma~20 blur as a fake lighting gradient on
    a page that's actually flatly lit -- real print is far finer-grained and
    washes out to near-uniform gray at that scale. Rendering actual text (and
    keeping line spacing uniform, no oversized paragraph-gap blocks) keeps S5
    honest for scan ground truth.
    """
    rng = rng if rng is not None else np.random.default_rng()
    img = np.full((h, w, 3), 255, np.uint8)
    margin = int(w * 0.1)
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = h / 1754 * 0.55
    thickness = max(1, int(round(h / 1754 * 1.2)))
    (_, text_h), _ = cv2.getTextSize("Ag", font, font_scale, thickness)
    line_gap = int(text_h * 2.2)
    y = int(h * 0.08) + text_h

    while y < h - margin:
        x = margin
        max_x = w - margin
        is_para_end = rng.random() < 0.12
        line_right = max_x if not is_para_end else margin + int((max_x - margin) * rng.uniform(0.5, 0.85))
        while x < line_right:
            word = _LOREM_WORDS[rng.integers(len(_LOREM_WORDS))]
            (word_w, _), _ = cv2.getTextSize(word, font, font_scale, thickness)
            if x + word_w > line_right:
                break
            cv2.putText(img, word, (x, y), font, font_scale, (40, 40, 40), thickness, cv2.LINE_AA)
            x += word_w + int(text_h * 0.6)
        y += line_gap
    return img


def save_image_as_pdf(img_bgr: np.ndarray, out_path: str, quality: int = 95) -> None:
    ok, buf = cv2.imencode(".jpg", img_bgr, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        raise RuntimeError("JPEG encode failed")
    h, w = img_bgr.shape[:2]
    doc = fitz.open()
    page = doc.new_page(width=w, height=h)
    page.insert_image(fitz.Rect(0, 0, w, h), stream=buf.tobytes())
    doc.save(out_path)
    doc.close()


def make_born_digital_pdf(out_path: str, rng: np.random.Generator) -> None:
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    lines = [f"Line {i}: this is a born-digital test document with real text." for i in range(30)]
    page.insert_text((72, 72), "\n".join(lines), fontsize=11)
    doc.save(out_path)
    doc.close()


# --------------------------------------------------------------------------
# Procedural backgrounds
# --------------------------------------------------------------------------

def make_background(kind: str, w: int, h: int, rng: np.random.Generator) -> np.ndarray:
    if kind == "wood":
        img = np.zeros((h, w, 3), np.uint8)
        img[:, :] = (30, 70, 120)
        streaks = np.zeros((h, w), np.float32)
        for _ in range(30):
            x0 = int(rng.integers(0, w))
            x1 = x0 + int(rng.integers(-40, 40))
            cv2.line(streaks, (x0, 0), (x1, h), 1.0, thickness=int(rng.integers(1, 4)))
        streaks = cv2.GaussianBlur(streaks, (0, 0), 3)
        noise = rng.normal(0, 12, (h, w)).astype(np.float32)
        variation = (noise + streaks * 20)[..., None]
        return np.clip(img.astype(np.float32) + variation, 0, 255).astype(np.uint8)
    if kind == "fabric":
        color = (int(rng.integers(50, 110)), int(rng.integers(40, 90)), int(rng.integers(40, 90)))
        img = np.full((h, w, 3), color, np.uint8)
        noise = rng.normal(0, 15, (h, w, 3))
        img = np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)
        return cv2.GaussianBlur(img, (3, 3), 0)
    if kind == "plain":
        color = tuple(int(c) for c in rng.integers(40, 200, 3))
        return np.full((h, w, 3), color, np.uint8)
    if kind == "near_white":
        img = np.full((h, w, 3), 245, np.uint8)
        noise = rng.normal(0, 3, (h, w, 3))
        return np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)
    raise ValueError(kind)


# --------------------------------------------------------------------------
# Homography jitter + degradations + occlusion
# --------------------------------------------------------------------------

def composite_with_jitter(page_img: np.ndarray, bg_kind: str, jitter_frac: float,
                           rng: np.random.Generator, margin_frac: float = 0.15):
    ph, pw = page_img.shape[:2]
    bw, bh = int(pw * (1 + 2 * margin_frac)), int(ph * (1 + 2 * margin_frac))
    bg = make_background(bg_kind, bw, bh, rng)

    ox, oy = int(pw * margin_frac), int(ph * margin_frac)
    base_corners = np.array([[ox, oy], [ox + pw, oy], [ox + pw, oy + ph], [ox, oy + ph]], dtype=np.float32)
    jitter = (rng.random((4, 2)) - 0.5) * 2 * jitter_frac * min(pw, ph)
    dst_corners = (base_corners + jitter).astype(np.float32)

    src_corners = np.array([[0, 0], [pw, 0], [pw, ph], [0, ph]], dtype=np.float32)
    M = cv2.getPerspectiveTransform(src_corners, dst_corners)
    warped_page = cv2.warpPerspective(page_img, M, (bw, bh), flags=cv2.INTER_LANCZOS4, borderValue=(0, 0, 0))
    mask = np.zeros((bh, bw), np.uint8)
    cv2.fillConvexPoly(mask, np.round(dst_corners).astype(np.int32), 255)
    mask3 = cv2.merge([mask, mask, mask])
    composite = np.where(mask3 > 0, warped_page, bg)
    return composite, dst_corners


def apply_shadow(img: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    h, w = img.shape[:2]
    mask = np.zeros((h, w), np.uint8)
    band_w = int(w * rng.uniform(0.25, 0.5))
    cx = int(rng.integers(0, w))
    angle = rng.uniform(-25, 25)
    box = cv2.boxPoints(((cx, h / 2), (band_w, h * 1.5), angle)).astype(np.int32)
    cv2.fillConvexPoly(mask, box, 255)
    mask_f = cv2.GaussianBlur(mask, (0, 0), sigmaX=max(1.0, w * 0.06)).astype(np.float32) / 255.0
    strength = rng.uniform(0.25, 0.5)
    factor = 1.0 - mask_f * strength
    return np.clip(img.astype(np.float32) * factor[..., None], 0, 255).astype(np.uint8)


def apply_vignette(img: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    h, w = img.shape[:2]
    Y, X = np.ogrid[:h, :w]
    cx, cy = w / 2, h / 2
    dist = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)
    maxd = np.sqrt(cx ** 2 + cy ** 2) + 1e-6
    strength = rng.uniform(0.15, 0.35)
    factor = 1 - strength * (dist / maxd) ** 2
    return np.clip(img.astype(np.float32) * factor[..., None], 0, 255).astype(np.uint8)


def apply_blur_gradient(img: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    h, w = img.shape[:2]
    blurred = cv2.GaussianBlur(img, (0, 0), rng.uniform(3, 6))
    Y, X = np.ogrid[:h, :w]
    axis = rng.choice(["top", "bottom", "left", "right"])
    if axis == "top":
        t = Y / h
    elif axis == "bottom":
        t = 1 - Y / h
    elif axis == "left":
        t = X / w
    else:
        t = 1 - X / w
    t = t.astype(np.float32)[..., None]
    out = img.astype(np.float32) * (1 - t) + blurred.astype(np.float32) * t
    return np.clip(out, 0, 255).astype(np.uint8)


def apply_noise(img: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    noise = rng.normal(0, rng.uniform(3, 10), img.shape)
    return np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)


def apply_jpeg_recompress(img: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    q = int(rng.integers(60, 85))
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, q])
    return cv2.imdecode(buf, cv2.IMREAD_COLOR)


def apply_frame_rotation(img: np.ndarray, corners: np.ndarray, rng: np.random.Generator):
    h, w = img.shape[:2]
    angle = rng.uniform(-8, 8)
    M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    rotated = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LANCZOS4, borderValue=(0, 0, 0))
    pts = np.hstack([corners, np.ones((4, 1), dtype=np.float32)])
    new_corners = (M @ pts.T).T
    return rotated, new_corners.astype(np.float32)


def apply_occlusion(img: np.ndarray, corners: np.ndarray, mode: str, rng: np.random.Generator):
    h, w = img.shape[:2]
    x0, y0, x1, y1 = 0, 0, w, h
    if mode == "corner":
        which = int(rng.integers(4))
        cut = rng.uniform(0.04, 0.08)
        if which in (0, 3):
            x0 = int(w * cut)
        else:
            x1 = w - int(w * cut)
        if which in (0, 1):
            y0 = int(h * cut)
        else:
            y1 = h - int(h * cut)
    elif mode == "edge":
        side = rng.choice(["top", "bottom", "left", "right"])
        cut = rng.uniform(0.08, 0.14)
        if side == "top":
            y0 = int(h * cut)
        elif side == "bottom":
            y1 = h - int(h * cut)
        elif side == "left":
            x0 = int(w * cut)
        else:
            x1 = w - int(w * cut)
    cropped = img[y0:y1, x0:x1]
    shifted = corners - np.array([x0, y0], dtype=np.float32)
    return cropped, shifted


def make_phone_photo_sample(rng: np.random.Generator, page: np.ndarray):
    bg_kind = str(rng.choice(["wood", "fabric", "plain", "near_white"]))
    jitter = rng.uniform(0.02, 0.07)
    composite, corners = composite_with_jitter(page, bg_kind, jitter, rng)

    applied = []
    if rng.random() < 0.6:
        composite = apply_shadow(composite, rng); applied.append("shadow")
    if rng.random() < 0.4:
        composite = apply_vignette(composite, rng); applied.append("vignette")
    if rng.random() < 0.4:
        composite = apply_blur_gradient(composite, rng); applied.append("blur_gradient")
    if rng.random() < 0.5:
        composite = apply_noise(composite, rng); applied.append("noise")
    if rng.random() < 0.3:
        composite, corners = apply_frame_rotation(composite, corners, rng); applied.append("rotate")
    if rng.random() < 0.5:
        composite = apply_jpeg_recompress(composite, rng); applied.append("jpeg")

    occlusion = None
    r = rng.random()
    if r < 0.15:
        composite, corners = apply_occlusion(composite, corners, "corner", rng)
        occlusion = "corner"
    elif r < 0.25:
        composite, corners = apply_occlusion(composite, corners, "edge", rng)
        occlusion = "edge"

    meta = {"background": bg_kind, "jitter": float(jitter), "degradations": applied, "occlusion": occlusion}
    return composite, corners, meta


# --------------------------------------------------------------------------
# Dataset builder
# --------------------------------------------------------------------------

def build_dataset(n: int, out_dir: str, seed: int = 0) -> list:
    os.makedirs(out_dir, exist_ok=True)
    rng = np.random.default_rng(seed)
    manifest = []

    n_photo = max(1, int(n * 0.6))
    n_scan = max(1, int(n * 0.3))
    n_digital = max(1, n - n_photo - n_scan)

    for i in range(n_photo):
        page = make_clean_page(rng=rng)
        composite, corners, meta = make_phone_photo_sample(rng, page)
        name = f"photo_{i:03d}"
        save_image_as_pdf(composite, os.path.join(out_dir, name + ".pdf"))
        cv2.imwrite(os.path.join(out_dir, name + "_gt.png"), page)
        manifest.append({"name": name, "page_type": "phone_photo", "corners": corners.tolist(), **meta})

    for i in range(n_scan):
        page = make_clean_page(w=2480, h=3508, rng=rng)
        name = f"scan_{i:03d}"
        save_image_as_pdf(page, os.path.join(out_dir, name + ".pdf"))
        manifest.append({"name": name, "page_type": "scan", "corners": None})

    for i in range(n_digital):
        name = f"digital_{i:03d}"
        make_born_digital_pdf(os.path.join(out_dir, name + ".pdf"), rng)
        manifest.append({"name": name, "page_type": "born_digital", "corners": None})

    with open(os.path.join(out_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    return manifest


def _load_manifest(dataset_dir: str) -> list:
    with open(os.path.join(dataset_dir, "manifest.json")) as f:
        return json.load(f)


# --------------------------------------------------------------------------
# Eval metrics (SS8)
# --------------------------------------------------------------------------

def eval_classifier(dataset_dir: str) -> None:
    manifest = _load_manifest(dataset_dir)
    config = Config()
    confusion: dict = {}
    scan_fp, scan_total = 0, 0

    for entry in manifest:
        path = os.path.join(dataset_dir, entry["name"] + ".pdf")
        doc = fitz.open(path)
        page = doc[0]
        true_type = entry["page_type"]
        if pdf_io.has_real_text_layer(page, config.text_layer_min_chars):
            pred = "born_digital"
        else:
            img_info = pdf_io.extract_native_image(page)
            if img_info is None:
                pred = "ambiguous"
            else:
                work, _ = pipeline._working_copy(img_info.bgr, config.working_max_dim)
                pred = vision.classify_page(work, img_info.raw_bytes, config).page_type
        doc.close()

        confusion[(true_type, pred)] = confusion.get((true_type, pred), 0) + 1
        if true_type == "scan":
            scan_total += 1
            if pred == "phone_photo":
                scan_fp += 1

    print("Confusion matrix (true -> pred):")
    for (t, p), count in sorted(confusion.items()):
        print(f"  {t:>12} -> {p:<12}: {count}")
    fp_rate = scan_fp / scan_total if scan_total else 0.0
    print(f"Scan false-positive rate: {fp_rate:.3f} ({scan_fp}/{scan_total}) -- target ~0")


def _quad_iou(q1: np.ndarray, q2: np.ndarray, shape) -> float:
    h, w = shape[:2]
    m1 = np.zeros((h, w), np.uint8)
    m2 = np.zeros((h, w), np.uint8)
    cv2.fillConvexPoly(m1, np.clip(np.round(q1), [0, 0], [w - 1, h - 1]).astype(np.int32), 1)
    cv2.fillConvexPoly(m2, np.clip(np.round(q2), [0, 0], [w - 1, h - 1]).astype(np.int32), 1)
    inter = int(np.logical_and(m1, m2).sum())
    union = int(np.logical_or(m1, m2).sum())
    return inter / union if union else 0.0


def eval_boundary(dataset_dir: str) -> None:
    manifest = _load_manifest(dataset_dir)
    config = Config()
    corner_errors, ious = [], []

    for entry in manifest:
        if entry["page_type"] != "phone_photo" or entry["corners"] is None:
            continue
        path = os.path.join(dataset_dir, entry["name"] + ".pdf")
        doc = fitz.open(path)
        img_info = pdf_io.extract_native_image(doc[0])
        doc.close()
        if img_info is None:
            continue

        full_img = img_info.bgr
        work, scale = pipeline._working_copy(full_img, config.working_max_dim)
        boundary = vision.detect_boundary(work, config)
        if boundary.quad is None:
            continue

        pred = vision.order_points(vision.scale_quad(boundary.quad, 1.0 / scale))
        true = vision.order_points(np.array(entry["corners"], dtype=np.float32))
        h, w = full_img.shape[:2]
        in_bounds = [i for i in range(4) if 0 <= true[i][0] <= w and 0 <= true[i][1] <= h]
        if in_bounds:
            corner_errors.append(float(np.mean([np.linalg.norm(pred[i] - true[i]) for i in in_bounds])))
        ious.append(_quad_iou(pred, true, full_img.shape))

    mean_err = float(np.mean(corner_errors)) if corner_errors else float("nan")
    mean_iou = float(np.mean(ious)) if ious else float("nan")
    print(f"Boundary: n={len(corner_errors)} mean corner error(px)={mean_err:.1f}")
    print(f"Boundary: n={len(ious)} mean IoU={mean_iou:.3f}")


def eval_do_no_harm(dataset_dir: str) -> None:
    config = Config()
    manifest = _load_manifest(dataset_dir)
    tmp_dir = os.path.join(dataset_dir, "_dnh_out")
    os.makedirs(tmp_dir, exist_ok=True)
    n, passed = 0, 0

    for entry in manifest:
        if entry["page_type"] not in ("scan", "born_digital"):
            continue
        n += 1
        in_path = os.path.join(dataset_dir, entry["name"] + ".pdf")
        out_path = os.path.join(tmp_dir, entry["name"] + "_out.pdf")
        pipeline.process_pdf(in_path, out_path, config)
        with open(in_path, "rb") as f1, open(out_path, "rb") as f2:
            same = f1.read() == f2.read()
        if same:
            passed += 1
        else:
            print(f"  NOT byte-identical: {entry['name']}")

    print(f"Do-no-harm: {passed}/{n} byte-identical -- target {n}/{n}")


def eval_sharpness(dataset_dir: str) -> None:
    config = Config()
    manifest = _load_manifest(dataset_dir)
    tmp_dir = os.path.join(dataset_dir, "_sharp_out")
    os.makedirs(tmp_dir, exist_ok=True)
    ratios = []

    for entry in manifest:
        if entry["page_type"] != "phone_photo":
            continue
        # Isolate whether rectify() itself softens the image: samples degraded
        # with blur/noise are *supposed* to score lower against the pristine
        # ground truth (that's the simulated photo condition, not a pipeline
        # defect), so they'd make this a useless check either way.
        degradations = entry.get("degradations", [])
        if "blur_gradient" in degradations or "noise" in degradations:
            continue
        gt_path = os.path.join(dataset_dir, entry["name"] + "_gt.png")
        if not os.path.exists(gt_path):
            continue
        gt_gray = cv2.cvtColor(cv2.imread(gt_path), cv2.COLOR_BGR2GRAY)
        gt_var = cv2.Laplacian(gt_gray, cv2.CV_64F).var()

        in_path = os.path.join(dataset_dir, entry["name"] + ".pdf")
        out_path = os.path.join(tmp_dir, entry["name"] + "_out.pdf")
        pipeline.process_pdf(in_path, out_path, config)
        doc = fitz.open(out_path)
        img_info = pdf_io.extract_native_image(doc[0])
        doc.close()
        if img_info is None:
            continue
        warped_gray = cv2.cvtColor(img_info.bgr, cv2.COLOR_BGR2GRAY)
        warped_var = cv2.Laplacian(warped_gray, cv2.CV_64F).var()
        if gt_var > 1e-6:
            ratios.append(warped_var / gt_var)

    mean_ratio = float(np.mean(ratios)) if ratios else float("nan")
    print(f"Sharpness: n={len(ratios)} mean ratio(warped/gt)={mean_ratio:.2f} -- target >= 0.9")


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(description="Synthetic dataset generator + eval harness")
    parser.add_argument("--generate", type=int, metavar="N", help="Generate N synthetic samples")
    parser.add_argument("--out", help="Output directory for --generate")
    parser.add_argument("--eval-classifier", metavar="DIR")
    parser.add_argument("--eval-boundary", metavar="DIR")
    parser.add_argument("--eval-do-no-harm", metavar="DIR")
    parser.add_argument("--eval-sharpness", metavar="DIR")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args(argv)

    if args.generate is not None:
        if not args.out:
            parser.error("--generate requires --out")
        build_dataset(args.generate, args.out, seed=args.seed)
        print(f"Generated {args.generate} samples in {args.out}")
    if args.eval_classifier:
        eval_classifier(args.eval_classifier)
    if args.eval_boundary:
        eval_boundary(args.eval_boundary)
    if args.eval_do_no_harm:
        eval_do_no_harm(args.eval_do_no_harm)
    if args.eval_sharpness:
        eval_sharpness(args.eval_sharpness)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
