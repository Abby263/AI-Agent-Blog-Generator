"""Core orchestration service."""

from __future__ import annotations

import logging
from pathlib import Path

from ..agents import (
    AssetPlannerAgent,
    BlogImproverAgent,
    BlogReviewerAgent,
    SeriesArchitectAgent,
    TopicResearchAgent,
)
from ..agents.base import AgentContext
from ..config.settings import AppSettings, SeriesRunConfig
from ..graphs.graph import GraphContext, build_blog_graph, build_outline_graph
from ..models.factory import build_llm_client
from ..schemas.artifacts import ArtifactType, PartStatus, RunManifest, RunStatus
from ..schemas.evaluation import BlogEvaluation, RunEvaluation, SeriesEvaluation
from ..schemas.memory import MemoryUpdateResult, SkillRetrievalQuery, SkillRetrievalResult
from ..schemas.review import BlogReviewReport
from ..schemas.series import BlogSeriesOutline, BlogSeriesPart
from ..services.approval_service import ApprovalService
from ..services.artifact_service import ArtifactService
from ..services.content_lint import ContentLintService
from ..services.deepagent_content_builder import DeepAgentContentBuilder
from ..services.deepagent_profile import DeepAgentProfileLoader
from ..services.evaluation_service import EvaluationService
from ..services.memory_service import MemoryService
from ..services.observability import ObservabilityService
from ..services.research_tools import ResearchToolkit
from ..utils.files import read_json
from ..utils.markdown import normalize_markdown_document
from ..utils.prompts import PromptLoader
from ..utils.slug import slugify

logger = logging.getLogger(__name__)


