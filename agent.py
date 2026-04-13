from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .llm_writer import LLMWriter
from .models import ResearchReport, SearchResult, SourceDocument
from .summarizer import summarize_documents, summarize_text
from .web_research import WebResearchClient, deduplicate_results


@dataclass
class ResearchConfig:
    max_queries: int = 4
    max_results_per_query: int = 5
    max_sources: int = 8


class ResearchAgent:
    def __init__(self, config: ResearchConfig | None = None) -> None:
        self.config = config or ResearchConfig()
        self.web = WebResearchClient()
        self.llm_writer = LLMWriter()

    def build_queries(self, topic: str) -> List[str]:
        base = topic.strip()
        candidates = [
            base,
            f"{base} latest developments",
            f"{base} statistics and trends",
            f"{base} challenges and opportunities",
            f"{base} future outlook",
        ]
        return candidates[: self.config.max_queries]

    def collect_sources(self, topic: str) -> List[SourceDocument]:
        all_results: List[SearchResult] = []
        for query in self.build_queries(topic):
            results = self.web.search(query, limit=self.config.max_results_per_query)
            all_results.extend(results)

        selected = deduplicate_results(all_results, keep=self.config.max_sources)
        docs = [self.web.fetch_source(result) for result in selected]
        return docs

    def research(self, topic: str) -> ResearchReport:
        sources = self.collect_sources(topic)

        for source in sources:
            combined_text = "\n".join([source.snippet, source.content])
            source.summary = summarize_text(combined_text, topic, max_sentences=5)

        executive = summarize_documents([s.summary for s in sources], topic, limit=7)
        detailed = summarize_documents([s.content for s in sources], topic, limit=14)

        report = ResearchReport(
            topic=topic,
            executive_summary=executive,
            detailed_findings=detailed,
            references=sources,
        )

        llm_markdown = self.llm_writer.write_report(topic, sources)
        if llm_markdown:
            # Preserve source list in structured model while returning richer markdown.
            report.detailed_findings = ["LLM-enhanced report generated."]
            report.executive_summary = ["See full markdown report below."]
            report._llm_markdown = llm_markdown  # type: ignore[attr-defined]

        return report


def render_report(report: ResearchReport) -> str:
    llm_markdown = getattr(report, "_llm_markdown", "")
    if llm_markdown:
        header = [
            f"# Research Report: {report.topic}",
            "",
            f"Generated on: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "",
        ]
        return "\n".join(header) + llm_markdown
    return report.to_markdown()
