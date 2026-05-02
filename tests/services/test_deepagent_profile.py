from pathlib import Path

from blog_series_agent.services.deepagent_profile import DeepAgentProfileLoader


def test_deepagent_profile_loads_memory_skills_and_subagents() -> None:
    profile = DeepAgentProfileLoader(Path("src/blog_series_agent/deepagent")).load()

    assert "technical content-building agent" in profile.memory
    assert "section_researcher" in profile.subagents
    assert {skill.name for skill in profile.skills} >= {
        "artifact-contract",
        "blog-series",
        "qa-review-gate",
        "section-grounding",
        "visuals-and-code",
    }


def test_deepagent_profile_renders_stage_guidance() -> None:
    profile = DeepAgentProfileLoader(Path("src/blog_series_agent/deepagent")).load()

    guidance = profile.guidance_for(stage="research", subagent_name="section_researcher")

    assert "Agent Memory" in guidance
    assert "Subagent Role: section_researcher" in guidance
    assert "section-grounding" in guidance
    assert "visuals-and-code" in guidance
