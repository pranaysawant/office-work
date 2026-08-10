# PROMPT: Phone-Photo Document Detection & Rectification Pipeline

You are a senior computer-vision engineer. Build a production-grade Python module that pre-processes PDFs before they enter a document-translation pipeline. Some users upload PDFs made from **phone photos of documents** instead of proper scans. Perspective distortion, background clutter, and skew break the downstream layout-extraction stage. Your job: detect such pages, find the document boundary, perspective-correct ("flatten") them like CamScanner does, and rebuild the PDF — while leaving genuine scans and born-digital pages completely untouched.

Work through this spec carefully. Where I specify an algorithm, follow it. Where I mark something OPTIONAL, implement only if it doesn't complicate the core path.

---

## 1. Hard Constraints

1. **Classical CV only.** Allowed: OpenCV (`cv2`), NumPy, Pillow, PyMuPDF (`fitz`), scikit-image (optional), `img2pdf` (optional). **Forbidden:** any deep-learning model, any LLM/VLM, pytesseract or any OCR engine, any network call.
2. **Preserve resolution and sharpness.** Never rasterize an embedded image at lower resolution than its native pixels. All boundary *detection* runs on a downscaled working copy for speed, but the final warp is applied to the **full-resolution original** with detected corners scaled back up. Interpolation: `cv2.INTER_LANCZOS4`. Re-encode JPEG at quality ≥ 95 (or keep lossless if source was lossless). The output page must never look softer than the input.
3. **Do no harm.** ~90–95% of traffic is genuine scans or born-digital PDFs. A false positive (warping a real scan) is worse than a false negative. Every stage must have a validated exit: if classification is uncertain, if no valid quad is found, or if the quad fails sanity checks → return the original page byte-identical, with a diagnostic flag. The pipeline must never output a degraded or garbage page.
4. **CPU-light.** Target ≤ ~1–2 s per page on a normal CPU. Run cheap signals first and short-circuit (see §4). Volume context: ~2,000 documents/day, ~5 pages average.
5. **Keep it pragmatic.** No speculative abstractions, no plugin architectures, no over-modularization. Minimum code that solves the problem well. A senior engineer reviewing the diff should not call it overcomplicated.

---

## 2. Input / Output Contract

**Entry point:**

```python
process_pdf(input_path: str, output_path: str, config: Config) -> PipelineReport
```

**Config (single dataclass, all tunables in one place):**

- `single_page_only: bool` — if `True`, only PDFs with exactly one page are inspected (the common real-world case: user photographs one page and converts it); multi-page PDFs pass through untouched. If `False` (default), every page of every PDF is inspected regardless of page count.
- Classification thresholds and signal weights (§4), boundary-detection parameters (§5), warp settings (§6), `debug_dir: Optional[str]` — when set, dump intermediate images per stage per page (edge maps, detected lines, candidate quads drawn on the image, final warp) for tuning without needing print statements.

**PipelineReport (JSON-serializable), one entry per page:**

```json
{
  "page": 1,
  "page_type": "phone_photo | scan | born_digital | ambiguous",
  "confidence": 0.87,
  "signals": {"exif": 1.0, "border": 0.9, "illumination": 0.8, "...": "..."},
  "action": "rectified | passthrough",
  "method": "contour_quad | line_quad_scoring | grabcut | text_deskew | none",
  "corners_px": [[x, y], "..."],
  "warnings": ["partial_capture_left_edge", "curled_page_suspected"]
}
```

**PDF handling (PyMuPDF):**

- A page with a real extractable text layer (`page.get_text()` returns substantive text, not OCR noise — check for > ~20 chars of real words) → `born_digital`, skip immediately. This is the fastest and most reliable filter.
- Image-only pages: extract the embedded image **at native resolution** via `page.get_images()` + `doc.extract_image(xref)` — do NOT use `page.get_pixmap()` at a fixed DPI, which resamples. Handle the case where a page has one full-bleed image (normal) vs. multiple images (treat as scan/complex, pass through with a warning).
- When rebuilding the output PDF, pages that were not modified must be copied through unchanged (copy original pages/streams; do not decode–re-encode them). Only replace the page image for rectified pages.

---

## 3. Architecture

```
doc_rectifier/
  config.py      # Config dataclass
  pdf_io.py      # page triage, native-res extraction, PDF rebuild
  classifier.py  # phone-photo scoring (§4)
  boundary.py    # quad detection cascade (§5)
  rectify.py     # full-res perspective warp (§6)
  pipeline.py    # orchestration + report
  synth.py       # synthetic test-data generator (§8) — build this FIRST
  cli.py         # process a file/folder, print report, --debug-dir
tests/
```

