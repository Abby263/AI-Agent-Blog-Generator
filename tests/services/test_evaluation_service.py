from pathlib import Path

from blog_series_agent.config.settings import SeriesRunConfig
from blog_series_agent.schemas.artifacts import RunManifest
from blog_series_agent.schemas.evaluation import ContentLintFinding, ContentLintReport, EvaluationSeverity
from blog_series_agent.schemas.review import BlogReviewReport, ReviewRecommendation, ReviewScorecard
from blog_series_agent.services.artifact_service import ArtifactService
from blog_series_agent.services.evaluation_service import EvaluationService


def test_evaluation_service_persists_blog_evaluation(tmp_path: Path) -> None:
    artifact_service = ArtifactService(tmp_path)
    evaluation_service = EvaluationService(artifact_service)
    manifest = RunManifest(run_id="run-1", topic="AI Agents", target_audience="intermediate", num_parts=4)
    config = SeriesRunConfig(topic="AI Agents", audience="intermediate", num_parts=4)
    report = BlogReviewReport(
        part_number=1,
        slug="introduction",
        title="Introduction",
        scorecard=ReviewScorecard(
            structure_consistency=8,
            series_alignment=8,
            clarity_of_explanation=8,
            technical_accuracy=8,
            technical_freshness=8,
            depth_and_completeness=7,
            readability_and_tone=8,
            visuals_and_examples=7,
            engagement_and_learning_reinforcement=7,
            practical_relevance=8,
        ),
        strengths=["Strong opening"],
        issues=["Needs one more practical example."],
        priority_fixes=["Add a concrete production example."],
        suggested_additions=["Include an evaluation diagram."],
        final_recommendation=ReviewRecommendation.REVISE,
        summary="Good draft with one notable gap.",
        active_skills_checked=["skill-intro"],
        skills_followed=["skill-intro"],
        skill_adherence_score=8,
    )

    evaluation = evaluation_service.evaluate_blog(
        manifest=manifest,
        config=config,
        review_report=report,
        final_markdown="# Title\n\nBody",
        lint_report=ContentLintReport(
            word_count=2,
            findings=[
                ContentLintFinding(
                    finding_type="under_target_length",
                    severity=EvaluationSeverity.HIGH,
                    message="Too short",
                    recommended_action="Expand it.",
                )
            ],
        ),
        active_skill_ids=["skill-intro"],
    )

    assert evaluation.overall_score > 0
    assert any(issue.issue_type == "under_target_length" for issue in evaluation.issues)
    assert (tmp_path / "evaluations" / "blog" / "Part-1-introduction-eval.json").exists()
