from blog_series_agent.schemas.evaluation import BlogEvaluation, CriterionScore


def test_blog_evaluation_overall_score() -> None:
    evaluation = BlogEvaluation(
        part_number=1,
        slug="introduction",
        title="Introduction",
        criteria=[
            CriterionScore(name="clarity", score=8, rationale="Strong", recommended_action="Keep clarity high"),
            CriterionScore(name="depth", score=6, rationale="Needs more detail", recommended_action="Expand the systems section"),
        ],
        summary="Blog evaluation summary.",
        skill_adherence_score=7,
    )

    assert evaluation.overall_score == 7.0

