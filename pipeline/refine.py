from __future__ import annotations

"""
AI refinement stage.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List

from openai import OpenAI
from openai import AuthenticationError

from .config import PipelineConfig
from .logging import get_logger
from .pages import DocumentText, PageText

log = get_logger(__name__)

try:
    import tiktoken  # type: ignore

    TIKTOKEN_AVAILABLE = True
except ImportError:  # pragma: no cover
    TIKTOKEN_AVAILABLE = False
    tiktoken = None  # type: ignore
    log.warning("tiktoken not installed; token counts will be estimated.")


PRICING = {
    "gpt-4.1": {"input": 0.002 / 1000, "output": 0.008 / 1000},
    "gpt-4o": {"input": 0.005 / 1000, "output": 0.015 / 1000},
    "gpt-4": {"input": 0.03 / 1000, "output": 0.06 / 1000},
}


def _token_count(text: str, model: str) -> int:
    if TIKTOKEN_AVAILABLE:
        try:
            encoding = tiktoken.encoding_for_model(model)
        except Exception:
            encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    # Rough estimate
    words = len(text.split())
    return int(words / 0.7)


def _estimate_cost(tokens_in: int, tokens_out: int, model: str) -> float:
    if model not in PRICING:
        model = "gpt-4"
    price = PRICING[model]
    return tokens_in * price["input"] + tokens_out * price["output"]


@dataclass
class RefinementStats:
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0


class AIRefiner:
    """Wrapper around OpenAI chat completions for deterministic refinement."""

    def __init__(self, cfg: PipelineConfig, *, max_workers: int = 4) -> None:
        if not cfg.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY missing; AI refinement cannot run.")
        self.cfg = cfg
        self.client = OpenAI(api_key=cfg.openai_api_key)
        self.max_workers = max_workers
        self.stats = RefinementStats()

    def refine_document(self, doc: DocumentText) -> DocumentText:
        total_input_tokens = sum(
            _token_count(page.cleaned or page.raw, self.cfg.ai_model) for page in doc.pages
        )
        estimated_cost = _estimate_cost(total_input_tokens, total_input_tokens // 2, self.cfg.ai_model)
        log.info("AI refinement estimated cost: $%.4f", estimated_cost)

        if estimated_cost > self.cfg.max_cost_limit and not self.cfg.confirm_cost:
            raise RuntimeError(
                f"Estimated cost ${estimated_cost:.2f} exceeds limit ${self.cfg.max_cost_limit:.2f}. "
                "Rerun with --confirm-cost to proceed."
            )

        log.info("Refining %d pages with model %s", len(doc.pages), self.cfg.ai_model)

        refined_pages: List[PageText] = [PageText(index=p.index, raw=p.raw) for p in doc.pages]

        pages_to_process: List[PageText] = []
        for page in doc.pages:
            text = (page.cleaned if page.cleaned is not None else page.raw).strip()
            if text:
                pages_to_process.append(page)
            else:
                refined_pages[page.index - 1].cleaned = ""

        if pages_to_process:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {
                    executor.submit(self._refine_page, page): page.index
                    for page in pages_to_process
                }

                for future in as_completed(futures):
                    page_index = futures[future]
                    refined_text, stats = future.result()
                    refined_pages[page_index - 1].cleaned = refined_text
                    self.stats.input_tokens += stats.input_tokens
                    self.stats.output_tokens += stats.output_tokens
                    self.stats.cost_usd += stats.cost_usd

        log.info(
            "AI refinement complete: %d tokens in, %d tokens out, cost $%.2f",
            self.stats.input_tokens,
            self.stats.output_tokens,
            self.stats.cost_usd,
        )

        return DocumentText(source=doc.source, pages=refined_pages)

    def _refine_page(self, page: PageText) -> tuple[str, RefinementStats]:
        text = page.cleaned or page.raw

        system_prompt = (
            "You are a meticulous proof-reader. Clean up OCR mistakes, fix casing "
            "and punctuation, and preserve original paragraph and line breaks as far "
            "as possible. Remove page headers/footers but keep genuine content. "
            "Do not summarise or omit any sentences."
        )

        try:
            response = self.client.chat.completions.create(
                model=self.cfg.ai_model,
                temperature=0.1,
                max_tokens=3000,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": text,
                    },
                ],
            )
        except AuthenticationError as exc:  # pragma: no cover - requires live API
            raise RuntimeError(
                "OpenAI authentication failed. Check OPENAI_API_KEY and model access."
            ) from exc

        usage = response.usage
        result_text = response.choices[0].message.content.strip()
        stats = RefinementStats(
            input_tokens=usage.prompt_tokens,
            output_tokens=usage.completion_tokens,
            cost_usd=_estimate_cost(usage.prompt_tokens, usage.completion_tokens, self.cfg.ai_model),
        )
        return result_text, stats


__all__ = ["AIRefiner", "RefinementStats"]
