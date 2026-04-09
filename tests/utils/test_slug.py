from blog_series_agent.utils.slug import slugify, to_part_filename


def test_slug_and_filename_helpers() -> None:
    assert slugify("ML System Design") == "ml-system-design"
    assert to_part_filename(4, "feature-pipelines") == "Part-4-feature-pipelines.md"
    assert to_part_filename(4, "feature-pipelines", suffix="review", extension="json") == (
        "Part-4-feature-pipelines-review.json"
    )

