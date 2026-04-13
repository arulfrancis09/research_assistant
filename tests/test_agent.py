import types

from research_agent.agent import ResearchAgent, ResearchConfig
from research_agent.models import SearchResult, SourceDocument


class DummyWeb:
    def search(self, query: str, limit: int = 5):
        return [
            SearchResult(title="A", url="https://example.com/a", snippet="alpha snippet", query=query),
            SearchResult(title="B", url="https://example.com/b", snippet="beta snippet", query=query),
        ][:limit]

    def fetch_source(self, result: SearchResult, max_chars: int = 12000):
        return SourceDocument(
            title=result.title,
            url=result.url,
            snippet=result.snippet,
            query=result.query,
            content=f"{result.title} has useful information about climate policy and market trends.",
        )


class DummyLLM:
    enabled = False

    def write_report(self, topic, sources):
        return ""


def test_research_generates_report():
    agent = ResearchAgent(ResearchConfig(max_queries=2, max_results_per_query=2, max_sources=3))
    agent.web = DummyWeb()
    agent.llm_writer = DummyLLM()

    report = agent.research("climate policy")
    assert report.topic == "climate policy"
    assert len(report.references) >= 1
    assert len(report.executive_summary) >= 1


def test_query_builder_limits_queries():
    agent = ResearchAgent(ResearchConfig(max_queries=3))
    queries = agent.build_queries("battery storage")
    assert len(queries) == 3
    assert queries[0] == "battery storage"
