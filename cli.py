from __future__ import annotations

import argparse
from pathlib import Path

from research_agent.agent import ResearchAgent, render_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Research a topic and generate a markdown report.")
    parser.add_argument("topic", help="Topic to research")
    parser.add_argument("--max-sources", type=int, default=8, help="Maximum number of sources to include")
    parser.add_argument("--output", default="research_report.md", help="Output markdown file path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    agent = ResearchAgent()
    agent.config.max_sources = max(3, args.max_sources)

    report = agent.research(args.topic)
    markdown = render_report(report)

    output_path = Path(args.output)
    output_path.write_text(markdown, encoding="utf-8")

    print(f"Research completed for: {args.topic}")
    print(f"Saved report to: {output_path.resolve()}")
    print(f"Sources used: {len(report.references)}")


if __name__ == "__main__":
    main()
