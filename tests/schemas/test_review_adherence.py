from blog_series_agent.schemas.review import BlogReviewReport, ReviewRecommendation, ReviewScorecard


def test_review_skill_adherence_fields_parse() -> None:
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
            depth_and_completeness=8,
            readability_and_tone=8,
            visuals_and_examples=8,
            engagement_and_learning_reinforcement=8,
            practical_relevance=8,
        ),
        strengths=["Clear opening"],
        issues=["Missed one active skill."],
        priority_fixes=["Add the required synthesis paragraph."],
        suggested_additions=["Add one architecture diagram."],
        final_recommendation=ReviewRecommendation.REVISE,
        summary="Solid draft with one skill adherence issue.",
        active_skills_checked=["skill-intro", "skill-synthesis"],
        skills_followed=["skill-intro"],
        skills_violated=["skill-synthesis"],
        skill_adherence_score=6,
        skill_adherence_notes=["The post followed the intro framing skill but missed the synthesis guidance."],
    )

    assert report.skill_adherence_score == 6
    assert report.skills_violated == ["skill-synthesis"]

