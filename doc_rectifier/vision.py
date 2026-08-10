"""Classical-CV core: Config, phone-photo classifier (S1-S8), boundary
detection cascade (Methods A-E), and perspective rectification.

All functions here operate on a caller-supplied image array; they never touch
PDFs or disk except for optional debug dumps under Config.debug_dir.
"""
from __future__ import annotations

import io
import itertools
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image, ExifTags


# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------

@dataclass
class Config:
    # I/O
    single_page_only: bool = False
    debug_dir: Optional[str] = None

    # Stage 1 classifier (SS4)
    text_layer_min_chars: int = 20
    signal_weights: Dict[str, float] = field(default_factory=lambda: {
        "exif": 1.2,
        "dimensions": 0.6,
        "border": 1.0,
        "illumination": 1.3,
        "sharpness": 0.8,
        "text_geometry": 1.1,
        "quad_feedback": 1.0,
    })
    t_photo: float = 1.2
    t_scan: float = -0.8

    # Stage 2 boundary detection (SS5)
    working_max_dim: int = 1200
    illum_blur_sigma: int = 31
    bilateral_d: int = 9
    bilateral_sigma_color: int = 75
    bilateral_sigma_space: int = 75
    canny_low_mult: float = 0.66
    canny_high_mult: float = 1.33
    hough_threshold: int = 40
    hough_min_line_length: int = 40
    hough_max_line_gap: int = 20
    line_angle_band_deg: float = 35.0
    top_k_lines_per_orientation: int = 6
    line_merge_dist_px: float = 15.0
    grabcut_iters: int = 5
    grabcut_inset_px: int = 20
    border_exclude_frac: float = 0.02

    # Quad validation
    min_area_frac: float = 0.10
    max_area_frac: float = 0.95
    angle_tolerance_deg: float = 35.0
    side_ratio_min: float = 0.5
    side_ratio_max: float = 2.0
    text_containment_floor: float = 0.6
    text_containment_score_weight: float = 0.3
    min_text_blobs: int = 3
    min_text_mask_pixels: int = 200
    noop_guard_frac: float = 0.02
    curled_score_low: float = 0.5
    curled_score_high: float = 0.75

    # Stage 3 rectify (SS6)
    jpeg_quality: int = 95
    aspect_snap_enabled: bool = True
    aspect_snap_tolerance: float = 0.08


# --------------------------------------------------------------------------
# Result types
# --------------------------------------------------------------------------

@dataclass
class ClassifyResult:
    page_type: str  # "phone_photo" | "scan" | "ambiguous"
    confidence: float
    signals: Dict[str, float]
    warnings: List[str] = field(default_factory=list)
    quad: Optional[np.ndarray] = None       # in the coord space of the img passed to classify_page
    method: Optional[str] = None
    boundary_warnings: List[str] = field(default_factory=list)


@dataclass
class BoundaryResult:
    quad: Optional[np.ndarray]
    method: str
    warnings: List[str] = field(default_factory=list)


# --------------------------------------------------------------------------
# Debug helper
# --------------------------------------------------------------------------

def debug_save(config: Config, name: str, img: np.ndarray) -> None:
    if not config.debug_dir or img is None:
        return
    os.makedirs(config.debug_dir, exist_ok=True)
    cv2.imwrite(os.path.join(config.debug_dir, name), img)


def _debug_quad_overlay(img: np.ndarray, quad: Optional[np.ndarray]) -> np.ndarray:
    vis = img.copy()
    if quad is not None:
        pts = np.round(quad).astype(np.int32)
        cv2.polylines(vis, [pts], True, (0, 0, 255), 3, cv2.LINE_AA)
        for p in pts:
            cv2.circle(vis, tuple(p), 6, (0, 255, 0), -1)
    return vis


# --------------------------------------------------------------------------
# Shared geometry helpers
# --------------------------------------------------------------------------

def order_points(pts: np.ndarray) -> np.ndarray:
    """Angle-sort around centroid, then rotate so index 0 is nearest top-left.

    Robust to rotated/skewed quads (sum/diff alone breaks near 45deg rotation).
    """
    pts = np.asarray(pts, dtype=np.float32).reshape(4, 2)
    center = pts.mean(axis=0)
    angles = np.arctan2(pts[:, 1] - center[1], pts[:, 0] - center[0])
    ordered = pts[np.argsort(angles)]
    sums = ordered.sum(axis=1)
    start = int(np.argmin(sums))
    ordered = np.roll(ordered, -start, axis=0)
    return ordered.astype(np.float32)


