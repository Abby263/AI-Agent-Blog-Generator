from blog_series_agent.utils.markdown import normalize_markdown_document


def test_normalize_markdown_document_strips_outer_fence() -> None:
    markdown = "```markdown\n# Title\n\nBody\n```"
    assert normalize_markdown_document(markdown) == "# Title\n\nBody"
