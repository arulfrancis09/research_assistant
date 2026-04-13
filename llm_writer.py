from __future__ import annotations

import os
from typing import List

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - optional dependency
    OpenAI = None  # type: ignore[assignment]

from .models import SourceDocument


class LLMWriter:
    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.base_url = os.getenv("OPENAI_BASE_URL")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
        self._client = None

        if self.api_key and OpenAI is not None:
            self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    @property
    def enabled(self) -> bool:
        return self._client is not None

    def write_report(self, topic: str, sources: List[SourceDocument]) -> str:
        if not self._client:
            return ""

        context_chunks = []
        for idx, src in enumerate(sources, start=1):
            content = src.summary or src.content
            content = content[:1800]
            context_chunks.append(
                f"[{idx}] {src.title}\nURL: {src.url}\nSnippet: {src.snippet}\nSummary: {content}"
            )
        context = "\n\n".join(context_chunks)

        prompt = (
            "You are a research analyst. Create a high-quality markdown report with this structure:\n"
            "1) Executive Summary (5-8 bullets)\n"
            "2) Background and Context\n"
            "3) Current Landscape\n"
            "4) Key Challenges and Risks\n"
            "5) Opportunities and Future Outlook\n"
            "6) Actionable Recommendations\n"
            "7) References as numbered citations [1], [2], ...\n"
            "Use only the provided sources. Do not invent facts.\n"
            f"Topic: {topic}\n\n"
            f"Sources:\n{context}"
        )

        resp = self._client.responses.create(
            model=self.model,
            input=prompt,
            temperature=0.2,
        )
        return (resp.output_text or "").strip()