def scale_quad(quad: np.ndarray, scale: float) -> np.ndarray:
    return (np.asarray(quad, dtype=np.float32) * scale).astype(np.float32)


def is_noop_quad(quad: np.ndarray, shape: Tuple[int, int], tol_frac: float) -> bool:
    h, w = shape[:2]
    ref = np.array([[0, 0], [w, 0], [w, h], [0, h]], dtype=np.float32)
    diag = float(np.hypot(w, h))
    q = order_points(quad)
    max_dev = max(float(np.linalg.norm(q[i] - ref[i])) for i in range(4))
    return max_dev < tol_frac * diag


def _interior_angles(quad: np.ndarray) -> List[float]:
    angles = []
    for i in range(4):
        p_prev = quad[(i - 1) % 4]
        p = quad[i]
        p_next = quad[(i + 1) % 4]
        v1 = p_prev - p
        v2 = p_next - p
        n1, n2 = np.linalg.norm(v1), np.linalg.norm(v2)
        if n1 < 1e-6 or n2 < 1e-6:
            angles.append(90.0)
            continue
        cos_a = np.clip(np.dot(v1, v2) / (n1 * n2), -1.0, 1.0)
        angles.append(float(np.degrees(np.arccos(cos_a))))
    return angles


# --------------------------------------------------------------------------
# Stage 1: Phone-photo classifier (SS4)
# --------------------------------------------------------------------------

def _signal_exif(exif_bytes: Optional[bytes]) -> float:
    if not exif_bytes:
        return 0.0
    try:
        img = Image.open(io.BytesIO(exif_bytes))
        exif = img.getexif()
    except Exception:
        return 0.0
    if not exif:
        return 0.0
    tags = {ExifTags.TAGS.get(k, k): v for k, v in exif.items()}
    make = str(tags.get("Make", "")).lower()
    model = str(tags.get("Model", "")).lower()
    scanner_kw = ("scan", "epson", "canoscan", "scansnap", "brother")
    if any(kw in make or kw in model for kw in scanner_kw):
        return -0.8
    has_camera_evidence = any(k in tags for k in ("Make", "Model", "FocalLength", "GPSInfo"))
    return 1.0 if has_camera_evidence else 0.0


def _signal_dimensions(shape: Tuple[int, int]) -> float:
    h, w = shape[:2]
    if h == 0 or w == 0:
        return 0.0
    ratio = max(h, w) / min(h, w)
    scan_ratios = (1.4142, 1.2941)
    photo_ratios = (4 / 3, 16 / 9, 3 / 2)
    for r in scan_ratios:
        if abs(ratio - r) / r <= 0.02:
            return -0.6
    for r in photo_ratios:
        if abs(ratio - r) / r <= 0.03:
            return 0.6
    return 0.0


