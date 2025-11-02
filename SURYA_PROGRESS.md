# Surya OCR Integration Progress

Date: 2025-11-02  
Environment: cpu-only sandbox (no GPU acceleration)

## What's been done
- Installed `surya-ocr==0.17.0` and confirmed available console entry point `surya_ocr`.
- Inspected package layout (`surya.scripts.ocr_text`) to understand callable CLI (`ocr_text_cli`).
- Attempted to run `surya_ocr` on *Corpus Hermeticum (Hermes Trismegistus).pdf* to fetch models.  
  - Initial invocation with `--page_range 0-2` exceeded command timeout (10 minutes) while downloading ~12 model components.  
  - Retried with `--page_range 0`; run aborted manually after confirming the download phase is the primary bottleneck (CPU-only host, large PyTorch checkpoints).
- Collected console usage help for future scripting (`surya_ocr --help`).
- Added CLI switches (`--ocr-engine`, `--page-range`) so contributors can select between direct text or Surya extraction for both `run` and `ocr` commands.
- Refactored `pipeline/ocr.py` to support the new engines, paginate requests consistently, and execute Surya via its CLI while mapping predictions back to page markers.
- Updated configuration handling and requirements to drop Tesseract/pdf2image and include `surya-ocr`. Removed PaddleOCR after repeated macOS runtime issues.
- Installed runtime dependencies (`pip install -r requirements.txt`) on macOS with GPU support and verified Surya extraction via `python -m pipeline ocr Corpus\ Hermeticum.pdf --ocr-engine surya --page-range 1-2`, producing expected text markers.
- Confirmed the full pipeline (with `--skip-ai`) completes on a Surya-backed run covering the opening pages, generating cleaned text and EPUB artefacts.
- Smoke-tested Surya on mid-document prose (`--page-range 5-6`) to confirm paragraph extraction quality and bibliography handling.

## Outstanding tasks
- Revise README installation instructions (GPU recommended, larger dependency footprint, model download notes).
- Test end-to-end on GPU-enabled host to ensure Surya completes inference quickly enough.

## Recommendations for GPU host
1. Re-run model download once (`surya_ocr <pdf> --page_range 0 --output_dir scratch`). The cached weights will prevent repeat downloads.
2. After confirming Surya’s CLI output structure, integrate it via Python subprocess or direct API calls for faster execution.
3. Validate pipeline on a multi-language sample (Greek + Latin) to compare accuracy vs. PyMuPDF-only extraction.

## Current pipeline behavior (clarification)
- The orchestrator never writes back into the original PDF.  
  - PyMuPDF extraction reads existing text layers.  
  - OCR (Tesseract today, Surya pending) outputs separate text files that feed cleanup/refinement/EPUB stages.  
- For users with high-quality pre-OCR’d PDFs, PyMuPDF extraction remains preferable; OCR should be opt-in and only recommended when the PDF lacks a usable text layer.
