"""Real-world research tools: web search and URL fetching.

These tools are called by the LLM during agentic research loops, giving agents
access to live information the same way Claude Code uses bash/grep/read.
"""

from __future__ import annotations

import logging
import re
import textwrap
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Result schemas
# ---------------------------------------------------------------------------


@dataclass
class WebSearchHit:
    title: str
    url: str
    snippet: str
    source: str = ""


@dataclass
class FetchedPage:
    url: str
    title: str
    text: str
    word_count: int
    success: bool
    error: str = ""


@dataclass
class ResearchToolResult:
    """Aggregated results returned by one tool-call round."""

    search_hits: list[WebSearchHit] = field(default_factory=list)
    fetched_pages: list[FetchedPage] = field(default_factory=list)

    def as_context_block(self) -> str:
        """Format all results as a readable context block for the LLM."""
        lines: list[str] = []
        if self.search_hits:
            lines.append("### Web Search Results")
            for hit in self.search_hits:
                lines.append(f"**{hit.title}**")
                lines.append(f"URL: {hit.url}")
                lines.append(hit.snippet)
                lines.append("")
        if self.fetched_pages:
            lines.append("### Fetched Page Content")
            for page in self.fetched_pages:
                if page.success:
                    lines.append(f"**{page.title}** ({page.url})")
                    lines.append(page.text[:3000])
                    lines.append("")
                else:
                    lines.append(f"[Could not fetch {page.url}: {page.error}]")
                    lines.append("")
        return "\n".join(lines) if lines else "No tool results available."


# ---------------------------------------------------------------------------
# Web Search
# ---------------------------------------------------------------------------


def web_search(query: str, max_results: int = 6) -> list[WebSearchHit]:
    """Search the web using DuckDuckGo. Returns a ranked list of hits."""
    try:
        from duckduckgo_search import DDGS  # type: ignore[import]

        with DDGS() as ddgs:
            raw = list(ddgs.text(query, max_results=max_results))
        hits: list[WebSearchHit] = []
        for item in raw:
            hits.append(
                WebSearchHit(
                    title=item.get("title", ""),
                    url=item.get("href", ""),
                    snippet=item.get("body", ""),
                    source=_domain(item.get("href", "")),
                )
            )
        logger.debug("web_search(%r) → %d hits", query, len(hits))
        return hits
    except Exception as exc:
        logger.warning("web_search failed for %r: %s", query, exc)
        return []


# ---------------------------------------------------------------------------
# URL Fetching
# ---------------------------------------------------------------------------


def fetch_page_text(url: str, max_chars: int = 5000) -> FetchedPage:
    """Fetch a URL and extract readable text. Strips boilerplate aggressively."""
    try:
        import requests
        from bs4 import BeautifulSoup

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (compatible; BlogResearchAgent/1.0; "
                "+https://github.com/blog-series-agent)"
            )
        }
        resp = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        # Remove navigation, scripts, styles, ads
        for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form"]):
            tag.decompose()

        # Prefer <article>, <main>, or <body>
        content_tag = soup.find("article") or soup.find("main") or soup.body
        raw_text = content_tag.get_text(separator="\n") if content_tag else soup.get_text(separator="\n")

        # Normalize whitespace
        lines = [ln.strip() for ln in raw_text.splitlines()]
        lines = [ln for ln in lines if ln and len(ln) > 20]
        text = "\n".join(lines)

        # Deduplicate adjacent identical lines (common in crawled sites)
        deduped: list[str] = []
        for line in text.splitlines():
            if not deduped or line != deduped[-1]:
                deduped.append(line)
        text = "\n".join(deduped)[:max_chars]

        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else _domain(url)

        logger.debug("fetch_page_text(%r) → %d chars", url, len(text))
        return FetchedPage(
            url=url,
            title=title,
            text=text,
            word_count=len(text.split()),
            success=True,
        )

    except Exception as exc:
        logger.warning("fetch_page_text failed for %r: %s", url, exc)
        return FetchedPage(
            url=url,
            title="",
            text="",
            word_count=0,
            success=False,
            error=str(exc),
        )


# ---------------------------------------------------------------------------
# ResearchToolkit — the callable interface for agents
# ---------------------------------------------------------------------------


