from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    query: str


@dataclass
class SourceDocument:
    title: str
    url: str
    snippet: str
    query: str
    content: str
    summary: str = ""


@dataclass
class ResearchReport:
    topic: str
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    executive_summary: List[str] = field(default_factory=list)
    detailed_findings: List[str] = field(default_factory=list)
    references: List[SourceDocument] = field(default_factory=list)

    def to_markdown(self) -> str:
        lines: List[str] = []
        lines.append(f"# Research Report: {self.topic}")
        lines.append("")
        lines.append(f"Generated on: {self.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        lines.append("")
        lines.append("## Executive Summary")
        if self.executive_summary:
            lines.extend([f"- {item}" for item in self.executive_summary])
        else:
            lines.append("- No summary points were generated.")

        lines.append("")
        lines.append("## Detailed Findings")
        if self.detailed_findings:
            lines.extend([f"- {item}" for item in self.detailed_findings])
        else:
            lines.append("- No detailed findings were generated.")

        lines.append("")
        lines.append("## Sources")
        if not self.references:
            lines.append("- No references were collected.")
        else:
            for idx, source in enumerate(self.references, start=1):
                lines.append(f"{idx}. [{source.title}]({source.url})")

        return "\n".join(lines)