def _sample_border_center(img: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    h, w = img.shape[:2]
    bw, bh = max(1, int(w * 0.03)), max(1, int(h * 0.03))
    mask = np.zeros((h, w), dtype=bool)
    mask[:bh, :] = True
    mask[-bh:, :] = True
    mask[:, :bw] = True
    mask[:, -bw:] = True
    cy0, cy1 = int(h * 0.35), int(h * 0.65)
    cx0, cx1 = int(w * 0.35), int(w * 0.65)
    border_px = img[mask]
    center_px = img[cy0:cy1, cx0:cx1].reshape(-1, img.shape[2])
    return border_px, center_px


def _signal_border(img: np.ndarray) -> float:
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    border_hsv, center_hsv = _sample_border_center(hsv)
    border_bgr, center_bgr = _sample_border_center(img)

    border_sat = float(border_hsv[:, 1].mean())
    center_sat = float(center_hsv[:, 1].mean())
    sat_signal = np.clip((border_sat - 25) / 60.0, -1.0, 1.0)

    lum_var = float(border_hsv[:, 2].astype(np.float32).var())
    var_signal = np.clip((lum_var - 150) / 800.0, -1.0, 1.0)

    color_dist = float(np.linalg.norm(border_bgr.mean(axis=0) - center_bgr.mean(axis=0)))
    dist_signal = np.clip((color_dist - 10) / 40.0, -1.0, 1.0)

    return float(np.clip(0.4 * sat_signal + 0.3 * var_signal + 0.3 * dist_signal, -1.0, 1.0))


def _signal_illumination(img: np.ndarray) -> float:
    h, w = img.shape[:2]
    scale = 200.0 / max(h, w)
    small = cv2.resize(img, (max(1, int(w * scale)), max(1, int(h * scale))), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY).astype(np.float32)
    blurred = cv2.GaussianBlur(gray, (0, 0), sigmaX=20)
    rng = float(blurred.max() - blurred.min())
    mean = float(blurred.mean()) + 1e-6
    ratio = rng / mean
    lo, hi = 0.15, 0.45
    if ratio <= lo:
        return -0.8
    if ratio >= hi:
        return 0.8
    frac = (ratio - lo) / (hi - lo)
    return float(-0.8 + 1.6 * frac)


def _signal_sharpness(img: np.ndarray) -> float:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    gh, gw = h // 4, w // 4
    if gh < 2 or gw < 2:
        return 0.0
    lap_vars, weights = [], []
    for i in range(4):
        for j in range(4):
            cell = gray[i * gh:(i + 1) * gh, j * gw:(j + 1) * gw]
            lap = cv2.Laplacian(cell, cv2.CV_64F)
            edge_density = float(np.mean(np.abs(cv2.Sobel(cell, cv2.CV_64F, 1, 0))))
            lap_vars.append(float(lap.var()))
            weights.append(edge_density)
    lap_vars = np.array(lap_vars)
    weights = np.array(weights)
    if weights.sum() < 1e-6:
        return 0.0
    keep = weights > (weights.max() * 0.15)
    if keep.sum() < 3:
        return 0.0
    vals = lap_vars[keep]
    mean = vals.mean() + 1e-6
    cv = vals.std() / mean
    return float(np.clip((cv - 0.3) / 1.2, -0.3, 1.0))


def _text_line_components(gray: np.ndarray, kernel_shape: Tuple[int, int]) -> List[np.ndarray]:
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                    cv2.THRESH_BINARY_INV, 25, 15)
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, np.ones(kernel_shape, np.uint8))
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours


def _signal_text_geometry(gray: np.ndarray) -> Tuple[float, Dict[str, float]]:
    contours = _text_line_components(gray, (25, 1))
    angles, ys = [], []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if w < 20 or h < 4 or w < h * 2:
            continue
        rect = cv2.minAreaRect(c)
        angle = rect[2]
        if angle < -45:
            angle += 90
        angles.append(angle)
        ys.append(y + h / 2.0)

    if len(angles) < 3:
        return 0.0, {"mean_abs_angle": 0.0, "convergence": 0.0}

    angles_arr = np.array(angles)
    ys_arr = np.array(ys)
    mean_abs_angle = float(np.mean(np.abs(angles_arr)))

    ys_norm = (ys_arr - ys_arr.mean())
    if np.ptp(ys_norm) > 1e-3:
        slope = float(np.polyfit(ys_norm, angles_arr, 1)[0])
    else:
        slope = 0.0
    convergence = abs(slope) * (np.ptp(ys_norm) / 100.0)

    tilt_signal = np.clip((mean_abs_angle - 1.0) / 8.0, 0.0, 1.0) * 0.4
    conv_signal = np.clip(convergence / 3.0, 0.0, 1.0) * 0.9
    score = float(np.clip(tilt_signal + conv_signal, 0.0, 1.0))
    return score, {"mean_abs_angle": mean_abs_angle, "convergence": convergence}


def detect_dominant_orientation(gray: np.ndarray) -> str:
    """Edge case #10: coarse check for a 90deg-rotated capture."""
    horiz = _text_line_components(gray, (25, 1))
    vert = _text_line_components(gray, (1, 25))

    def total_len(contours, horizontal: bool) -> float:
        total = 0.0
        for c in contours:
            x, y, w, h = cv2.boundingRect(c)
            long_side, short_side = (w, h) if horizontal else (h, w)
            if long_side > short_side * 2:
                total += long_side
        return total

    h_len = total_len(horiz, True)
    v_len = total_len(vert, False)
    if h_len < 50 and v_len < 50:
        return "unknown"
    if v_len > h_len * 1.5:
        return "vertical"
    return "horizontal"


