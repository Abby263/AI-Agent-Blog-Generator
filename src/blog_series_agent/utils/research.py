"""Helpers for grounded research evidence extraction and sanitization."""

from __future__ import annotations

import re

from ..schemas.series import SourceNote

_META_PHRASES = (
    "web search evidence could not be retrieved",
    "no external research sources were successfully retrieved",
    "would risk fabrication",
    "leaves practical_references and citation_anchors empty",
    "no credible sources were found",
    "no results found",
)


def count_urls(text: str) -> int:
    """Count HTTP(S) URLs in a string."""
    return len(re.findall(r"https?://\S+", text or ""))


def extract_source_notes_from_evidence(evidence_text: str, limit: int = 8) -> list[SourceNote]:
    """Extract title + URL pairs from grounded evidence text."""
    lines = (evidence_text or "").splitlines()
    notes: list[SourceNote] = []
    seen_urls: set[str] = set()

    for index, line in enumerate(lines):
        stripped = line.strip()
        url_match = re.match(r"URL:\s*(https?://\S+)", stripped)
        if not url_match:
            continue

        url = url_match.group(1).rstrip(").,")
        if url in seen_urls:
            continue

        title = ""
        if index > 0:
            prev = lines[index - 1].strip()
            bracket_match = re.match(r"\[\d+\]\s+(.+)", prev)
            title_match = re.match(r"Title:\s*(.+)", prev)
            if bracket_match:
                title = bracket_match.group(1).strip()
            elif title_match:
                title = title_match.group(1).strip()
            elif prev.startswith("**") and prev.endswith("**"):
                title = prev.strip("*").strip()
            else:
                title = prev

        if not title:
            title = url

        notes.append(
            SourceNote(
                title=title,
                source_type=_infer_source_type(url),
                url=url,
                note="Extracted from grounded evidence gathered during the run.",
                credibility="high" if _looks_credible(url) else "medium",
            )
        )
        seen_urls.add(url)
        if len(notes) >= limit:
            break

    return notes


def sanitize_research_meta(text: str, fallback: str = "") -> str:
    """Remove scaffolding/meta paragraphs about failed retrieval from text."""
    paragraphs = re.split(r"\n\s*\n", text or "")
    kept: list[str] = []
    for paragraph in paragraphs:
        normalized = " ".join(paragraph.lower().split())
        if any(phrase in normalized for phrase in _META_PHRASES):
            continue
        if paragraph.strip():
            kept.append(paragraph.strip())
    return "\n\n".join(kept).strip() or fallback.strip()


def sanitize_supporting_points(points: list[str]) -> list[str]:
    """Remove meta/error bullets from supporting-point lists."""
    cleaned: list[str] = []
    for point in points:
        normalized = " ".join((point or "").lower().split())
        if any(phrase in normalized for phrase in _META_PHRASES):
            continue
        if point and point.strip():
            cleaned.append(point.strip())
    return cleaned


def _looks_credible(url: str) -> bool:
    domain = _domain(url)
    return any(
        token in domain
        for token in (
            ".org",
            ".edu",
            "arxiv.org",
            "tensorflow.org",
            "kubernetes.io",
            "nvidia.com",
            "onnxruntime.ai",
            "github.io",
            "engineering.",
            "docs.",
        )
    )


def _infer_source_type(url: str) -> str:
    domain = _domain(url)
    if "arxiv.org" in domain or "proceedings.mlr.press" in domain or "papers." in domain:
        return "paper"
    if any(token in domain for token in ("docs.", "tensorflow.org", "kubernetes.io", "onnxruntime.ai", "nvidia.com")):
        return "documentation"
    if any(token in domain for token in ("engineering.", "blog", "netflixtechblog", "openai.com")):
        return "engineering_blog"
    return "web"


def _domain(url: str) -> str:
    match = re.search(r"https?://(?:www\.)?([^/]+)", url)
    return match.group(1).lower() if match else url.lower()
