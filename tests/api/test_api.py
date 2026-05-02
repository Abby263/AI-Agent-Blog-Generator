from fastapi.testclient import TestClient

from blog_series_agent.api.app import app
from blog_series_agent.api.dependencies import get_application_services, get_pipeline_service
from blog_series_agent.schemas.artifacts import RunManifest, RunStatus
from blog_series_agent.schemas.evaluation import BlogEvaluation, CriterionScore, SeriesEvaluation
from blog_series_agent.schemas.memory import FeedbackItem, FeedbackSeverity, FeedbackSourceType, FeedbackType, ReusableSkill


class FakeArtifactService:
    def __init__(self) -> None:
        self.manifest = RunManifest(run_id="run-123", topic="AI Agents", target_audience="intermediate", num_parts=4)

    def create_run_manifest(self, config):  # noqa: ANN001
        return self.manifest

    def set_status(self, manifest, status, error=None):  # noqa: ANN001
        manifest.status = status

    def load_manifest(self, run_id: str):  # noqa: ARG002
        self.manifest.status = RunStatus.COMPLETED
        return self.manifest

    def artifacts_for_part(self, part_id: str):  # noqa: ARG002
        return []

    def list_manifests(self):
        return [self.manifest]

    def latest_outline_path(self):
        return None


class FakeApprovalService:
    def parse_part_id(self, part_id: str):  # noqa: ARG002
        return 1, "introduction"

    def load(self, part_number: int, slug: str):  # noqa: ARG002
        return None

    def submit_approval(self, **kwargs):  # noqa: ANN003
        return None


class FakeEvaluationService:
    def latest_series_evaluation(self):
        return SeriesEvaluation(
            topic="AI Agents",
            criteria=[CriterionScore(name="progression_quality", score=8, rationale="Strong", recommended_action="Keep going")],
            summary="Series evaluation summary.",
        )

    def load_blog_evaluation(self, part_id: str):  # noqa: ARG002
        return BlogEvaluation(
            part_number=1,
            slug="introduction",
            title="Introduction",
            criteria=[CriterionScore(name="clarity", score=8, rationale="Good", recommended_action="Maintain clarity")],
            summary="Blog evaluation summary.",
            skill_adherence_score=8,
        )


class FakeMemoryService:
    def list_feedback(self):
        return [
            FeedbackItem(
                feedback_id="fb-1",
                source_type=FeedbackSourceType.USER,
                source_artifact="Part-1-introduction",
                raw_feedback="Clarify the opening.",
                normalized_issue_type=FeedbackType.CLARITY_ISSUE,
                severity=FeedbackSeverity.MEDIUM,
                suggested_fix="Lead with a clearer problem statement.",
                reviewer="alice",
            )
        ]

    def list_candidate_skills(self):
        return []

    def list_approved_skills(self):
        return [
            ReusableSkill(
                id="skill-intro",
                title="Introduction framing",
                category="clarity_issue",
                guidance_text="Begin with a concrete problem before definitions.",
                confidence_score=0.8,
                status="approved",
                active=True,
            )
        ]

    def capture_manual_feedback(self, **kwargs):  # noqa: ANN003
        return self.list_feedback()[0]

    def capture_approval_feedback(self, **kwargs):  # noqa: ANN003
        return []

    def approve_skill(self, skill_id: str):  # noqa: ARG002
        return self.list_approved_skills()[0]

    def reject_skill(self, skill_id: str):  # noqa: ARG002
        return self.list_approved_skills()[0].model_copy(update={"status": "rejected", "active": False})

    def retrieve_skills(self, query, record_usage=False):  # noqa: ANN001, ARG002
        from blog_series_agent.schemas.memory import SkillRetrievalResult

        return SkillRetrievalResult(
            query=query,
            retrieved_skill_ids=["skill-intro"],
            retrieved_guidance=["[skill-intro] Begin with a concrete problem before definitions."],
            retrieval_notes=["Introduction framing"],
        )


class FakePipelineService:
    def __init__(self) -> None:
        self.artifact_service = FakeArtifactService()

    def run_outline(self, config):  # noqa: ANN001, ARG002
        return self.artifact_service.manifest

    def run_series(self, config):  # noqa: ANN001, ARG002
        return self.artifact_service.manifest

    def run_blog(self, config, part):  # noqa: ANN001, ARG002
        return self.artifact_service.manifest

    def review_existing(self, path):  # noqa: ANN001, ARG002
        return self.artifact_service.manifest

    def improve_existing(self, draft, review):  # noqa: ANN001, ARG002
        return self.artifact_service.manifest

    def evaluate_part(self, part_id: str):  # noqa: ARG002
        return FakeEvaluationService().load_blog_evaluation(part_id)

    def evaluate_series_latest(self):
        return FakeEvaluationService().latest_series_evaluation()

    def build_memory(self, *, topic: str, audience: str):  # noqa: ARG002
        from blog_series_agent.schemas.memory import MemoryUpdateResult

        return MemoryUpdateResult(candidate_skills_created=[])


def test_api_smoke() -> None:
    app.dependency_overrides[get_pipeline_service] = lambda: FakePipelineService()
    app.dependency_overrides[get_application_services] = lambda: {
        "artifact_service": FakeArtifactService(),
        "approval_service": FakeApprovalService(),
        "evaluation_service": FakeEvaluationService(),
        "memory_service": FakeMemoryService(),
    }
    client = TestClient(app)

    response = client.get("/series/latest")
    assert response.status_code == 200
    assert response.json()["latest_manifest"]["run_id"] == "run-123"

    feedback = client.get("/feedback")
    assert feedback.status_code == 200
    assert feedback.json()["feedback"][0]["feedback_id"] == "fb-1"

    skills = client.get("/memory/skills")
    assert skills.status_code == 200
    assert skills.json()["approved_skills"][0]["id"] == "skill-intro"

    preview = client.get("/memory/retrieval-preview", params={"topic": "AI Agents"})
    assert preview.status_code == 200
    assert preview.json()["retrieval"]["retrieved_skill_ids"] == ["skill-intro"]

    app.dependency_overrides.clear()