Keep each module focused; do not split further.

---

## 4. Stage 1 — Phone-Photo Classifier

No single signal is reliable. Compute a weighted ensemble of weak signals, each returning a score in [-1, +1] (negative = scan evidence, positive = photo evidence). Order them cheapest-first and short-circuit when the running decision is already certain.

**S1. Text layer (free, from pdf_io):** real text layer → born_digital, stop.

**S2. EXIF (very cheap):** read EXIF from the extracted JPEG bytes with Pillow. Presence of camera `Make`/`Model`/`FocalLength`/GPS → strong photo evidence (+1). Scanner vendor strings → scan evidence. **Absence proves nothing** (PDF converters strip EXIF) → score 0, continue.

**S3. Pixel dimensions & aspect ratio (very cheap):** scans come in paper aspect ratios at standard DPIs — A4 ≈ 1.414 (e.g., 2480×3508 @300dpi, 1240×1754 @150dpi), Letter ≈ 1.294 — usually with clean round dimensions. Phone photos come in sensor ratios: 4:3 (4032×3024, 4000×3000, 3264×2448…), 16:9, 3:4. Match against both families with tolerance.

**S4. Border/background analysis:** sample four perimeter strips (outer ~3% of each side). Scans have near-uniform white or pure-black borders with very low saturation and low variance. Phone photos on a desk show the desk: elevated saturation (wood, fabric), texture variance, and a strong color difference vs. the central region. Score from (a) mean saturation of border vs. center, (b) luminance variance in the border, (c) border-vs-center color distance.

**S5. Illumination uniformity:** downscale to ~200 px, convert to gray, Gaussian-blur heavily (σ ≈ 15–25) to isolate the low-frequency lighting field. Scanners illuminate flatly → tiny range. Phone photos always show a brightness gradient, vignette, or shadow → large range. Score from (max − min)/mean of the lighting field. This is one of the most discriminative cheap signals.

**S6. Sharpness spatial variance:** divide the working image into a 4×4 grid; compute variance-of-Laplacian per cell on the gray image. Scans are uniformly sharp. Handheld photos show focus falloff (sharp center, soft edges, or sharp bottom / soft top). Score from the coefficient of variation across cells. Guard: on cells with almost no content (blank margins) Laplacian variance is naturally low — weight cells by their edge density so blank paper doesn't fake "blur".

**S7. Text-line geometry:** adaptive-threshold the working gray image, morphologically close horizontally (wide kernel, e.g., 25×1) so words merge into line blobs, take connected components that look like text lines (wide, short), and fit an angle to each (`cv2.minAreaRect` or `cv2.fitLine`). Two measurements: (a) **mean absolute angle** — scans ≈ 0°, photos are tilted; (b) **angle variance / systematic drift top-to-bottom** — perspective makes baselines *converge*, so the angle changes across the page; a merely-rotated scan has constant angle. Convergence is strong photo evidence; constant small tilt alone is weak.

**S8. Perspective-quad feedback:** if scores S2–S7 land in the ambiguous band, run the boundary detector (§5) and use its result as the tiebreaker: a confident quad whose opposite sides differ in length by > ~3% or whose interior angles deviate from 90° by > ~3° is a perspective photo. A quad that is essentially the full frame and rectangular → scan.

**Decision:** weighted sum → `score`. `score > T_photo` → phone_photo; `score < T_scan` → scan (passthrough); between → run S8; still ambiguous → **passthrough** with `page_type: ambiguous` (do-no-harm). Choose default weights/thresholds conservatively, expose all in Config, and log the per-signal breakdown in the report so thresholds can be tuned from production logs.

**Prior art / feasibility note:** this exact classification problem was solved with classical features long ago — Silva, Lins et al., "Scanned or Photographed? Automatically Deciding How a Document was Digitized" (2009) reported >99.9% accuracy on 16,000+ documents using hand-crafted features (including image-entropy measures) with a classical classifier. So a well-tuned feature ensemble is sufficient; no deep learning is needed. OPTIONAL upgrade path if hand-tuned weights plateau: add border-region entropy as signal S9, and/or replace the weighted sum with a small decision tree trained on the synthetic dataset from §8 (scikit-learn, still classical, still CPU-trivial) — but ship the hand-tuned weighted sum first.

---

## 5. Stage 2 — Boundary Detection Cascade

Run on a working copy downscaled to max dimension ~1200 px (remember the scale factor). This is the hard part; the cascade goes from cheap/strict to robust/lenient.

