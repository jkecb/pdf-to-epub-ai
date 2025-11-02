# PDF to EPUB AI Converter Scripts

A Python toolkit for converting PDF files to clean, readable EPUB format using AI-powered post-OCR correction and text refinement.

## Overview

This project provides a complete pipeline for converting PDF files to EPUB format:

1. **PDF OCR** - Extract text from PDF files using OCR when necessary
2. **OCR Cleanup** - Remove common OCR artifacts using regex and heuristics
3. **AI Refinement** - Use OpenAI GPT-4.1 to correct spelling, punctuation, and OCR errors
4. **EPUB Generation** - Convert the cleaned text to properly formatted EPUB files

## Features

- **Python orchestrator** – Single entry point (`python -m pipeline`) manages OCR, cleaning, AI refinement, and EPUB generation with shared configuration.
- **Page-aware workflow** – Every stage preserves page boundaries so EPUBs mirror the source pagination and plain-text exports stay easy to audit.
- **Flexible extraction** – Tries direct text extraction first, with optional Surya OCR for page images when the PDF lacks a text layer.
- **Robust preprocessing** – Removes headers/footers, repairs soft-hyphen breaks, normalises whitespace, and protects list/heading structure.
- **OpenAI refinement** – Deterministic prompts with concurrency, cost tracking, and skip logic for empty pages; works with any GPT-4.1-compatible key.
- **Cost and progress telemetry** – Live token counts, cost estimates, and guardrails (`--max-cost`, `--confirm-cost`) for long documents.
- **Modular CLI utilities** – Each stage remains available as a standalone script for debugging or bespoke workflows.

## Installation

### Requirements

- Python 3.7+
- OpenAI API key

### Dependencies

Install required packages:

```bash
# Install from requirements.txt (recommended)
pip install -r requirements.txt

# Or install individually:
pip install openai python-dotenv ebooklib tqdm tiktoken PyMuPDF pillow surya-ocr
```

**System Notes:**
- Surya ships large neural checkpoints; the first run will download ~2 GB of weights to your cache.
- GPU acceleration (CUDA or Apple M‑series MPS) dramatically speeds up Surya. CPU-only runs work but can be slow.
- Ensure you have enough disk space in your cache directory (defaults to `~/Library/Caches/datalab` on macOS).

### Setup

1. Clone this repository
2. Create a `.env` file in the project root (the orchestrator loads these values automatically):
   ```env
   OPENAI_API_KEY=sk-your-key
   AI_MODEL=gpt-4.1
   OUTPUT_DIR=output
   TEMP_DIR=temp
   MAX_COST_LIMIT=5
   ```
   Adjust any paths or limits to suit your environment. CLI flags always take precedence over `.env` values.

## Usage

### Automated Pipeline

Run the full workflow with the new CLI:

```bash
python -m pipeline run "document.pdf" --ocr-engine surya --max-cost 5 --confirm-cost
```

Useful flags:

- `--ocr-engine {text|surya}` – choose between direct text extraction or Surya OCR.
- `--page-range 5-120` – limit processing to a 1-based inclusive slice.
- `--skip-ai` – stop after heuristic cleanup (no OpenAI cost).
- `--max-pages N` – cap the number of pages processed after other filters (handy for smoke tests).
- `--force-ocr` – bypass direct extraction and run the chosen OCR engine.
- `--max-cost` / `--confirm-cost` – cost guardrails for OpenAI refinement.

### Manual Step-by-Step Process

For manual control or debugging, each stage is available as a subcommand:

```bash
# Step 1: Extract text from PDF (OCR if needed)
python -m pipeline ocr document.pdf --output temp/document_ocr.txt --max-pages 5

# Step 2: Clean OCR text with the heuristic pipeline
python -m pipeline clean --input temp/document_ocr.txt --output temp/document_clean.txt

# Step 3: AI refinement (costs money!)
python -m pipeline refine --input temp/document_clean.txt --output temp/document_refined.txt --max-cost 5 --confirm-cost

# Step 4: Convert to EPUB while preserving page boundaries
python -m pipeline epub --input temp/document_refined.txt --output output/document.epub
```

### Subcommands Overview

#### `python -m pipeline ocr`

Extracts text from PDFs, automatically falling back to OCR when needed.

```bash
python -m pipeline ocr document.pdf --ocr-engine surya --output document_ocr.txt --page-range 10-25
```

- `--ocr-engine {text|surya}` selects the extraction method.
- `--force-ocr` forces Surya even when a text layer exists.
- `--page-range` and `--max-pages` combine to keep experiments focused.

#### `python -m pipeline clean`

Applies regex/heuristic cleanup to page-marked text.

```bash
python -m pipeline clean --input document_ocr.txt --output document_clean.txt
```

#### `python -m pipeline refine`

Runs the OpenAI-based refinement stage.

```bash
python -m pipeline refine --input document_clean.txt --output document_refined.txt --max-cost 5 --confirm-cost
```

