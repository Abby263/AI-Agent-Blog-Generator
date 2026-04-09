from blog_series_agent.agents.blog_outline import BlogOutlineAgent
from blog_series_agent.schemas.series import BlogChapterPlan, BlogSectionPlan


def test_blog_outline_normalization_adds_missing_mandatory_sections() -> None:
    plan = BlogChapterPlan(
        part_number=1,
        slug="intro",
        title="Intro",
        subtitle="Sub",
        chapter_summary="Summary",
        section_plans=[
            BlogSectionPlan(heading="Introduction", purpose="Open strongly."),
            BlogSectionPlan(heading="Conclusion", purpose="Close strongly."),
        ],
    )

    normalized = BlogOutlineAgent._normalize_plan(plan)

    headings = [section.heading for section in normalized.section_plans]
    assert "References" in headings
    assert headings[0] == "Introduction"
    assert headings[-1] == "References"