**Preprocessing (shared):**

1. Gray conversion; also keep the HSV **saturation** channel (paper is low-saturation; wooden/colored desks are not — saturation often separates page from background better than luminance).
2. **Illumination normalization:** `norm = gray / GaussianBlur(gray, σ≈31)` (float, rescaled). This is critical: it erases soft shadow boundaries — including the user's own phone/hand shadow falling across the page — and vignetting, while sharp physical paper edges survive. All edge detection below runs on this normalized image (and optionally on the saturation channel; take the union of edge maps).
3. **Bilateral filter** (`cv2.bilateralFilter`, small d, moderate σ) before edge detection: suppresses fine texture — wood grain, fabric weave, sensor noise — while preserving the sharp page boundary. Standard practice in production document scanners; plain Gaussian blur softens the boundary we need.
4. **Text suppression for the contour path:** repeated morphological closing (`cv2.MORPH_CLOSE`, 5×5 kernel, ~3 iterations) on the working image turns the printed page into a near-blank bright blob, so interior text/table edges cannot compete with the outer boundary during contour detection (this is the trick used in the LearnOpenCV reference scanner). Use the closed image for Method A; use the un-closed normalized image for line detection in Method B (text baselines there are handled by segment-length filtering).
5. Auto-Canny: thresholds from the median of the normalized image (`lower = 0.66·median`, `upper = 1.33·median`), then a light dilation to connect broken edges.

**Why adaptive, not fixed, parameters:** the Docutain team demonstrated (References §9) the trap of fixed-parameter Canny on unknown inputs: with a small Gaussian blur, background texture (their example: a wooden floor) floods the edge map with noise; with a blur large enough to remove that noise, the document's own edges get erased too. There is no single blur/threshold setting that works across inputs you haven't seen. Items 3 and 5 exist precisely to escape this trap — bilateral filtering removes texture without eroding the sharp boundary, and Canny thresholds derive from each image's median rather than constants. Do not replace them with fixed values during tuning.

**Method A — Contour quad (fast path, all four edges visible):**
`findContours` on the edge map → keep contours with area > ~20% of frame → convex hull → `approxPolyDP` (ε ≈ 2% of perimeter) → accept if exactly 4 points and validation (below) passes. This is the textbook CamScanner approach; it fails exactly when corners are missing, which is why Method B exists.

**Method B — Candidate lines → quad enumeration & scoring (the workhorse; handles missing corners):**
The key insight: **do not search for corners — search for boundary *lines* and intersect them mathematically.** A corner hidden by a staple, a torn corner, or a corner slightly out of frame doesn't matter, because two lines still intersect at a well-defined point, even outside the image bounds. This is the approach Dropbox used for their production scanner and that Hough-based on-device ID-document localization uses (see References §9), with one production-grade refinement: **don't commit to one line per side early — enumerate candidate quads and score them.**

1. Detect line segments with `cv2.HoughLinesP` (or `cv2.createLineSegmentDetector` — note LSD is unavailable in some OpenCV 3.4.x–4.0 builds for license reasons, so make HoughLinesP the default) on the edge map; merge collinear segments.
2. Discard short segments; classify the rest as near-horizontal or near-vertical with a generous perspective band (±35°). Keep the **top-k strongest candidate lines per orientation** (k ≈ 5–8), strength = total supporting segment length / Hough votes.
3. Compute pairwise intersections between horizontal-family and vertical-family candidate lines as potential corners, filtering with geometric constraints (reject intersections at very acute angles, or absurdly far outside the frame).
4. **Enumerate all plausible quadrilaterals** (choose 2 horizontal + 2 vertical candidate lines, top above bottom, left left-of right) and **score each quad by summing edge-map strength along its full perimeter**, with soft priors from the validation rules below. Pick the highest-scoring quad. This is what makes fingers, staples, and pens harmless: an occluded stretch merely lowers the score locally, while the true boundary still wins overall — no single-line fit gets bent by outliers.
5. Corners **may fall outside the image**; that is allowed and correct — this is exactly what solves the missing-corner case.
6. **Missing side:** if one orientation family has only one credible line (page edge runs off the frame), substitute the corresponding image border as the fourth line, proceed, and add warning `partial_capture_<side>`. The warp then still fixes perspective for the visible content; the lost content is unrecoverable and the flag tells downstream. If **two or more sides** have no support → fall down the cascade.

