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
- **Flexible extraction** – Attempts direct text extraction first, with automatic fallback to high-quality OCR (PyMuPDF + pdf2image + Tesseract).
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
pip install openai python-dotenv ebooklib tqdm tiktoken PyMuPDF pytesseract pillow pdf2image
```

**System Dependencies:**
- **Tesseract OCR**: Required for OCR functionality
  - Windows: Download from [GitHub releases](https://github.com/UB-Mannheim/tesseract/wiki)
  - macOS: `brew install tesseract`
  - Ubuntu: `sudo apt install tesseract-ocr`
- **Poppler** (optional): Improves PDF to image conversion
  - Windows: Download from [poppler releases](https://github.com/oschwartz10612/poppler-windows/releases)
  - macOS: `brew install poppler`
  - Ubuntu: `sudo apt install poppler-utils`

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

The recommended entry point is the Python orchestrator:

```bash
python -m pipeline "document.pdf" --max-pages 10 --max-cost 5 --confirm-cost
```

Key options:

- `--skip-ai` – run only the local OCR + cleaning stages.
- `--max-pages N` – process only the first *N* pages (useful for smoke tests).
- `--tesseract-lang lang` – override the OCR language (defaults to `eng`).
- `--max-cost` / `--confirm-cost` – guardrails for OpenAI usage.

The wrapper scripts now delegate to the orchestrator, so you can still use them if you prefer platform-specific launchers:

```bash
./run_pipeline.sh document.pdf --skip-ai
```

```powershell
PS> .\run_pipeline.ps1 document.pdf --max-pages 5
```

```batch
REM Windows CMD
run_pipeline.bat document.pdf --tesseract-lang eng+ron
```

### Manual Step-by-Step Process

For manual control or debugging, each stage still has its own CLI wrapper:

```bash
# Step 1: Extract text from PDF (OCR if needed)
python pdf_ocr.py --in document.pdf --out temp/document_ocr.txt --max-pages 5

# Step 2: Clean OCR text with the heuristic pipeline
python process_ocr.py --in temp/document_ocr.txt --out temp/document_clean.txt

# Step 3: AI refinement (costs money!)
python openai_cleaner.py --in temp/document_clean.txt --out temp/document_refined.txt --model gpt-4.1 --max-cost 5 --confirm-cost

# Step 4: Convert to EPUB while preserving page boundaries
python convert_to_epub.py --in temp/document_refined.txt --out output/document.epub
```

### Individual Tools

#### PDF OCR (`pdf_ocr.py`)

Extracts text from PDF files using OCR when necessary:

```bash
python pdf_ocr.py --in document.pdf --out document.txt --max-pages 20
```

**Options:**
- `--language`: Tesseract language code (default: `eng`).
- `--force-ocr`: Force OCR even if direct text extraction works.
- `--max-pages`: Limit processing to the first *N* pages (speeds up testing).
- `--list-languages`: Show available Tesseract languages.
- `--check-deps`: Check if all dependencies are installed.

**Features:**
- **Smart extraction**: Tries direct text extraction first (faster)
- **OCR fallback**: Uses Tesseract OCR for image-based PDFs
- **Multiple backends**: Supports PyMuPDF, pdf2image, and Tesseract
- **High quality**: 300 DPI image conversion for better OCR results
- **Multi-language**: Supports all Tesseract language packs

**Dependencies:**
```bash
pip install PyMuPDF pytesseract pillow pdf2image
```

*Note: Also requires Tesseract OCR system installation and optionally Poppler for pdf2image.*

#### OCR Cleanup (`process_ocr.py`)

Cleans raw OCR text using regex patterns and heuristics:

```bash
python process_ocr.py --in input.txt --out output/clean.txt
```

**Features:**
- Removes repeated headers/footers and page counters.
- Repairs hyphenated and soft-hyphen word breaks.
- Re-flows paragraphs while respecting lists and headings.
- Normalizes whitespace and punctuation.
- Cleans up common OCR glyph substitutions.

#### AI Refinement (`openai_cleaner.py`)

Uses OpenAI's API to correct spelling, punctuation, and OCR errors:

```bash
python openai_cleaner.py --in input.txt --out output.txt --model gpt-4.1 --max-cost 5 --confirm-cost
```

**Options:**
- `--model`: Choose OpenAI model (default: value from `.env`, typically `gpt-4.1`).
- `--max-cost`: Estimated cost ceiling in USD (defaults to `MAX_COST_LIMIT`).
- `--confirm-cost`: Required when the estimate exceeds the cost ceiling.
- `--log-level`: Adjust verbosity while debugging.

The refiner processes pages concurrently, tracks token usage and cost, and falls back gracefully if the OpenAI credentials are missing or invalid.

**Cost Estimation:**
- GPT-4.1: ~$0.002 per 1K input tokens, ~$0.008 per 1K output tokens
- Typical 200-page book: $2-8 depending on content

#### EPUB Conversion (`convert_to_epub.py`)

Converts cleaned text to EPUB format:

```bash
python convert_to_epub.py --in input.txt --out output.epub
```

**Features:**
- Preserves original page boundaries (each page becomes a spine item).
- Generates a clean EPUB with TOC and default styling.
- Works equally well on heuristic-only or AI-refined text.

## Testing

The project includes several test scripts:

- `test_api.py` - Test OpenAI API connectivity
- `test_chunks.py` - Test text chunking logic  
- `test_subset.py` - Process a small subset for testing

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
| `TESSERACT_LANG` | Default OCR language code. | `eng` |

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
├── run_pipeline.{sh,ps1,bat} # Thin wrappers around the orchestrator
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
