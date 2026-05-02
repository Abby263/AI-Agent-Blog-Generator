from blog_series_agent.schemas.review import ReviewScorecard


def test_review_scorecard_totals() -> None:
    scorecard = ReviewScorecard(
        structure_consistency=8,
        series_alignment=7,
        clarity_of_explanation=8,
        technical_accuracy=9,
        technical_freshness=7,
        depth_and_completeness=8,
        readability_and_tone=8,
        visuals_and_examples=7,
        engagement_and_learning_reinforcement=6,
        practical_relevance=9,
    )

    assert scorecard.total_score == 77
    assert scorecard.consistency_score == 37
    assert scorecard.technical_quality_score == 40