- `--ai-model` overrides the model declared in `.env`.
- `--max-cost` / `--confirm-cost` keep spending in check.
- `--pdf` optionally links back to the original PDF for metadata.

#### `python -m pipeline epub`

Generates an EPUB with page-by-page spine entries.

```bash
python -m pipeline epub --input document_refined.txt --output document.epub
```

- `--pdf` (optional) improves metadata when the original PDF is still available.

## Testing

No automated regression suite ships with the repository today. When changing the pipeline, run a targeted Surya-backed conversion with a small `--page-range` to smoke test the extraction/cleanup flow before processing a full document.

## Configuration

### Environment Variables

The orchestrator and the per-stage CLIs read their defaults from `.env`:

| Key | Description | Default |
| --- | --- | --- |
| `OPENAI_API_KEY` | API key used by `openai` library. | *required* |
| `AI_MODEL` | Chat-completions model for refinement. | `gpt-4.1` |
| `OUTPUT_DIR` | Directory for final EPUB/TXT artefacts. | `output/` |
| `TEMP_DIR` | Scratch space for OCR/intermediate text. | `temp/` |
| `MAX_TOKENS_PER_CHUNK` | Upper bound for AI chunk size. | `3000` |
| `MAX_COST_LIMIT` | USD ceiling before prompting for confirmation. | `10.0` |

Override any of these at runtime via CLI flags (e.g., `python -m pipeline doc.pdf --max-cost 3`).

### Chunking Parameters

The AI refinement tool splits text into chunks for processing:

- Default: 2500 tokens per chunk (optimal for context and cost)
- Chunks are created at paragraph boundaries when possible
- Large paragraphs are split at sentence boundaries

### Model Selection

Supported OpenAI models:
- `gpt-4.1` (recommended) - Best balance of quality and cost
- `gpt-4` - Higher quality, higher cost
- `gpt-4o` - Alternative model option

### Concurrency

The AI refinement tool processes chunks concurrently:
- Default: 5 concurrent requests
- Includes rate limiting and error handling
- Progress tracking with cost estimates

## Project Structure

```
pdf-to-epub-ai/
├── pipeline/                 # Shared infrastructure used by every entry point
│   ├── __init__.py
│   ├── __main__.py           # Enables `python -m pipeline`
│   ├── config.py             # Env/CLI configuration resolver
│   ├── logging.py            # Central logging config
│   ├── main.py               # Orchestrator CLI
│   ├── ocr.py                # Direct + OCR extraction helpers
│   ├── pages.py              # Page dataclasses
│   ├── preprocess.py         # Heuristic text cleanup
│   ├── refine.py             # OpenAI integration and cost tracking
│   └── storage.py            # Page-oriented I/O helpers
├── pdf_ocr.py                # Standalone OCR CLI wrapper
├── process_ocr.py            # Standalone cleanup CLI wrapper
├── openai_cleaner.py         # Standalone AI refinement CLI wrapper
├── convert_to_epub.py        # Standalone EPUB conversion CLI wrapper
├── test_*.py / *.bat         # Utility scripts for smoke tests
├── requirements.txt          # Python dependencies
├── README.md                 # This documentation
└── LICENSE
```

## Error Handling

- **API failures**: Automatic retry with exponential backoff
- **Rate limiting**: Built-in delays and concurrency limits
- **File errors**: Comprehensive error messages and graceful degradation
- **Token limits**: Automatic text chunking with size validation

## Cost Management

The AI refinement tool provides detailed cost tracking:
- Real-time cost accumulation
- Estimated total cost based on progress
- Token usage statistics (input/output)
- Cost per chunk analysis

**Rule of thumb:** with `gpt-4.1`, expect roughly $0.005–$0.006 per source page (about 600 input / 540 output tokens). Use `--max-cost` and `--confirm-cost` to prevent surprises on very long documents.

## Tips for Best Results

1. **OCR Quality**: Start with the highest quality OCR possible
2. **Preprocessing**: Use `process_ocr.py` before AI refinement to reduce costs
3. **Testing**: Use `test_subset.py` to validate results before processing large files
4. **Model Selection**: GPT-4.1 provides excellent results at lower cost than GPT-4
5. **Chunking**: Default settings work well, but adjust if you notice context issues

## Troubleshooting

### Common Issues

**"OPENAI_API_KEY not found"**
- Ensure `.env` file exists with valid API key
- Check file is in project root directory

**"API rate limit exceeded"**
- Reduce concurrent processing (modify `batch_size` in code)
- Add delays between requests

**"Chunks too large"**
- Reduce `max_tokens` parameter in chunking
- Check for very long paragraphs without proper breaks

**Poor chapter detection**
- Ensure chapter headings follow standard format (Chapter 1, Part I, etc.)
- Manual heading cleanup may be needed before conversion

## Contributing

This is a specialized tool for PDF to EPUB conversion. Feel free to fork and adapt for your specific needs.

Contributions, bug reports, and feature requests are welcome!

## License

MIT License - see LICENSE file for details.
