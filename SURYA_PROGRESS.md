# Surya OCR Integration Progress

Date: 2025-11-02  
Environment: cpu-only sandbox (no GPU acceleration)

## What’s been done
- Installed `surya-ocr==0.17.0` and confirmed available console entry point `surya_ocr`.
- Inspected package layout (`surya.scripts.ocr_text`) to understand callable CLI (`ocr_text_cli`).
- Attempted to run `surya_ocr` on *Corpus Hermeticum (Hermes Trismegistus).pdf* to fetch models.  
  - Initial invocation with `--page_range 0-2` exceeded command timeout (10 minutes) while downloading ~12 model components.  
  - Retried with `--page_range 0`; run aborted manually after confirming the download phase is the primary bottleneck (CPU-only host, large PyTorch checkpoints).
- Collected console usage help for future scripting (`surya_ocr --help`).

## Outstanding tasks
- Implement pipeline switches:
  - `--extract-only` (PyMuPDF direct text extraction, default).
  - `--ocr` with optional `--ocr-engine surya` (drop current Tesseract fallback).
- Wrap `surya_ocr` CLI (or underlying predictors) inside `pipeline/ocr.py`, handling:
  - Output capture (Surya emits JSON/Markdown – decide on intermediate format).
  - Temporary file management and page-to-text conversion.
  - Progress logging compatible with orchestrator.
- Update `requirements.txt` (add `surya-ocr` and remove `pytesseract`/`pdf2image` if no longer needed).
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

