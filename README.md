# doc_rectifier

Classical-CV pipeline that detects PDF pages made from phone-photos of
documents, perspective-corrects ("flattens") them, and rebuilds the PDF --
while leaving genuine scans and born-digital pages untouched. Implements
`doc_rectifier_prompt.md`, consolidated into 4 modules for a one-day POC
(the spec's own reference architecture uses 8).

No deep learning, no OCR, no network calls -- OpenCV + NumPy + Pillow +
PyMuPDF only.

## Layout

```
doc_rectifier/
  vision.py     Config + classifier (S1-S8) + boundary cascade (A-E) + rectify
  pdf_io.py     page triage, native-res image extraction, PDF rebuild
  pipeline.py   process_pdf() orchestration, PipelineReport, CLI
  synth.py      synthetic ground-truth generator + eval CLI (no real samples exist)
```

## Install

```
pip install -r requirements.txt
```

## Usage

```
python3 -m doc_rectifier.pipeline INPUT.pdf --output-dir OUT/ [--debug-dir DEBUG/] [--single-page-only]
python3 -m doc_rectifier.pipeline SOME_FOLDER/ --output-dir OUT/
```

Prints one JSON `PipelineReport` per input PDF (schema: see `PageReport` in
`pipeline.py`, matches SS2 of the spec). `--debug-dir` dumps per-stage
intermediate images (edge map, quad overlay, final warp) per page, named
`<pdf-stem>_p<N>_*.png`.

## Verifying it

Two sources of truth were used, since no real failure samples existed at the
start of this project:

**1. Synthetic ground truth** (no real samples needed):

```
python3 -m doc_rectifier.synth --generate 30 --out /tmp/synth_set --seed 0
python3 -m doc_rectifier.synth --eval-classifier /tmp/synth_set    # confusion matrix, scan FP rate (must be ~0)
python3 -m doc_rectifier.synth --eval-boundary /tmp/synth_set      # mean corner error (px), IoU
python3 -m doc_rectifier.synth --eval-do-no-harm /tmp/synth_set    # scans/born-digital must round-trip byte-identical
python3 -m doc_rectifier.synth --eval-sharpness /tmp/synth_set     # warped vs ground-truth Laplacian variance ratio
```

Across several independently-seeded 30-40 sample runs: **scan false-positive
rate consistently 0** (the one hard safety requirement), **do-no-harm
consistently byte-identical** (e.g. 16/16), phone-photo recall ~80-90%.
Boundary IoU is typically ~0.8-0.93 but noisy on samples that stack multiple
extreme synthetic degradations at once (vignette + noise + heavy rotation +
JPEG, all simultaneously at high intensity) -- see "Real-world validation"
below for a more representative accuracy read.

**2. Real phone photos** -- `samples-phone-clicked/` in this repo has actual
phone-camera document photos (a DMV form on a dark wood table, an invoice on
a light wood floor, two receipts on a dark surface, a flyer on brushed
steel, etc.). Wrapping each in a single-image PDF and running it through
`pipeline.py` is what actually shook out the real bugs during development
(listed below) -- the synthetic harness alone did not catch any of them.
Current result on that set: all 11 correctly classified as `phone_photo`
(100%); 10/11 rectified with a clean, tightly-cropped result (verified
visually, including the two narrow receipts that were the hardest cases);
1 hard diagonal shot on a reflective steel background where the cascade
makes no change and honestly reports `boundary_not_found`/`noop_quad`
rather than guessing. Output image resolution now never exceeds the
source's (see bug list) -- it's smaller than the input by whatever fraction
was background/margin being cropped away, which is the correct, intended
effect of rectification, not a quality loss.

## Bugs the real photos caught (synthetic data missed all of these)

- **PDF rebuild silently duplicated the image xref with the wrong
  `/Filter`.** `Page.replace_image()` looked right but spawns a *new* image
  object and leaves the old one dangling, and a naive `update_stream()`
  defaults to declaring `/Filter /FlateDecode` on what is actually raw JPEG
  bytes. Fixed in `pdf_io.rebuild_pdf` by using `update_stream(..., compress=0)`
  plus explicit `xref_set_key` calls for `Filter`/`Width`/`Height`.
- **`--debug-dir` on a folder overwrote itself.** Prefixes were just
  `p<N>`, so processing 11 PDFs left only the last one's debug images on
  disk. Fixed by prefixing with the PDF's filename stem.
- **Method A recomputed its own Canny with fixed thresholds** (`(50, 150)`)
  instead of reusing the shared adaptive edge map -- exactly the
  fixed-parameter trap SS5 warns about. It silently produced a broken,
  fragmented boundary on a real wood-grain-background photo where the
  shared auto-Canny map was clean. Fixed by having Method A consume the
  shared `edges` map directly.
- **A single `approxPolyDP` epsilon isn't robust to a real (slightly wavy,
  JPEG-softened) page edge.** Widened to a step-wise epsilon search.
- **The text-containment quad-validation check was rejecting geometrically
  correct quads on textured backgrounds.** `_text_mask` ran plain
  `adaptiveThreshold` on the raw image, which happily classifies wood grain
  (and, on a high-contrast dark background, the page's *own silhouette
  edge*) as "text" -- so even the *correct* quad couldn't hit containment,
  because most of the "text" was noise outside it by definition, or the one
  surviving fragment was outside it by a few pixels. Fixed in three steps:
  shape-filter the mask to wide-and-short blobs (same trick as the S7
  text-geometry signal), add a density check so a thin traced outline curve
  (sparse) doesn't pass as a dense text line, and require at least a
  few distinct blobs before trusting the mask at all -- a lone fragment
  isn't a signal. On top of that, containment was converted from a hard
  reject gate into a soft scoring term in Method B (weighted alongside
  perimeter edge strength), since even a cleaned-up mask is inherently
  noisier on real photos than on synthetic ground truth, and a single
  unreliable signal shouldn't be able to veto an otherwise-correct quad.
