from blog_series_agent.config.settings import SeriesRunConfig
from blog_series_agent.schemas.review import BlogReviewReport, ReviewRecommendation, ReviewScorecard
from blog_series_agent.services.content_lint import ContentLintService


def test_content_lint_detects_underlength_and_placeholder_visuals() -> None:
    service = ContentLintService()
    config = SeriesRunConfig(topic="ML System Design", audience="intermediate", num_parts=12, min_word_count=1800)
    markdown = "\n".join(
        [
            "# Title",
            "## Introduction",
            "Short body.",
            "![Architecture](https://example.com/arch.png)",
            "## References",
            "- Building Machine Learning Powered Applications",
        ]
    )

    report = service.lint_markdown(markdown, config)

    assert report.word_count < config.min_word_count
    assert "example.com" in report.placeholder_visuals
    assert any(finding.finding_type == "under_target_length" for finding in report.findings)
    assert any(finding.finding_type == "weak_references" for finding in report.findings)


def test_content_lint_accepts_real_images_with_credit_and_valid_code() -> None:
    service = ContentLintService()
    config = SeriesRunConfig(topic="ML System Design", audience="intermediate", num_parts=12, min_word_count=10)
    markdown = "\n".join(
        [
            "# Title",
            "### Posts in this Series",
            "- Part 1",
            "### Table of Contents",
            "1. Detailed Core Sections",
            "## Detailed Core Sections",
            "Substantive body text with implementation detail.",
            "![Observability Architecture](https://images.example.org/arch.png)",
            "_Image credit: [Example Engineering](https://example.org/post)_",
            "```python",
            "def is_drift(score: float, threshold: float = 0.2) -> bool:",
            "    return score > threshold",
            "```",
            "#### Sources for This Section",
            "- [Example Engineering Post](https://example.org/post)",
            "## References",
            "- [Example Engineering Post](https://example.org/post)",
            "- [Hidden Technical Debt in Machine Learning Systems](https://research.google/pubs/pub43146/)",
            "- [Amazon SageMaker Model Monitor](https://docs.aws.amazon.com/sagemaker/latest/dg/model-monitor.html)",
        ]
    )

    report = service.validate_final_artifact(markdown, config)

    assert not any(f.finding_type == "missing_image_credits" for f in report.findings)
    assert not any(f.finding_type == "code_example_issues" for f in report.findings)


def test_content_lint_enriches_review_scores() -> None:
    service = ContentLintService()
    config = SeriesRunConfig(topic="ML System Design", audience="intermediate", num_parts=12, min_word_count=1800)
    report = BlogReviewReport(
        part_number=1,
        slug="intro",
        title="Intro",
        scorecard=ReviewScorecard(
            structure_consistency=8,
            series_alignment=8,
            clarity_of_explanation=8,
            technical_accuracy=8,
            technical_freshness=8,
            depth_and_completeness=8,
            readability_and_tone=8,
            visuals_and_examples=8,
            engagement_and_learning_reinforcement=8,
            practical_relevance=8,
        ),
        strengths=["Good structure"],
        issues=[],
        priority_fixes=[],
        suggested_additions=[],
        final_recommendation=ReviewRecommendation.REVISE,
        summary="Needs work.",
    )
    lint_report = service.lint_markdown("## Introduction\nShort text.\n## References\n- Book", config)

    enriched = service.enrich_review_report(report, lint_report, [], config)

    assert enriched.scorecard.depth_and_completeness < 8
    assert any(item.startswith("[Lint]") for item in enriched.issues)
