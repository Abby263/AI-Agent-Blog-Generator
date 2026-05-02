from pathlib import Path

from blog_series_agent.utils.prompts import PromptLoader


def test_prompt_loader_renders_template() -> None:
    loader = PromptLoader(Path("src/blog_series_agent/prompts"))
    rendered = loader.render("topic_research", topic="AI Agents", audience="advanced", num_parts=10)

    assert "AI Agents" in rendered
    assert "advanced" in rendered
    assert "10" in rendered