class PipelineService:
    """Runs outline, blog, review, improvement, evaluation, and memory workflows."""

    def __init__(
        self,
        *,
        settings: AppSettings,
        prompt_loader: PromptLoader,
        artifact_service: ArtifactService,
        approval_service: ApprovalService,
        content_lint_service: ContentLintService,
        evaluation_service: EvaluationService,
        memory_service: MemoryService,
        observability_service: ObservabilityService,
    ) -> None:
        self.settings = settings
        self.prompt_loader = prompt_loader
        self.artifact_service = artifact_service
        self.approval_service = approval_service
        self.content_lint_service = content_lint_service
        self.evaluation_service = evaluation_service
        self.memory_service = memory_service
        self.observability_service = observability_service

    def run_outline(self, config: SeriesRunConfig) -> RunManifest:
        manifest = self.artifact_service.create_run_manifest(config)
        self._start_run(manifest, config, name="outline")
        try:
            llm = build_llm_client(config.model, self.settings)
            graph = build_outline_graph(self._build_graph_context(llm, config), manifest)
            graph.invoke({"config": config})
            self.artifact_service.set_status(manifest, RunStatus.COMPLETED)
            self.observability_service.finish_run_trace(
                run_id=manifest.run_id,
                outputs={"status": "completed", "artifact_count": len(self.artifact_service.load_manifest(manifest.run_id).artifacts)},
            )
            return self.artifact_service.load_manifest(manifest.run_id)
        except Exception as exc:  # pragma: no cover - defensive outer boundary
            self.artifact_service.set_status(manifest, RunStatus.FAILED, error=str(exc))
            self.observability_service.finish_run_trace(run_id=manifest.run_id, error=str(exc))
            raise

    def run_blog(self, config: SeriesRunConfig, part_number: int) -> RunManifest:
        manifest = self.artifact_service.create_run_manifest(config)
        self._start_run(manifest, config, name="blog")
        try:
            llm = build_llm_client(config.model, self.settings)
            graph_context = self._build_graph_context(llm, config)
            outline = self._ensure_outline(config, manifest, graph_context)
            part = self._find_part(outline, part_number)
            graph = build_blog_graph(graph_context, manifest)
            state = graph.invoke(
                {
                    "config": config,
                    "series_outline": outline,
                    "current_part": part,
                    "approval_iteration": 0,
                }
            )
            self._persist_run_evaluation(manifest, [state.get("review_report")], [state.get("approval_record")])
            self._finalize_manifest(manifest)
            fresh_manifest = self.artifact_service.load_manifest(manifest.run_id)
            self.observability_service.finish_run_trace(
                run_id=manifest.run_id,
                outputs={"status": fresh_manifest.status, "part_number": part_number},
            )
            return fresh_manifest
        except Exception as exc:  # pragma: no cover - defensive outer boundary
            self.artifact_service.update_part_status(manifest, part_number, PartStatus.FAILED)
            self.artifact_service.set_status(manifest, RunStatus.FAILED, error=str(exc))
            self.observability_service.finish_run_trace(run_id=manifest.run_id, error=str(exc))
            raise

    def run_series(self, config: SeriesRunConfig) -> RunManifest:
        manifest = self.artifact_service.create_run_manifest(config)
        self._start_run(manifest, config, name="series")
        try:
            llm = build_llm_client(config.model, self.settings)
            graph_context = self._build_graph_context(llm, config)
            outline = self._ensure_outline(config, manifest, graph_context)
            target_parts = config.selected_parts or [part.part_number for part in outline.parts]
            graph = build_blog_graph(graph_context, manifest)
            blog_evaluations: list[BlogEvaluation] = []
            review_reports: list[BlogReviewReport] = []
            approvals = []
            for part_number in target_parts:
                # Skip parts that already have a final or approved artifact
                if self._part_already_complete(part_number, outline):
                    logger.info("Skipping part %d: already complete from a previous run.", part_number)
                    continue
                part = self._find_part(outline, part_number)
                state = graph.invoke(
                    {
                        "config": config,
                        "series_outline": outline,
                        "current_part": part,
                        "approval_iteration": 0,
                        "length_expansion_iteration": 0,
                    }
                )
                if state.get("blog_evaluation") is not None:
                    blog_evaluations.append(state["blog_evaluation"])
                if state.get("review_report") is not None:
                    review_reports.append(state["review_report"])
                if state.get("approval_record") is not None:
                    approvals.append(state["approval_record"])
            if config.enable_evaluation and blog_evaluations:
                self.evaluation_service.evaluate_series(manifest=manifest, outline=outline, blog_evaluations=blog_evaluations)
            self._persist_run_evaluation(manifest, review_reports, approvals)
            self._finalize_manifest(manifest)
            fresh_manifest = self.artifact_service.load_manifest(manifest.run_id)
            self.observability_service.finish_run_trace(
                run_id=manifest.run_id,
                outputs={"status": fresh_manifest.status, "parts_completed": len(target_parts)},
            )
            return fresh_manifest
        except Exception as exc:  # pragma: no cover - defensive outer boundary
            self.artifact_service.set_status(manifest, RunStatus.FAILED, error=str(exc))
            self.observability_service.finish_run_trace(run_id=manifest.run_id, error=str(exc))
            raise

    def resume_series(self, run_id: str, config: SeriesRunConfig) -> RunManifest:
        """Resume a previously failed or partially completed run."""
        existing_manifest = self.artifact_service.load_manifest(run_id)
        if existing_manifest.status == RunStatus.COMPLETED:
            logger.info("Run %s is already completed.", run_id)
            return existing_manifest

        manifest = existing_manifest
        self.artifact_service.set_status(manifest, RunStatus.RUNNING)
        self._start_run(manifest, config, name="resume_series")
        try:
            llm = build_llm_client(config.model, self.settings)
            graph_context = self._build_graph_context(llm, config)
            outline = self._ensure_outline(config, manifest, graph_context)
            target_parts = config.selected_parts or [part.part_number for part in outline.parts]
            graph = build_blog_graph(graph_context, manifest)

            # Determine which parts need work
            completed_statuses = {PartStatus.APPROVED, PartStatus.IMPROVED, PartStatus.ASSET_PLANNED}
            remaining_parts = [
                pn for pn in target_parts
                if manifest.part_statuses.get(pn) not in completed_statuses
            ]

            blog_evaluations: list[BlogEvaluation] = []
            review_reports: list[BlogReviewReport] = []
            approvals = []
            for part_number in remaining_parts:
                part = self._find_part(outline, part_number)
                state = graph.invoke(
                    {
                        "config": config,
                        "series_outline": outline,
                        "current_part": part,
                        "approval_iteration": 0,
                        "length_expansion_iteration": 0,
                    }
                )
                if state.get("blog_evaluation") is not None:
                    blog_evaluations.append(state["blog_evaluation"])
                if state.get("review_report") is not None:
                    review_reports.append(state["review_report"])
                if state.get("approval_record") is not None:
                    approvals.append(state["approval_record"])

            if config.enable_evaluation and blog_evaluations:
                self.evaluation_service.evaluate_series(manifest=manifest, outline=outline, blog_evaluations=blog_evaluations)
            self._persist_run_evaluation(manifest, review_reports, approvals)
            self._finalize_manifest(manifest)
            fresh_manifest = self.artifact_service.load_manifest(manifest.run_id)
            self.observability_service.finish_run_trace(
                run_id=manifest.run_id,
                outputs={"status": fresh_manifest.status, "parts_resumed": len(remaining_parts)},
            )
            return fresh_manifest
        except Exception as exc:  # pragma: no cover
            self.artifact_service.set_status(manifest, RunStatus.FAILED, error=str(exc))
            self.observability_service.finish_run_trace(run_id=manifest.run_id, error=str(exc))
            raise

    def review_existing(self, draft_path: str | Path) -> RunManifest:
        path = Path(draft_path)
        part_number, slug = self.approval_service.parse_part_id(path.stem)
        config = SeriesRunConfig(
            topic=slug.replace("-", " ").title(),
            audience="intermediate",
            num_parts=max(part_number, 1),
            model=self.settings.default_model_config(),
            output_dir=self.settings.blog_series_output_dir,
            **self.settings.default_run_overrides(),
        )
        manifest = self.artifact_service.create_run_manifest(config)
        self._start_run(manifest, config, name="review_existing")
        llm = build_llm_client(config.model, self.settings)
        context = AgentContext(llm=llm, prompts=self.prompt_loader)
        part = BlogSeriesPart(
            part_number=part_number,
            title=slug.replace("-", " ").title(),
            slug=slug,
            purpose="Review an existing draft.",
            prerequisite_context=[],
            key_concepts=[],
            recommended_diagrams=[],
        )
        reviewer = BlogReviewerAgent(context)
        draft_markdown = normalize_markdown_document(path.read_text(encoding="utf-8"))
        lint_report = self.content_lint_service.lint_markdown(draft_markdown, config)
        report = reviewer.run(
            config,
            part,
            draft_markdown,
            self._empty_retrieval(config, part_number, "review"),
            self.content_lint_service.lint_summary(lint_report),
        )
        report = self.content_lint_service.enrich_review_report(report, lint_report, [], config)
        self.artifact_service.write_json_artifact(
            manifest=manifest,
            artifact_type=ArtifactType.REVIEW,
            folder="reviews",
            filename=f"{path.stem}-review.json",
            payload=report.model_dump(mode="json"),
            part_number=part_number,
        )
        self.artifact_service.set_status(manifest, RunStatus.COMPLETED)
        self.observability_service.finish_run_trace(run_id=manifest.run_id, outputs={"status": "completed"})
        return self.artifact_service.load_manifest(manifest.run_id)

    def improve_existing(self, draft_path: str | Path, review_path: str | Path) -> RunManifest:
        draft = Path(draft_path)
        review = Path(review_path)
        part_number, slug = self.approval_service.parse_part_id(draft.stem)
        config = SeriesRunConfig(
            topic=slug.replace("-", " ").title(),
            audience="intermediate",
            num_parts=max(part_number, 1),
            model=self.settings.default_model_config(),
            output_dir=self.settings.blog_series_output_dir,
            **self.settings.default_run_overrides(),
        )
        manifest = self.artifact_service.create_run_manifest(config)
        self._start_run(manifest, config, name="improve_existing")
        llm = build_llm_client(config.model, self.settings)
        context = AgentContext(llm=llm, prompts=self.prompt_loader)
        part = BlogSeriesPart(
            part_number=part_number,
            title=slug.replace("-", " ").title(),
            slug=slug,
            purpose="Improve an existing draft.",
            prerequisite_context=[],
            key_concepts=[],
            recommended_diagrams=[],
        )
        improver = BlogImproverAgent(context)
        review_report = BlogReviewReport.model_validate(read_json(review))
        draft_markdown = normalize_markdown_document(draft.read_text(encoding="utf-8"))
        lint_report = self.content_lint_service.lint_markdown(draft_markdown, config)
        final_markdown = improver.run(
            config,
            part,
            draft_markdown,
            review_report,
            self._empty_retrieval(config, part_number, "final"),
            self.content_lint_service.lint_summary(lint_report),
        )
        final_markdown = normalize_markdown_document(final_markdown)
        if not final_markdown.strip():
            final_markdown = draft_markdown
        self.artifact_service.write_markdown_artifact(
            manifest=manifest,
            artifact_type=ArtifactType.FINAL,
            folder="final",
            filename=f"{draft.stem}.md",
            content=final_markdown,
            part_number=part_number,
        )
        self.artifact_service.set_status(manifest, RunStatus.COMPLETED)
        self.observability_service.finish_run_trace(run_id=manifest.run_id, outputs={"status": "completed"})
        return self.artifact_service.load_manifest(manifest.run_id)

    def evaluate_part(self, part_id: str) -> BlogEvaluation:
        part_number, slug = self.approval_service.parse_part_id(part_id)
        review_path = self.artifact_service.path_for_part("reviews", part_number, slug, suffix="review", extension="json")
        if not review_path.exists():
            raise FileNotFoundError(f"Review artifact not found for {part_id}")
        final_path = self.artifact_service.path_for_part("final", part_number, slug)
        draft_path = self.artifact_service.path_for_part("drafts", part_number, slug)
        article_path = final_path if final_path.exists() else draft_path
        if not article_path.exists():
            raise FileNotFoundError(f"Draft/final artifact not found for {part_id}")
        config = SeriesRunConfig(
            topic=slug.replace("-", " ").title(),
            audience="intermediate",
            num_parts=max(part_number, 1),
            model=self.settings.default_model_config(),
            output_dir=self.settings.blog_series_output_dir,
            **self.settings.default_run_overrides(),
        )
        manifest = self.artifact_service.create_run_manifest(config)
        review_report = BlogReviewReport.model_validate(read_json(review_path))
        final_markdown = normalize_markdown_document(article_path.read_text(encoding="utf-8"))
        lint_report = self.content_lint_service.lint_markdown(final_markdown, config)
        return self.evaluation_service.evaluate_blog(
            manifest=manifest,
            config=config,
            review_report=review_report,
            final_markdown=final_markdown,
            lint_report=lint_report,
            active_skill_ids=self.memory_service.retrieve_skills(
                SkillRetrievalQuery(
                    topic=config.topic,
                    audience=config.target_audience,
                    part_number=part_number,
                    artifact_type="evaluation",
                    max_skills=config.max_retrieved_skills,
                ),
                record_usage=False,
            ).retrieved_skill_ids,
        )

    def evaluate_series_latest(self) -> SeriesEvaluation:
        outline_path = self.artifact_service.path_for_outline("json")
        if not outline_path.exists():
            raise FileNotFoundError("Series outline not found.")
        outline = BlogSeriesOutline.model_validate(read_json(outline_path))
        blog_evaluations = [
            BlogEvaluation.model_validate(read_json(path))
            for path in sorted((self.artifact_service.output_dir / "evaluations" / "blog").glob("Part-*-eval.json"))
        ]
        if not blog_evaluations:
            raise FileNotFoundError("No blog evaluations available to aggregate.")
        config = SeriesRunConfig(
            topic=outline.topic,
            audience=outline.target_audience,
            num_parts=len(outline.parts),
            model=self.settings.default_model_config(),
            output_dir=self.settings.blog_series_output_dir,
            **self.settings.default_run_overrides(),
        )
        manifest = self.artifact_service.create_run_manifest(config)
        return self.evaluation_service.evaluate_series(manifest=manifest, outline=outline, blog_evaluations=blog_evaluations)

    def get_blog_evaluation(self, part_id: str) -> BlogEvaluation | None:
        return self.evaluation_service.load_blog_evaluation(part_id)

    def get_latest_series_evaluation(self) -> SeriesEvaluation | None:
        return self.evaluation_service.latest_series_evaluation()

    def build_memory(self, *, topic: str, audience: str) -> MemoryUpdateResult:
        config = SeriesRunConfig(
            topic=topic,
            audience=audience,
            num_parts=1,
            model=self.settings.default_model_config(),
            output_dir=self.settings.blog_series_output_dir,
            **self.settings.default_run_overrides(),
        )
        return self.memory_service.build_candidate_skills(topic=topic, audience=audience, config=config)

    def preview_memory_retrieval(
        self,
        *,
        topic: str,
        audience: str,
        part_number: int | None = None,
        artifact_type: str = "draft",
    ) -> SkillRetrievalResult:
        return self.memory_service.retrieve_skills(
            SkillRetrievalQuery(
                topic=topic,
                audience=audience,
                part_number=part_number,
                artifact_type=artifact_type,
                max_skills=self.settings.blog_series_max_retrieved_skills,
            ),
            record_usage=False,
        )

    def _build_graph_context(self, llm, config: SeriesRunConfig | None = None) -> GraphContext:
        toolkit: ResearchToolkit | None = None
        if config and getattr(config, "enable_web_search", False):
            toolkit = ResearchToolkit(
                max_search_results=getattr(config, "web_search_max_results", 6),
                max_fetch_chars=getattr(config, "web_fetch_max_chars", 5000),
                max_fetches_per_section=getattr(config, "web_max_fetches_per_section", 3),
                enabled=True,
            )
            logger.info("Research toolkit enabled (web search + URL fetch).")
        deepagent_profile = DeepAgentProfileLoader().load()
        deepagent_content_builder = DeepAgentContentBuilder(
            llm=llm,
            profile=deepagent_profile,
            research_toolkit=toolkit,
        )
        agent_context = AgentContext(
            llm=llm,
            prompts=self.prompt_loader,
            research_toolkit=toolkit,
            deepagent_profile=deepagent_profile,
        )
        return GraphContext(
            artifact_service=self.artifact_service,
            approval_service=self.approval_service,
            content_lint_service=self.content_lint_service,
            evaluation_service=self.evaluation_service,
            memory_service=self.memory_service,
            observability_service=self.observability_service,
            deepagent_content_builder=deepagent_content_builder,
            topic_research_agent=TopicResearchAgent(agent_context),
            series_architect_agent=SeriesArchitectAgent(agent_context),
            blog_reviewer_agent=BlogReviewerAgent(agent_context),
            blog_improver_agent=BlogImproverAgent(agent_context),
            asset_planner_agent=AssetPlannerAgent(agent_context),
        )

    def _ensure_outline(
        self,
        config: SeriesRunConfig,
        manifest: RunManifest,
        graph_context: GraphContext,
    ) -> BlogSeriesOutline:
        outline_path = self.artifact_service.path_for_outline("json")
        if outline_path.exists():
            existing = BlogSeriesOutline.model_validate(read_json(outline_path))
            if (
                existing.topic == config.topic
                and existing.target_audience == config.target_audience
                and len(existing.parts) == config.num_parts
            ):
                return existing
        graph = build_outline_graph(graph_context, manifest)
        state = graph.invoke({"config": config})
        return state["series_outline"]

    @staticmethod
    def _find_part(outline: BlogSeriesOutline, part_number: int) -> BlogSeriesPart:
        for part in outline.parts:
            if part.part_number == part_number:
                if not part.slug:
                    part.slug = slugify(part.title)
                return part
        raise ValueError(f"Part {part_number} not found in outline")

    def _start_run(self, manifest: RunManifest, config: SeriesRunConfig, *, name: str) -> None:
        self.observability_service.configure_for_run(config)
        self.artifact_service.set_status(manifest, RunStatus.RUNNING)
        self.observability_service.start_run_trace(
            run_id=manifest.run_id,
            name=name,
            metadata={
                "topic": config.topic,
                "num_parts": config.num_parts,
                "run_mode": config.run_mode.value,
                "builder": "deepagents",
                "use_memory": config.use_memory,
                "enable_evaluation": config.enable_evaluation,
            },
            inputs={"topic": config.topic, "selected_parts": config.selected_parts},
        )

    def _persist_run_evaluation(
        self,
        manifest: RunManifest,
        review_reports: list[BlogReviewReport | None],
        approvals: list[object],
    ) -> RunEvaluation:
        clean_reviews = [report for report in review_reports if report is not None]
        clean_approvals = [record for record in approvals if record is not None]
        return self.evaluation_service.evaluate_run(
            manifest=manifest,
            review_reports=clean_reviews,
            approvals=clean_approvals,
        )

    def _finalize_manifest(self, manifest: RunManifest) -> None:
        fresh_manifest = self.artifact_service.load_manifest(manifest.run_id)
        if any(status == PartStatus.WAITING_FOR_APPROVAL for status in fresh_manifest.part_statuses.values()):
            self.artifact_service.set_status(fresh_manifest, RunStatus.WAITING_FOR_APPROVAL)
        elif any(status == PartStatus.REJECTED for status in fresh_manifest.part_statuses.values()):
            self.artifact_service.set_status(fresh_manifest, RunStatus.REJECTED)
        else:
            self.artifact_service.set_status(fresh_manifest, RunStatus.COMPLETED)

    def _part_already_complete(self, part_number: int, outline: BlogSeriesOutline) -> bool:
        """Check if a part already has a final or approved artifact from a previous run."""
        part = self._find_part(outline, part_number)
        final_path = self.artifact_service.path_for_part("final", part_number, part.slug)
        if final_path.exists():
            return True
        approval_path = self.artifact_service.path_for_part(
            "approval", part_number, part.slug, suffix="approval", extension="json"
        )
        if approval_path.exists():
            from ..schemas.approval import ApprovalDecision
            record = self.approval_service.load(part_number, part.slug)
            if record and record.status in {ApprovalDecision.APPROVED, ApprovalDecision.APPROVED_WITH_NOTES}:
                return True
        return False

    @staticmethod
    def _empty_retrieval(config: SeriesRunConfig, part_number: int, artifact_type: str) -> SkillRetrievalResult:
        query = SkillRetrievalQuery(
            topic=config.topic,
            audience=config.target_audience,
            part_number=part_number,
            artifact_type=artifact_type,
            max_skills=config.max_retrieved_skills,
        )
        return SkillRetrievalResult(query=query, retrieved_skill_ids=[], retrieved_guidance=[], retrieval_notes=[])