**Method C — GrabCut segmentation (tough backgrounds, used when A and B fail):**
`cv2.grabCut` initialized with a rectangle inset ~20 px from the frame border as probable-foreground (after the text-suppression closing from preprocessing, so the page is a solid blob). Take the largest connected foreground component, then fit a quad to its convex hull (`approxPolyDP`, or minAreaRect if the hull is ragged) and run the same validation. GrabCut is the heaviest step (hundreds of ms), which is why it sits third in the cascade, but it handles low-contrast and cluttered backgrounds that defeat pure edge-based methods — this is the LearnOpenCV reference scanner's core mechanism. Conceptually it is also the classical stand-in for the U-Net segmentation masks commercial SDKs use (References §9): same mask → contour → quad flow, no neural network.

**Method D — Text-mass fallback (no usable boundary):**
Build a text mask (adaptive threshold + morphological close), take `cv2.minAreaRect` of the text region, and apply **rotation-only deskew** (affine, no perspective). This at least fixes tilt when the page boundary is undetectable — e.g., **white paper on a white desk** with no visible seam (GrabCut also fails there since foreground and background are statistically identical). OPTIONAL enhancement: estimate perspective from converging text baselines (fit a line per text row; their vanishing point gives the horizontal perspective) — describe in comments, implement only if straightforward.

**Method E — Give up gracefully:** return the page untouched, `action: passthrough`, `method: none`, warning `boundary_not_found`.

**Quad validation (applied to A and B output — every check must pass):**

- Area between ~25% and ~98% of frame.
- Convex; interior angles within 90° ± 35°.
- Opposite side length ratios within [0.5, 2.0].
- The quad must contain ≥ ~90% of the text mask (this kills false quads from **patterned backgrounds** — ruled tablecloths, floor tiles, a second document under the target — because the winning quad must actually enclose the text).
- Line-fit residuals low; if a boundary line fits poorly because the physical edge is curved, the page is likely **curled or folded** — planar homography cannot flatten a curved page. Still warp (it usually helps), but add warning `curled_page_suspected`.
- **No-op guard:** if the final quad deviates from the full axis-aligned frame by < ~2% at every corner, skip warping entirely (`action: passthrough`) — warping a nearly-perfect image only costs sharpness.

---

## 6. Stage 3 — Rectification

1. Scale the four corners back to full-resolution coordinates.
2. Order TL, TR, BR, BL (sum/diff trick or angle sort around centroid — must be robust to rotated quads).
3. Output canvas: `W = max(len(top), len(bottom))`, `H = max(len(left), len(right))` computed at full resolution — using the max preserves the best-sampled dimension and never downsamples content.
4. `cv2.getPerspectiveTransform` + `cv2.warpPerspective(..., flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE)`.
5. OPTIONAL aspect correction: oblique shots distort the true aspect ratio. If W/H is within ~8% of A4 (1.414) or Letter (1.294), snap to it. (The full Zhang–He whiteboard-rectification aspect estimation from the homography is overkill for v1 — mention it in comments only.)
6. **No binarization, no "magic filter", no contrast enhancement.** Downstream is layout extraction + translation on the natural image; CamScanner-style black-and-white output would destroy information. Keep color exactly as captured.
7. Encode JPEG quality ≥ 95 and rebuild the PDF per §2.

Corners outside the original image bounds are fine — `warpPerspective` maps the missing region from replicated border pixels; combined with the `partial_capture` warning this is the correct behavior.

---

## 7. Edge-Case Catalog (must be handled or explicitly flagged)

| # | Case | Handling |
|---|------|----------|
| 1 | One corner missing (staple, tear, framing) | Method B line intersection |
| 2 | Entire edge out of frame | Border substitution + `partial_capture` warning |
| 3 | Phone/hand shadow across the page | Illumination normalization before edge detection; sharp-step edges beat soft shadow gradients |
| 4 | Fingers holding the page | Robust line fit treats the dent as an outlier |
| 5 | White paper on white desk | Color/edge signals dead → Method D deskew-only fallback |
| 6 | Patterned background (ruled cloth, tiles, wood grain lines) | Text-containment validation rejects quads that don't enclose the text mass |
| 7 | Document lying on another document | Same text-containment rule; prefer the innermost valid quad enclosing the text |
| 8 | Curled / folded page | Warp anyway, flag `curled_page_suspected`; true dewarping is out of scope v1 |
| 9 | Glare / flash hotspot | Normalization reduces it; never threshold/binarize output |
| 10 | 90° rotated capture | If dominant text-line direction is vertical, rotate 90° before boundary detection (180° detection needs OCR → out of scope; note in README) |
| 11 | Two-page open-book photo | Out of scope v1; if aspect + twin text columns with center fold suspected, flag `possible_book_spread` and pass through |
| 12 | Genuine scan that is slightly skewed | Classified as scan → untouched in v1 (do-no-harm). OPTIONAL config flag `deskew_scans` for later |