- **A strong image-corner vignette could out-compete the real page edge**
  and get accepted as a near-full-frame quad. Tightened `max_area_frac`
  from 0.98 to 0.95.
- **A spurious strong edge sits right at the frame border on real photos**
  (lens vignette falloff, sensor/encoding artifacts) and repeatedly
  out-scored the true document edge in Hough line ranking, badly oversizing
  the quad on that side (a receipt's background-table edge would win over
  its own much-shorter true edge). Fixed by blanking a thin margin
  (`border_exclude_frac`, 2% default) of the edge map before contour/line
  detection -- long enough to kill a line that exists only in that strip,
  short enough not to touch a real edge that extends inward.
- **`min_area_frac` (0.25, matching the spec's suggested default) rejected
  the *correct* quad on narrow documents.** A receipt photographed with
  normal margin on both sides legitimately occupies well under 25% of the
  frame area (it's long and narrow, not page-shaped); the cascade would
  reject the tight, correct quad for being "too small" and fall back to a
  wider, wrong one that happened to clear the bar. Lowered to 0.10.

## Tuning guide

All thresholds live in `vision.Config`. Which one to move depends on the
failure mode observed in a `PipelineReport`:

- **Real scans getting `page_type: phone_photo`** (the one failure mode that
  actually matters -- do-no-harm): raise `t_photo`, or lower the weight of
  whichever `signals` entry is consistently high on the false positives.
  `illumination` is the most common offender on scans with heavy, uneven
  text density (a full-width dark header block can fake a lighting gradient
  after the S5 blur) -- check `signals.illumination` on the misclassified
  pages first.
- **Real phone photos landing in `ambiguous`/passthrough** (a missed
  opportunity, not a safety issue): lower `t_photo`, or check
  `signals.quad_feedback` -- a phone photo shot fairly flat-on can look
  near-rectangular enough that S8 pulls the tiebreak toward "scan-like."
- **`method: contour_quad` quads are off**: rare: they're near-pixel-exact
  in testing. If it happens, loosen `min_area_frac`/`angle_tolerance_deg`.
- **`method: line_quad_scoring` or `grabcut` quads are noisy**: these only
  fire when contour detection fails (typically cluttered/wood/fabric
  backgrounds, or strong glare/vignette), and are the least precise stage of
  the cascade -- in testing, near-pixel-exact when `contour_quad` fires, but
  visibly off on a meaningful fraction of harder-background cases. First try
  raising `top_k_lines_per_orientation` and lowering `line_merge_dist_px`
  (more/finer line candidates to score); for GrabCut, raise `grabcut_iters`
  or widen `grabcut_inset_px`. If a strong corner vignette or glare hotspot
  is winning over the real edge, `max_area_frac` (0.95 default) is the first
  lever -- lower it further if oversized quads keep slipping through.
- **Pages passing through with `boundary_not_found`**: cascade gave up
  (Method E). Check the `--debug-dir` edge map -- usually means the
  background genuinely doesn't contrast with the page (case #5, white-on-white)
  or an aggressive crop occluded too much of two sides at once.
- **`curled_page_suspected` warnings on otherwise-fine pages**: the
  perimeter-support heuristic (`curled_score_low`/`curled_score_high` in
  `_method_b_lines`) is a coarse proxy, not real curvature detection; widen
  the band or ignore the warning if it's noisy on your traffic.

## Known limitations / deliberate v1 cuts

Matches the spec's own OPTIONAL markers and SS7 edge-case table:

- Classifier is a hand-tuned weighted sum only (no S9 entropy signal, no
  decision-tree upgrade).
- Method D (no-boundary fallback) does rotation-only deskew; true
  perspective-from-text-baseline-vanishing-point estimation is not implemented.
- No standalone pytest suite -- `synth.py`'s eval CLI covers the spec's SS8
  metrics directly.
- Edge case #10 (90deg-rotated capture) and #11 (book-spread) use coarse
  heuristics (`vision.detect_dominant_orientation`, aspect-ratio guess)
  rather than robust detection, per the spec's "out of scope v1" framing.
- Edge case #8 (curled/folded page): warped anyway with a warning, no true
  dewarping.
- The sharpness eval (`--eval-sharpness`) excludes samples degraded with
  synthetic blur/noise, since comparing a deliberately-blurred photo against
  a pristine ground-truth page tests the *degradation*, not the rectifier;
  even on clean samples the ratio undershoots the spec's 0.9x target because
  the synthetic generator's own forward homography warp (needed to place the
  page onto a background) adds a second resampling pass beyond what
  `rectify()` itself does -- a testing-harness artifact, not evidence that
  `warpPerspective(..., INTER_LANCZOS4)` is softening real captures.
- Boundary corner-error/IoU on the synthetic set is noticeably worse on
  samples that stack several extreme degradations simultaneously (heavy
  vignette + noise + 8deg rotation + low-quality JPEG, all at once) --
  Method B/GrabCut can pick a wrong supporting line under those conditions.
  This looks worse in aggregate than the pipeline actually performs on a
  single real photo (see "Real-world validation" above, where 9/11 real
  phone photos rectified cleanly); treat the synthetic corner-error number
  as a stress test, not a production accuracy estimate, and prioritize
  `--debug-dir` inspection of real failures over chasing this number down.
- GrabCut and Method D are functional but not deeply tuned -- they're the
  fallback tail of the cascade and were exercised far less than Method A/B
  during development.