class ResearchToolkit:
    """
    Bundles web_search and fetch_page_text into an interface that agents call.

    This mirrors how Claude Code exposes Bash/Grep/Read to the LLM: the model
    decides what to look for, the toolkit executes it, and results flow back
    into the context window.
    """

    def __init__(
        self,
        *,
        max_search_results: int = 6,
        max_fetch_chars: int = 5000,
        max_fetches_per_section: int = 3,
        enabled: bool = True,
    ) -> None:
        self.max_search_results = max_search_results
        self.max_fetch_chars = max_fetch_chars
        self.max_fetches_per_section = max_fetches_per_section
        self.enabled = enabled

    # ------------------------------------------------------------------
    # Public interface used by agents
    # ------------------------------------------------------------------

    def search(self, query: str) -> list[WebSearchHit]:
        if not self.enabled:
            return []
        return web_search(query, max_results=self.max_search_results)

    def fetch(self, url: str) -> FetchedPage:
        if not self.enabled:
            return FetchedPage(url=url, title="", text="", word_count=0, success=False, error="toolkit disabled")
        return fetch_page_text(url, max_chars=self.max_fetch_chars)

    def research_queries(
        self,
        queries: list[str],
        *,
        fetch_top_n: int | None = None,
    ) -> ResearchToolResult:
        """
        Run a set of search queries, then fetch the most promising pages.
        Returns an aggregated ResearchToolResult ready to inject into a prompt.
        """
        if not self.enabled:
            return ResearchToolResult()

        all_hits: list[WebSearchHit] = []
        seen_urls: set[str] = set()
        for query in queries:
            for hit in self.search(query):
                if hit.url and hit.url not in seen_urls:
                    all_hits.append(hit)
                    seen_urls.add(hit.url)

        # Deduplicate by URL already done; now prioritise credible domains
        ranked = _rank_hits(all_hits)

        n_fetch = fetch_top_n if fetch_top_n is not None else self.max_fetches_per_section
        to_fetch = [h for h in ranked if _is_fetchable(h.url)][:n_fetch]

        fetched: list[FetchedPage] = []
        for hit in to_fetch:
            page = self.fetch(hit.url)
            fetched.append(page)

        return ResearchToolResult(search_hits=ranked[:self.max_search_results], fetched_pages=fetched)

    # ------------------------------------------------------------------
    # OpenAI-compatible tool schemas (for function-calling)
    # ------------------------------------------------------------------

    def as_langchain_tools(self) -> list[Any]:
        """Return LangChain-compatible tool objects for bind_tools()."""
        from langchain_core.tools import StructuredTool  # type: ignore[import]

        toolkit = self

        def _web_search(query: str) -> str:
            """Search the web for current technical information, papers, engineering blogs, and documentation."""
            hits = toolkit.search(query)
            if not hits:
                return "No results found."
            return "\n".join(
                f"[{i + 1}] {h.title}\nURL: {h.url}\n{h.snippet}"
                for i, h in enumerate(hits)
            )

        def _fetch_url(url: str) -> str:
            """Fetch and read the text content of a URL for detailed information."""
            page = toolkit.fetch(url)
            if not page.success:
                return f"Could not fetch {url}: {page.error}"
            return f"Title: {page.title}\nURL: {url}\n\n{page.text}"

        return [
            StructuredTool.from_function(
                func=_web_search,
                name="web_search",
                description="Search the web for current technical information, papers, engineering blogs, and documentation. Use specific queries.",
            ),
            StructuredTool.from_function(
                func=_fetch_url,
                name="fetch_url",
                description="Fetch and read the text content of a URL. Use this to read full articles, docs, or papers found via web_search.",
            ),
        ]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _domain(url: str) -> str:
    match = re.search(r"https?://(?:www\.)?([^/]+)", url)
    return match.group(1) if match else url


# Priority domains for credible technical sources
_HIGH_CREDIBILITY_DOMAINS = {
    "arxiv.org", "papers.nips.cc", "proceedings.mlr.press",
    "engineering.fb.com", "engineering.atspotify.com", "netflixtechblog.com",
    "openai.com", "anthropic.com", "deepmind.com",
    "uber.com", "airbnb.io", "doordash.engineering", "lyft.engineering",
    "stripe.com/blog", "shopify.engineering", "github.blog",
    "aws.amazon.com/blogs", "cloud.google.com/blog", "azure.microsoft.com/blog",
    "mlops.community", "huggingface.co",
    "eugeneyan.com", "huyenchip.com", "newsletter.pragmaticengineer.com",
}

_LOW_CREDIBILITY_DOMAINS = {
    "medium.com", "towardsdatascience.com", "quora.com", "reddit.com",
    "stackoverflow.com", "wikipedia.org",
}


def _rank_hits(hits: list[WebSearchHit]) -> list[WebSearchHit]:
    """Re-rank search hits, boosting credible technical sources."""
    def _score(hit: WebSearchHit) -> int:
        domain = _domain(hit.url).lower()
        if any(d in domain for d in _HIGH_CREDIBILITY_DOMAINS):
            return 2
        if any(d in domain for d in _LOW_CREDIBILITY_DOMAINS):
            return 0
        return 1

    return sorted(hits, key=lambda h: -_score(h))


def _is_fetchable(url: str) -> bool:
    """Filter out URLs that are unlikely to return useful text content."""
    blocked = (".pdf", ".png", ".jpg", ".gif", ".zip", ".pptx", ".docx")
    lower = url.lower()
    if any(lower.endswith(ext) for ext in blocked):
        return False
    # Skip social/video platforms
    skip_domains = ("youtube.com", "twitter.com", "x.com", "linkedin.com", "facebook.com")
    domain = _domain(lower)
    return not any(skip in domain for skip in skip_domains)