---

## 8. Build Order & Verification — build the test harness FIRST

There are **no real failure samples available**. Therefore Phase 1 is a synthetic data generator (`synth.py`) that creates ground-truth test cases from any clean scanned/born-digital PDF page:

1. Start from a clean page image (ground truth).
2. Apply a random homography: jitter the four corners independently (simulates handheld angle), record the true corners.
3. Composite onto a procedurally generated background — wood-like (low-frequency noise + directional streaks), fabric, plain colored, and near-white (for edge case #5). No downloaded assets.
4. Degradations, each with on/off + intensity params: soft directional shadow polygon crossing the page (edge case #3), vignette, blur gradient (sharp center → soft edges), Gaussian sensor noise, JPEG re-compression, slight rotation of the whole frame.
5. Corner-occlusion variants: crop the frame so 1 corner / 1 full edge / 2 adjacent corners are outside the image (edge cases #1–2).

**Metrics (implement as pytest + a CLI eval command):**

- Classifier: confusion matrix over a set of synthetic photos + untouched clean scans. Report false-positive rate on scans separately — it must be ~0.
- Boundary: mean corner error in px (where corners are in-frame) and IoU between the rectified output and the ground-truth page.
- Do-no-harm: feeding a clean scan PDF must produce a byte-identical (or at minimum pixel-identical) output.
- Sharpness: variance-of-Laplacian of rectified output ≥ ~0.9× that of the ground-truth page region.

**Phases (complete and verify each before the next):**

1. `pdf_io.py` + `synth.py` + metric harness → verify: extraction is native-res; synthetic set generates with ground truth.
2. `classifier.py` → verify: confusion matrix on synthetic set; FP rate on scans ≈ 0.
3. `boundary.py` + `rectify.py` → verify: corner error / IoU on synthetic set, including missing-corner and shadow variants.
4. `pipeline.py` + `cli.py` + debug visualization → verify: end-to-end on mixed synthetic PDFs (scan pages + photo pages in one file); only photo pages modified.
5. README: usage, config tuning guide (which threshold to move for which failure mode), known limitations (#8, #10, #11).

---

## 9. References (prior art this spec is built on)

These are for documentation and reviewer context; the spec above already contains everything needed, so you do not need to fetch them.

- Dropbox Engineering — *Fast and Accurate Document Detection for Scanning* (line detection → intersection → quad enumeration → perimeter scoring): https://dropbox.tech/machine-learning/fast-and-accurate-document-detection-for-scanning
- Tropin et al. — *Advanced Hough-based method for on-device document localization* (production Hough-based quad detection under compute constraints): https://arxiv.org/abs/2106.09987
- LearnOpenCV — *Automatic Document Scanner using OpenCV* (morphological closing to blank text + GrabCut background removal): https://learnopencv.com/automatic-document-scanner-using-opencv/
- Silva, Lins et al. — *Automatically Deciding if a Document was Scanned or Photographed* (2009; >99.9% with classical features, proving classifier feasibility): https://jucs.org/jucs_15_18/automatically_deciding_if_a/jucs_15_18_3364_3375_silva.pdf
- Docutain SDK blog — *Edge Detection for Image Processing* (Sobel vs. Canny comparison; demonstrates why fixed-parameter Canny fails on textured backgrounds — the wooden-floor example motivating the bilateral-filter + auto-Canny mandate in §5. Their final recommendation is a trained TensorFlow edge model, which is **out of scope** under Constraint 1; the multi-method cascade is our classical answer to the same robustness gap): https://sdk.docutain.com/blogartikel/edge-detection-for-image-processing
- Filestack blog — *Document Detection and Preprocessing API* (production pipeline confirming Method B's structure: edge map → Hough lines → intersections → four most-probable vertices → perspective transform. Their edge maps come from HED / U-Net deep models — **out of scope** here; GrabCut in Method C is the classical analogue of their segmentation mask. Note: their final Otsu/local-threshold binarization exists because their downstream is OCR — ours is layout extraction + translation on the natural image, which is exactly why §6 forbids binarization): https://blog.filestack.com/document-detection-enhancement-and-preprocessing-api/

---

State your assumptions before coding each phase. If any part of this spec is ambiguous or you see a simpler approach that satisfies the same constraints, say so before implementing.