def _signal_quad_feedback(quad: Optional[np.ndarray], shape: Tuple[int, int]) -> float:
    if quad is None:
        return 0.0
    q = order_points(quad)
    if is_noop_quad(q, shape, tol_frac=0.02):
        return -0.8
    top = np.linalg.norm(q[1] - q[0])
    bottom = np.linalg.norm(q[2] - q[3])
    left = np.linalg.norm(q[3] - q[0])
    right = np.linalg.norm(q[2] - q[1])
    side_dev = max(abs(top - bottom) / max(top, bottom, 1.0), abs(left - right) / max(left, right, 1.0))
    angle_dev = max(abs(a - 90) for a in _interior_angles(q))
    if side_dev > 0.03 or angle_dev > 3.0:
        return float(np.clip(0.5 + side_dev + angle_dev / 30.0, 0.0, 1.0))
    return -0.5


def classify_page(img: np.ndarray, exif_bytes: Optional[bytes], config: Config,
                   debug_prefix: str = "page") -> ClassifyResult:
    """Assumes S1 (real text layer -> born_digital) was already resolved by the caller.

    img must be the same working-resolution copy the caller will later pass to
    detect_boundary, so a quad computed here via the S8 tiebreak (and returned
    on ClassifyResult.quad) is directly usable by the caller without rescaling.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    signals: Dict[str, float] = {}
    signals["exif"] = _signal_exif(exif_bytes)
    signals["dimensions"] = _signal_dimensions(img.shape)
    signals["border"] = _signal_border(img)
    signals["illumination"] = _signal_illumination(img)
    signals["sharpness"] = _signal_sharpness(img)
    signals["text_geometry"], _ = _signal_text_geometry(gray)

    weights = config.signal_weights
    score = sum(signals[k] * weights.get(k, 0.0) for k in signals)

    if score > config.t_photo:
        return ClassifyResult("phone_photo", score, signals)
    if score < config.t_scan:
        return ClassifyResult("scan", score, signals)

    # S8 tiebreaker: run the boundary detector and use quad geometry as evidence.
    boundary = detect_boundary(img, config, debug_prefix=debug_prefix + "_s8")
    signals["quad_feedback"] = _signal_quad_feedback(boundary.quad, img.shape)
    score2 = score + signals["quad_feedback"] * weights.get("quad_feedback", 0.0)

    if score2 > config.t_photo:
        return ClassifyResult("phone_photo", score2, signals, quad=boundary.quad,
                               method=boundary.method, boundary_warnings=boundary.warnings)
    if score2 < config.t_scan:
        return ClassifyResult("scan", score2, signals)
    return ClassifyResult("ambiguous", score2, signals)


# --------------------------------------------------------------------------
# Stage 2: Boundary detection cascade (SS5)
# --------------------------------------------------------------------------

def _normalize_illumination(gray: np.ndarray, sigma: int) -> np.ndarray:
    gray_f = gray.astype(np.float32) + 1.0
    bg = cv2.GaussianBlur(gray_f, (0, 0), sigmaX=sigma)
    norm = gray_f / bg
    norm = cv2.normalize(norm, None, 0, 255, cv2.NORM_MINMAX)
    return norm.astype(np.uint8)


def _auto_canny(img: np.ndarray, low_mult: float, high_mult: float) -> np.ndarray:
    med = float(np.median(img))
    lower = int(max(0, low_mult * med))
    upper = int(min(255, high_mult * med))
    if upper <= lower:
        upper = lower + 1
    return cv2.Canny(img, lower, upper)


def _text_mask(gray: np.ndarray) -> np.ndarray:
    """Adaptive-threshold blobs, kept only where they're shaped like a text
    line (wide-and-short after a horizontal close) -- same trick as the S7
    text-geometry signal. Plain adaptiveThreshold on a textured background
    (wood grain, fabric) produces plenty of small high-contrast blobs that
    aren't text; the quad-validation text-containment check then unfairly
    rejects a geometrically-correct quad because it can't contain background
    noise that's outside it by definition. Shape-filtering suppresses most of
    that noise while keeping real text lines.

    On a high-contrast page-vs-background photo (e.g. white paper on a dark
    surface), adaptiveThreshold also fires on the page's own silhouette edge,
    not just ink -- and that boundary curve, after the same horizontal close,
    is just as "wide and short" as a real text line. A density check (real
    text is a dense cluster of strokes; a 1-2px curve tracing a bounding box
    is mostly empty space) rejects the outline while keeping real text. The
    frame border is excluded too, matching detect_boundary's edge map, since
    lens/encoding artifacts there can otherwise masquerade as a text line.
    """
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                    cv2.THRESH_BINARY_INV, 25, 15)
    h_img, w_img = gray.shape
    m = max(2, int(0.02 * max(h_img, w_img)))
    thresh[:m, :] = 0
    thresh[-m:, :] = 0
    thresh[:, :m] = 0
    thresh[:, -m:] = 0
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, np.ones((1, 25), np.uint8))
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    mask = np.zeros_like(gray)
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if not (w >= h * 2.5 and w >= 15 and h <= 40):
            continue
        blob = np.zeros_like(gray)
        cv2.drawContours(blob, [c], -1, 255, -1)
        density = cv2.countNonZero(cv2.bitwise_and(closed[y:y + h, x:x + w], blob[y:y + h, x:x + w])) / (w * h)
        if density >= 0.35:
            cv2.drawContours(mask, [c], -1, 255, -1)
    return mask


def _validate_quad(quad: np.ndarray, shape: Tuple[int, int], text_mask: Optional[np.ndarray],
                    config: Config) -> Tuple[bool, str]:
    h, w = shape[:2]
    frame_area = float(h * w)
    area = abs(cv2.contourArea(quad.astype(np.float32)))
    if area < config.min_area_frac * frame_area or area > config.max_area_frac * frame_area:
        return False, "area"

    margin = 0.5 * max(w, h)
    if (np.any(quad[:, 0] < -margin) or np.any(quad[:, 0] > w + margin) or
            np.any(quad[:, 1] < -margin) or np.any(quad[:, 1] > h + margin)):
        return False, "out_of_bounds"

    if not cv2.isContourConvex(np.round(quad).astype(np.int32)):
        return False, "convex"

    angles = _interior_angles(quad)
    if any(abs(a - 90) > config.angle_tolerance_deg for a in angles):
        return False, "angle"

    top = np.linalg.norm(quad[1] - quad[0])
    bottom = np.linalg.norm(quad[2] - quad[3])
    left = np.linalg.norm(quad[3] - quad[0])
    right = np.linalg.norm(quad[2] - quad[1])
    for a, b in ((top, bottom), (left, right)):
        if min(a, b) < 1e-3:
            return False, "degenerate"
        ratio = a / b
        if not (config.side_ratio_min <= ratio <= config.side_ratio_max):
            return False, "side_ratio"

    # detect_boundary already nulls text_mask out when it has too few blobs to
    # trust (see min_text_blobs) -- so by the time text_mask reaches here, it's
    # already been screened as a reasonably reliable "where the real text is"
    # signal, and a real hard floor is safe. This matters: a candidate quad
    # can score well on pure edge-perimeter strength (a strong internal fold
    # or a printed divider line) while still cropping off a large fraction of
    # real content -- e.g. missing a receipt's low-contrast top edge caused
    # Method B to settle for an internal line, silently truncating the header.
    # 0.6 was picked with real photos in hand: every correctly-detected quad
    # measured >=0.88 containment; the truncating one measured 0.38.
    if text_mask is not None and np.count_nonzero(text_mask) > config.min_text_mask_pixels:
        if _text_containment_ratio(quad, shape, text_mask) < config.text_containment_floor:
            return False, "text_containment"

    return True, "ok"


def _text_containment_ratio(quad: np.ndarray, shape: Tuple[int, int], text_mask: np.ndarray) -> float:
    h, w = shape[:2]
    text_total = np.count_nonzero(text_mask)
    if text_total == 0:
        return 1.0
    poly_mask = np.zeros((h, w), dtype=np.uint8)
    clipped = np.clip(quad, [0, 0], [w - 1, h - 1]).astype(np.int32)
    cv2.fillConvexPoly(poly_mask, clipped, 255)
    text_in = np.count_nonzero(cv2.bitwise_and(text_mask, poly_mask))
    return text_in / text_total


def _method_a_contour(edges: np.ndarray, shape: Tuple[int, int], text_mask: np.ndarray,
                       config: Config) -> Tuple[Optional[np.ndarray], str]:
    """edges is the shared auto-Canny map (SS5 preprocessing), not a fresh Canny
    pass -- a fixed-threshold re-Canny here (previously (50, 150)) hits exactly
    the fixed-parameter trap SS5 warns about: it silently produced a broken,
    fragmented boundary loop on real wood-grain-background photos where the
    shared adaptive edge map was clean. RETR_EXTERNAL already ignores interior
    text/table edges, so there's no need for the separate text-blanking image.
    """
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None, "none"
    frame_area = shape[0] * shape[1]
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]
    for c in contours:
        if cv2.contourArea(c) < config.min_area_frac * frame_area:
            continue
        hull = cv2.convexHull(c)
        peri = cv2.arcLength(hull, True)
        # A real page edge is rarely a mathematically clean quad (physical curl,
        # JPEG softening at corners) -- a single fixed epsilon often yields 5-6+
        # points where 4 would still be a good fit, so widen it step-wise until
        # exactly 4 points is reached (the standard CamScanner-style approach).
        for eps_frac in (0.02, 0.03, 0.05, 0.08):
            approx = cv2.approxPolyDP(hull, eps_frac * peri, True)
            if len(approx) == 4:
                quad = order_points(approx.reshape(4, 2).astype(np.float32))
                ok, _ = _validate_quad(quad, shape, text_mask, config)
                if ok:
                    return quad, "contour_quad"
    return None, "none"


def _line_intersect(l1: Tuple[Tuple[float, float], Tuple[float, float]],
                     l2: Tuple[Tuple[float, float], Tuple[float, float]]) -> Optional[Tuple[float, float]]:
    (x1, y1), (x2, y2) = l1
    (x3, y3), (x4, y4) = l2
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-6:
        return None
    px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / denom
    py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / denom
    return px, py


def _classify_segments(lines: np.ndarray, band_deg: float):
    horiz, vert = [], []
    for x1, y1, x2, y2 in np.asarray(lines, dtype=np.float64).reshape(-1, 4):
        length = float(np.hypot(x2 - x1, y2 - y1))
        if length < 1e-3:
            continue
        angle = np.degrees(np.arctan2(y2 - y1, x2 - x1)) % 180
        if angle <= band_deg or angle >= 180 - band_deg:
            horiz.append(((x1, y1), (x2, y2), length))
        elif abs(angle - 90) <= band_deg:
            vert.append(((x1, y1), (x2, y2), length))
    return horiz, vert


def _line_normal_form(p1, p2):
    """Return (theta, rho) for clustering near-duplicate lines."""
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    theta = np.arctan2(dy, dx)
    nx, ny = -np.sin(theta), np.cos(theta)
    rho = nx * p1[0] + ny * p1[1]
    return theta, rho


def _top_k_lines(segs, k: int, merge_dist: float):
    segs_sorted = sorted(segs, key=lambda s: -s[2])
    chosen = []
    for p1, p2, length in segs_sorted:
        theta, rho = _line_normal_form(p1, p2)
        is_dup = False
        for cp1, cp2, _ in chosen:
            ctheta, crho = _line_normal_form(cp1, cp2)
            if abs(np.degrees(theta - ctheta)) % 180 < 8 and abs(rho - crho) < merge_dist:
                is_dup = True
                break
        if not is_dup:
            chosen.append((p1, p2, length))
        if len(chosen) >= k:
            break
    return [(p1, p2) for p1, p2, _ in chosen]


def _intersect_quad(top, bottom, left, right) -> Optional[np.ndarray]:
    tl = _line_intersect(top, left)
    tr = _line_intersect(top, right)
    br = _line_intersect(bottom, right)
    bl = _line_intersect(bottom, left)
    if None in (tl, tr, br, bl):
        return None
    return np.array([tl, tr, br, bl], dtype=np.float32)


def _perimeter_edge_strength(quad: np.ndarray, edges: np.ndarray) -> float:
    h, w = edges.shape
    total, count = 0.0, 0
    pts = quad.tolist()
    for i in range(4):
        p1, p2 = pts[i], pts[(i + 1) % 4]
        for t in np.linspace(0, 1, 40):
            x = p1[0] + (p2[0] - p1[0]) * t
            y = p1[1] + (p2[1] - p1[1]) * t
            xi, yi = int(round(x)), int(round(y))
            if 0 <= xi < w and 0 <= yi < h:
                count += 1
                if edges[yi, xi] > 0:
                    total += 1
    return total / count if count else 0.0


def _method_b_lines(edges: np.ndarray, shape: Tuple[int, int], text_mask: np.ndarray,
                     config: Config) -> Tuple[Optional[np.ndarray], str, List[str], float]:
    h, w = shape[:2]
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=config.hough_threshold,
                             minLineLength=config.hough_min_line_length,
                             maxLineGap=config.hough_max_line_gap)
    if lines is None:
        return None, "none", [], 0.0

    horiz, vert = _classify_segments(lines, config.line_angle_band_deg)
    h_cands = _top_k_lines(horiz, config.top_k_lines_per_orientation, config.line_merge_dist_px)
    v_cands = _top_k_lines(vert, config.top_k_lines_per_orientation, config.line_merge_dist_px)

    side_warns = []
    if not h_cands:
        h_cands = [((0.0, 0.0), (float(w), 0.0)), ((0.0, float(h)), (float(w), float(h)))]
        side_warns.append("partial_capture_top_or_bottom")
    elif len(h_cands) == 1:
        h_cands.append(((0.0, float(h)), (float(w), float(h))))
        side_warns.append("partial_capture_bottom")
    if not v_cands:
        v_cands = [((0.0, 0.0), (0.0, float(h))), ((float(w), 0.0), (float(w), float(h)))]
        side_warns.append("partial_capture_left_or_right")
    elif len(v_cands) == 1:
        v_cands.append(((float(w), 0.0), (float(w), float(h))))
        side_warns.append("partial_capture_right")

    best_quad, best_score = None, -1.0
    for h1, h2 in itertools.combinations(h_cands, 2):
        top, bottom = (h1, h2) if (h1[0][1] + h1[1][1]) < (h2[0][1] + h2[1][1]) else (h2, h1)
        for v1, v2 in itertools.combinations(v_cands, 2):
            left, right = (v1, v2) if (v1[0][0] + v1[1][0]) < (v2[0][0] + v2[1][0]) else (v2, v1)
            quad = _intersect_quad(top, bottom, left, right)
            if quad is None:
                continue
            quad = order_points(quad)
            ok, _ = _validate_quad(quad, shape, text_mask, config)
            if not ok:
                continue
            perimeter_score = _perimeter_edge_strength(quad, edges)
            w_text = config.text_containment_score_weight
            score = perimeter_score
            if text_mask is not None and np.count_nonzero(text_mask) > config.min_text_mask_pixels:
                score = (1 - w_text) * perimeter_score + w_text * _text_containment_ratio(quad, shape, text_mask)
            if score > best_score:
                best_score, best_quad = score, quad

    if best_quad is None:
        return None, "none", [], 0.0
    return best_quad, "line_quad_scoring", side_warns, best_score


def _method_c_grabcut(img: np.ndarray, shape: Tuple[int, int], text_mask: np.ndarray,
                       config: Config) -> Tuple[Optional[np.ndarray], str]:
    h, w = shape[:2]
    inset = min(config.grabcut_inset_px, h // 4, w // 4)
    if inset < 2:
        return None, "none"
    mask = np.zeros((h, w), np.uint8)
    rect = (inset, inset, w - 2 * inset, h - 2 * inset)
    bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    try:
        cv2.grabCut(img, mask, rect, bgd, fgd, config.grabcut_iters, cv2.GC_INIT_WITH_RECT)
    except cv2.error:
        return None, "none"
    fg = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    contours, _ = cv2.findContours(fg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None, "none"
    c = max(contours, key=cv2.contourArea)
    hull = cv2.convexHull(c)
    peri = cv2.arcLength(hull, True)
    approx = cv2.approxPolyDP(hull, 0.02 * peri, True)
    if len(approx) == 4:
        quad = approx.reshape(4, 2).astype(np.float32)
    else:
        quad = cv2.boxPoints(cv2.minAreaRect(hull))
    quad = order_points(quad)
    ok, _ = _validate_quad(quad, shape, text_mask, config)
    if not ok:
        return None, "none"
    return quad, "grabcut"


def _method_d_text_deskew(text_mask: Optional[np.ndarray], shape: Tuple[int, int]) -> Tuple[Optional[np.ndarray], str]:
    if text_mask is None:
        return None, "none"
    ys, xs = np.where(text_mask > 0)
    if len(xs) < 200:
        return None, "none"
    pts = np.column_stack([xs, ys]).astype(np.float32)
    angle = cv2.minAreaRect(pts)[2]
    if angle < -45:
        angle += 90
    if abs(angle) < 0.5:
        return None, "none"
    h, w = shape[:2]
    M = cv2.getRotationMatrix2D((w / 2.0, h / 2.0), angle, 1.0)
    corners = np.array([[[0, 0], [w, 0], [w, h], [0, h]]], dtype=np.float32)
    rotated = cv2.transform(corners, M)[0]
    return order_points(rotated), "text_deskew"


def detect_boundary(img: np.ndarray, config: Config, debug_prefix: str = "page") -> BoundaryResult:
    """img should already be the working-resolution copy; corners are returned
    in img's own coordinate space (caller rescales to full-res)."""
    warnings: List[str] = []
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    sat = hsv[:, :, 1]

    norm = _normalize_illumination(gray, config.illum_blur_sigma)
    bilateral = cv2.bilateralFilter(norm, config.bilateral_d, config.bilateral_sigma_color,
                                     config.bilateral_sigma_space)
    sat_bilateral = cv2.bilateralFilter(sat, config.bilateral_d, config.bilateral_sigma_color,
                                         config.bilateral_sigma_space)

    edges_gray = _auto_canny(bilateral, config.canny_low_mult, config.canny_high_mult)
    edges_sat = _auto_canny(sat_bilateral, config.canny_low_mult, config.canny_high_mult)
    edges = cv2.bitwise_or(edges_gray, edges_sat)
    edges = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1)

    # Real phone photos often carry a spurious strong edge right at the frame
    # border (lens vignette falloff, sensor/encoding artifacts) -- on real
    # samples this out-scored the true (shorter, weaker) document edge and
    # got picked as a page boundary line, badly oversizing the quad on that
    # side. Blanking a thin margin removes lines that exist only in that
    # strip without touching a real edge, which extends well inward.
    m = max(2, int(config.border_exclude_frac * max(img.shape[0], img.shape[1])))
    edges[:m, :] = 0
    edges[-m:, :] = 0
    edges[:, :m] = 0
    edges[:, -m:] = 0

    text_mask = _text_mask(gray)
    # A handful of stray fragments (a misread page-edge sliver, a JPEG
    # artifact) is not a trustworthy "this is where the text is" signal --
    # treat it as absent rather than let one blob veto/skew every candidate.
    text_blobs, _ = cv2.findContours(text_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if len(text_blobs) < config.min_text_blobs:
        text_mask = None

    debug_save(config, f"{debug_prefix}_edges.png", edges)

    quad, method = _method_a_contour(edges, img.shape, text_mask, config)
    if quad is None:
        quad, method, side_warns, score = _method_b_lines(edges, img.shape, text_mask, config)
        warnings.extend(side_warns)
        if quad is not None and config.curled_score_low <= score < config.curled_score_high:
            warnings.append("curled_page_suspected")
    if quad is None:
        quad, method = _method_c_grabcut(img, img.shape, text_mask, config)
    if quad is None:
        quad, method = _method_d_text_deskew(text_mask, img.shape)
        if quad is not None:
            warnings.append("deskew_only_no_boundary")

    if quad is None:
        debug_save(config, f"{debug_prefix}_quad.png", img)
        return BoundaryResult(None, "none", warnings + ["boundary_not_found"])

    debug_save(config, f"{debug_prefix}_quad.png", _debug_quad_overlay(img, quad))
    return BoundaryResult(quad, method, warnings)


# --------------------------------------------------------------------------
# Stage 3: Rectification (SS6)
# --------------------------------------------------------------------------

def _maybe_snap_aspect(W: int, H: int, tol: float) -> Tuple[int, int]:
    targets = (1.4142, 1.2941)  # A4, US Letter
    long_dim, short_dim = max(W, H), min(W, H)
    if short_dim < 1:
        return W, H
    ratio = long_dim / short_dim
    for t in targets:
        if abs(ratio - t) / t <= tol:
            short_dim = int(round(long_dim / t))
            break
    return (long_dim, short_dim) if W >= H else (short_dim, long_dim)


def rectify(full_img: np.ndarray, quad: np.ndarray, config: Config,
            debug_prefix: str = "page") -> np.ndarray:
    quad = order_points(quad)
    tl, tr, br, bl = quad

    width = int(round(max(np.linalg.norm(br - bl), np.linalg.norm(tr - tl))))
    height = int(round(max(np.linalg.norm(tr - br), np.linalg.norm(tl - bl))))
    width, height = max(width, 1), max(height, 1)

    if config.aspect_snap_enabled:
        width, height = _maybe_snap_aspect(width, height, config.aspect_snap_tolerance)

    dst = np.array([[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]], dtype=np.float32)
    M = cv2.getPerspectiveTransform(quad, dst)
    warped = cv2.warpPerspective(full_img, M, (width, height),
                                  flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE)
    debug_save(config, f"{debug_prefix}_warped.png", warped)
    return warped
