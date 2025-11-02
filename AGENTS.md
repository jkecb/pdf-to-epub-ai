# Repository Guidelines

## Project Structure & Module Organization
Core logic lives in `pipeline/`: `main.py` coordinates the PDF → EPUB flow, submodules (`ocr.py`, `preprocess.py`, `refine.py`, `epub.py`) handle each stage, and `config.py` plus `logging.py` centralise configuration and telemetry. `__main__.py` keeps `python -m pipeline` as the canonical entry point. Repo root stores smoke tests (`test_api.py`, `test_chunks.py`, `test_subset.py`), Windows batch wrappers, and the sample source `Corpus Hermeticum.pdf`. Ephemeral artefacts belong in the directories named in `.env` (`OUTPUT_DIR`, `TEMP_DIR`) to avoid accidental commits.

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate` – create an isolated environment.
- `pip install -r requirements.txt` – install Python dependencies.
- `python -m pipeline run Corpus\ Hermeticum.pdf --max-pages 5 --max-cost 2 --confirm-cost` – full smoke test on a limited page range.
- `python test_chunks.py` / `python test_subset.py` – targeted regressions for chunking and partial pipelines.
- `python -m pipeline --help` – confirm new flags and usage text.

## Coding Style & Naming Conventions
Stick to PEP 8: 4-space indentation, snake_case identifiers, UpperCamelCase for classes such as `Page` in `pipeline/pages.py`. Preserve type hints and module-level docstrings; most files already import `from __future__ import annotations` to keep signatures forward-compatible. Extend existing modules instead of adding new top-level scripts, and route logging through `pipeline.logging.get_logger` so CLI verbosity switches remain effective.

## Testing Guidelines
Add focused tests near the logic they exercise; create `pipeline/tests/` if suites outgrow the root. Name files `test_<feature>.py` and prefer deterministic fixtures over uploading large PDFs. Before a PR lands, run `python test_chunks.py` and a constrained `python -m pipeline run ... --max-pages` invocation, reporting skipped long-form runs with rationale in the PR notes.

## Commit & Pull Request Guidelines
Model commit messages on the existing history: concise, capitalised, imperative summaries (e.g., `Consolidate CLI into pipeline package`) with optional body detail. PRs should outline motivation, enumerate major code paths touched, include CLI output or artefact locations, and call out configuration or dependency changes. Link related issues and request reviewers for cross-cutting edits (OCR, refinement, storage).

## Security & Configuration Tips
Keep secrets out of git—use `.env.example` for documentation and load values through `pipeline/config.py`. When sharing logs or telemetry, redact cost totals and document identifiers. New modules must respect the existing config loader so headless runs and cost guardrails continue to work without manual intervention.
