from pathlib import Path

from blog_series_agent.config.settings import RunMode, SeriesRunConfig
from blog_series_agent.schemas.memory import FeedbackSeverity, FeedbackType, SkillRetrievalQuery
from blog_series_agent.services.memory_service import MemoryService


def test_memory_service_feedback_and_skill_lifecycle(tmp_path: Path) -> None:
    service = MemoryService(tmp_path)
    service.capture_manual_feedback(
        source_artifact="Part-1-introduction",
        raw_feedback="The introduction needs a clearer real-world problem.",
        normalized_issue_type=FeedbackType.CLARITY_ISSUE,
        severity=FeedbackSeverity.MEDIUM,
        suggested_fix="Open with a concrete problem before definitions.",
        reviewer="alice",
        part_number=1,
        blog_slug="introduction",
    )
    service.capture_manual_feedback(
        source_artifact="Part-2-requirements",
        raw_feedback="The introduction needs a clearer real-world problem.",
        normalized_issue_type=FeedbackType.CLARITY_ISSUE,
        severity=FeedbackSeverity.MEDIUM,
        suggested_fix="Open with a concrete problem before definitions.",
        reviewer="bob",
        part_number=2,
        blog_slug="requirements",
    )
    service.capture_manual_feedback(
        source_artifact="Part-3-data-pipelines",
        raw_feedback="The introduction needs a clearer real-world problem.",
        normalized_issue_type=FeedbackType.CLARITY_ISSUE,
        severity=FeedbackSeverity.MEDIUM,
        suggested_fix="Open with a concrete problem before definitions.",
        reviewer="carol",
        part_number=3,
        blog_slug="data-pipelines",
    )

    result = service.build_candidate_skills(
        topic="ML System Design",
        audience="intermediate",
        config=SeriesRunConfig(
            topic="ML System Design",
            audience="intermediate",
            num_parts=12,
            run_mode=RunMode.REVIEW,
            approval_required=True,
        ),
    )

    assert len(result.candidate_skills_created) == 1
    approved = service.approve_skill(result.candidate_skills_created[0].id)
    retrieval = service.retrieve_skills(
        SkillRetrievalQuery(
            topic="ML System Design",
            audience="intermediate",
            part_number=1,
            artifact_type="draft",
            max_skills=3,
        ),
        record_usage=False,
    )

    assert approved.active is True
    assert retrieval.retrieved_skill_ids == [approved.id]
    assert "problem" in approved.guidance_text.lower()
    assert "before formal definitions" in approved.guidance_text.lower()
    assert (tmp_path / "approved_skills.md").exists()
    assert (tmp_path / "raw_feedback_log.md").exists()


def test_memory_service_generalizes_visual_feedback_into_reusable_skill(tmp_path: Path) -> None:
    service = MemoryService(tmp_path)
    for reviewer in ("alice", "bob", "carol"):
        service.capture_manual_feedback(
            source_artifact="Part-6-deployment-strategies",
            raw_feedback="Do not leave placeholder captions or example.com image links in architecture sections.",
            normalized_issue_type=FeedbackType.VISUAL_ISSUE,
            severity=FeedbackSeverity.HIGH,
            suggested_fix="Replace fake image links with explicit visual specs.",
            reviewer=reviewer,
            part_number=6,
            blog_slug="deployment-strategies",
        )

    result = service.build_candidate_skills(
        topic="ML System Design",
        audience="intermediate",
        config=SeriesRunConfig(topic="ML System Design", audience="intermediate", num_parts=12, run_mode=RunMode.REVIEW),
    )

    assert len(result.candidate_skills_created) == 1
    skill = result.candidate_skills_created[0]
    assert skill.title == "Use purposeful visuals instead of placeholders"
    assert "never leave placeholder image urls" in skill.guidance_text.lower()
