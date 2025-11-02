# PDF to EPUB AI Converter Scripts

A Python toolkit for converting PDF files to clean, readable EPUB format using AI-powered post-OCR correction and text refinement.

## Overview

This project provides a complete pipeline for converting PDF files to EPUB format:

1. **PDF OCR** - Extract text from PDF files using OCR when necessary
2. **OCR Cleanup** - Remove common OCR artifacts using regex and heuristics
3. **AI Refinement** - Use OpenAI GPT-4.1 to correct spelling, punctuation, and OCR errors
4. **EPUB Generation** - Convert the cleaned text to properly formatted EPUB files

## Features

- **Smart PDF text extraction** - Direct extraction or OCR fallback
- **Post-OCR correction** - Local regex cleanup + AI-powered refinement
- **AI text refinement** - OpenAI GPT-4.1 for spelling, grammar, and OCR error correction
- **Concurrent processing** - Parallel API calls for faster processing
- **Real-time cost tracking** - Detailed progress and cost estimation
- **Automatic chapter detection** - Smart EPUB structuring from headings
- **Intelligent text chunking** - Paragraph-aware splitting for optimal API usage
- **Multi-language OCR support** - All Tesseract language packs
- **Comprehensive error handling** - Retry logic and graceful failure recovery

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
2. Create a `.env` file in the project root:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

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
python openai_cleaner.py --in temp/document_clean.txt --out temp/document_refined.txt --model gpt-4o --max-cost 5 --confirm-cost

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
python openai_cleaner.py --in input.txt --out output.txt --model gpt-4o --max-cost 5 --confirm-cost
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
├── pdf_ocr.py             # PDF text extraction with OCR
├── process_ocr.py          # OCR cleanup with regex/heuristics
├── openai_cleaner.py       # AI-powered text refinement
├── convert_to_epub.py      # EPUB generation
├── run_pipeline.bat        # Windows batch script for full pipeline
├── run_pipeline.ps1        # PowerShell script for full pipeline
├── run_pipeline.sh         # Linux/macOS bash script for full pipeline
├── test_pdf_pipeline.bat   # Windows test pipeline (no AI)
├── sample_ocr_text.txt     # Sample OCR text for testing
├── .env.example           # Environment variables template
├── requirements.txt       # Python dependencies
├── output/                # Output directory for processed files
├── temp/                  # Temporary files directory
├── .env                   # Environment variables (API keys)
├── .gitignore            # Git ignore patterns
├── LICENSE               # MIT License
└── README.md             # This documentation
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
