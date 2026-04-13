from __future__ import annotations

import base64
from urllib.parse import parse_qs, quote_plus, urlparse

import requests
try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover - optional until installed
    BeautifulSoup = None  # type: ignore[assignment]

from .models import SearchResult, SourceDocument


HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9",
}


class WebResearchClient:
    def __init__(self, timeout: int = 15) -> None:
        self.timeout = timeout

    def search(self, query: str, limit: int = 8) -> list[SearchResult]:
        if BeautifulSoup is None:
            raise RuntimeError("beautifulsoup4 is required for web search parsing. Install from requirements.txt")
        primary = self._search_bing(query, limit=limit)
        if primary:
            return primary
        return self._search_ddg(query, limit=limit)

    def _search_bing(self, query: str, limit: int = 8) -> list[SearchResult]:
        url = (
            f"https://www.bing.com/search?q={quote_plus(query)}"
            f"&count={max(limit, 10)}&setlang=en-US&mkt=en-US&cc=US&ensearch=1"
        )
        response = requests.get(url, headers=HEADERS, timeout=self.timeout)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        results: list[SearchResult] = []
        nodes = soup.select("li.b_algo")

        for node in nodes:
            link = node.select_one("h2 a")
            snippet_node = node.select_one("div.b_caption p")
            if not link:
                continue

            title = " ".join(link.get_text(" ", strip=True).split())
            href = link.get("href", "").strip()
            href = self._resolve_bing_redirect(href)
            snippet = ""
            if snippet_node:
                snippet = " ".join(snippet_node.get_text(" ", strip=True).split())

            if not href or not href.startswith("http"):
                continue

            results.append(SearchResult(title=title, url=href, snippet=snippet, query=query))
            if len(results) >= limit:
                break

        return results

    def _resolve_bing_redirect(self, href: str) -> str:
        if not href.startswith("https://www.bing.com/ck/a"):
            return href
        try:
            parsed = urlparse(href)
            payload = parse_qs(parsed.query).get("u", [""])[0]
            if payload.startswith("a1"):
                encoded = payload[2:]
                encoded += "=" * (-len(encoded) % 4)
                decoded = base64.urlsafe_b64decode(encoded).decode("utf-8", errors="ignore")
                if decoded.startswith("http"):
                    return decoded
        except Exception:
            pass
        try:
            resp = requests.get(href, headers=HEADERS, timeout=self.timeout, allow_redirects=True)
            final_url = resp.url
            if final_url and final_url.startswith("http"):
                return final_url
        except Exception:
            pass
        return href

    def _search_ddg(self, query: str, limit: int = 8) -> list[SearchResult]:
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        response = requests.get(url, headers=HEADERS, timeout=self.timeout)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        results: list[SearchResult] = []
        nodes = soup.select("div.result")

        for node in nodes:
            link = node.select_one("a.result__a")
            snippet_node = node.select_one("a.result__snippet") or node.select_one("div.result__snippet")
            if not link:
                continue

            title = " ".join(link.get_text(" ", strip=True).split())
            href = link.get("href", "").strip()
            snippet = ""
            if snippet_node:
                snippet = " ".join(snippet_node.get_text(" ", strip=True).split())

            if not href or not href.startswith("http"):
                continue

            results.append(SearchResult(title=title, url=href, snippet=snippet, query=query))
            if len(results) >= limit:
                break

        return results

    def fetch_source(self, result: SearchResult, max_chars: int = 12000) -> SourceDocument:
        text = ""
        try:
            if BeautifulSoup is None:
                raise RuntimeError("beautifulsoup4 is required for page content extraction.")
            response = requests.get(result.url, headers=HEADERS, timeout=self.timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            for tag in soup(["script", "style", "noscript", "svg", "header", "footer", "nav"]):
                tag.decompose()

            blocks = []
            for node in soup.find_all(["h1", "h2", "h3", "p", "li"]):
                chunk = " ".join(node.get_text(" ", strip=True).split())
                if len(chunk) >= 40:
                    blocks.append(chunk)

            text = "\n".join(blocks)
            if len(text) > max_chars:
                text = text[:max_chars]
        except Exception as exc:
            # Fallback: r.jina.ai mirrors web pages in clean text format.
            try:
                mirror = f"https://r.jina.ai/http://{result.url.removeprefix('http://').removeprefix('https://')}"
                fallback = requests.get(mirror, headers=HEADERS, timeout=self.timeout)
                fallback.raise_for_status()
                text = fallback.text[:max_chars]
            except Exception:
                text = f"Could not fetch full page content. Error: {exc}"

        return SourceDocument(
            title=result.title,
            url=result.url,
            snippet=result.snippet,
            query=result.query,
            content=text,
        )


def deduplicate_results(results: list[SearchResult], keep: int) -> list[SearchResult]:
    seen_urls = set()
    seen_domains = set()
    deduped: list[SearchResult] = []

    for result in results:
        normalized = result.url.split("#", 1)[0]
        domain = urlparse(normalized).netloc.lower()
        if normalized in seen_urls:
            continue

        domain_penalty = domain in seen_domains
        if domain_penalty and len(deduped) >= max(3, keep // 2):
            continue

        seen_urls.add(normalized)
        seen_domains.add(domain)
        deduped.append(result)
        if len(deduped) >= keep:
            break

    return deduped
