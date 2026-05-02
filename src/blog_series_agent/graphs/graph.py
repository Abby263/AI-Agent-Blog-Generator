"""LangGraph builders for outline and blog workflows."""

from __future__ import annotations

from dataclasses import dataclass

try:
    from langgraph.graph import END, START, StateGraph
except ImportError:  # pragma: no cover - handled at runtime when graph execution is requested
    END = "__end__"
    START = "__start__"
    StateGraph = None

from ..agents import (
    AssetPlannerAgent,
    BlogImproverAgent,
    BlogReviewerAgent,
    SeriesArchitectAgent,
    TopicResearchAgent,
)
from ..schemas.approval import ApprovalDecision
from ..schemas.artifacts import ArtifactType, PartStatus
from ..schemas.memory import SkillRetrievalQuery, SkillRetrievalResult
from ..schemas.review import BlogReviewReport, ReviewRecommendation, ReviewScorecard
from ..services.approval_service import ApprovalService
from ..services.artifact_service import ArtifactService
from ..services.content_lint import ContentLintService
from ..services.deepagent_content_builder import DeepAgentContentBuilder, deepagent_artifact_filename
from ..services.evaluation_service import EvaluationService
from ..services.memory_service import MemoryService
from ..services.observability import ObservabilityService
from ..services.rendering import (
    render_asset_plan_markdown,
    render_outline_markdown,
    render_review_markdown,
    render_topic_research_markdown,
)
from ..utils.slug import to_part_filename
from ..utils.markdown import normalize_markdown_document
from .routing import (
    route_after_approval,
    route_after_asset,
    route_after_evaluation,
    route_after_improve,
    route_after_length_check,
    route_after_memory,
    route_after_review,
)
from .state import BlogWorkflowState, OutlineWorkflowState


@dataclass(slots=True)
class GraphContext:
    """Dependencies shared by graph nodes."""

    artifact_service: ArtifactService
    approval_service: ApprovalService
    content_lint_service: ContentLintService
    evaluation_service: EvaluationService
    memory_service: MemoryService
    observability_service: ObservabilityService
    deepagent_content_builder: DeepAgentContentBuilder
    topic_research_agent: TopicResearchAgent
    series_architect_agent: SeriesArchitectAgent
    blog_reviewer_agent: BlogReviewerAgent
    blog_improver_agent: BlogImproverAgent
    asset_planner_agent: AssetPlannerAgent


def _empty_retrieval(*, topic: str, audience: str, part_number: int, artifact_type: str, max_skills: int) -> SkillRetrievalResult:
    query = SkillRetrievalQuery(
        topic=topic,
        audience=audience,
        part_number=part_number,
        artifact_type=artifact_type,
        max_skills=max_skills,
    )
    return SkillRetrievalResult(query=query, retrieved_skill_ids=[], retrieved_guidance=[], retrieval_notes=[])


def _fallback_review(state: BlogWorkflowState) -> BlogReviewReport:
    part = state["current_part"]
    retrieval = state.get("retrieved_skills")
    return BlogReviewReport(
        part_number=part.part_number,
        slug=part.slug,
        title=part.title,
        scorecard=ReviewScorecard(
            structure_consistency=7,
            series_alignment=7,
            clarity_of_explanation=7,
            technical_accuracy=7,
            technical_freshness=7,
            depth_and_completeness=7,
            readability_and_tone=7,
            visuals_and_examples=7,
            engagement_and_learning_reinforcement=7,
            practical_relevance=7,
        ),
        strengths=["Review was disabled, so evaluation uses a lightweight fallback scorecard."],
        issues=[],
        priority_fixes=[],
        suggested_additions=[],
        final_recommendation=ReviewRecommendation.APPROVE,
        summary="Lightweight review fallback because the review stage was disabled.",
        freshness_findings=[],
        active_skills_checked=retrieval.retrieved_skill_ids if retrieval else [],
        skills_followed=[],
        skills_violated=[],
        skill_adherence_score=0,
        skill_adherence_notes=["Skill adherence was not fully assessed because review was disabled."],
    )


def build_outline_graph(context: GraphContext, manifest) -> object:
    if StateGraph is None:
        raise RuntimeError("langgraph is required to run the workflow. Install project dependencies first.")
    graph = StateGraph(OutlineWorkflowState)

    def topic_research_node(state: OutlineWorkflowState) -> OutlineWorkflowState:
        context.observability_service.log_node_event(
            run_id=manifest.run_id,
            node_name="topic_research",
            metadata={"topic": state["config"].topic},
        )
        dossier = context.topic_research_agent.run(state["config"])
        context.artifact_service.write_json_artifact(
            manifest=manifest,
            artifact_type=ArtifactType.RESEARCH,
            folder="research",
            filename="topic_research.json",
            payload=dossier.model_dump(mode="json"),
        )
        context.artifact_service.write_markdown_artifact(
            manifest=manifest,
            artifact_type=ArtifactType.RESEARCH,
            folder="research",
            filename="topic_research.md",
            content=render_topic_research_markdown(dossier),
        )
        return {"topic_dossier": dossier}

    def series_architect_node(state: OutlineWorkflowState) -> OutlineWorkflowState:
        context.observability_service.log_node_event(
            run_id=manifest.run_id,
            node_name="series_architect",
            metadata={"topic": state["config"].topic},
        )
        outline = context.series_architect_agent.run(state["config"], state["topic_dossier"])
        context.artifact_service.write_json_artifact(
            manifest=manifest,
            artifact_type=ArtifactType.SERIES_OUTLINE,
            folder="series_outline",
            filename="series_outline.json",
            payload=outline.model_dump(mode="json"),
        )
        context.artifact_service.write_markdown_artifact(
            manifest=manifest,
            artifact_type=ArtifactType.SERIES_OUTLINE,
            folder="series_outline",
            filename="series_outline.md",
            content=render_outline_markdown(outline),
        )
        return {"series_outline": outline}

    graph.add_node("topic_research", topic_research_node)
    graph.add_node("series_architect", series_architect_node)
    graph.add_edge(START, "topic_research")
    graph.add_edge("topic_research", "series_architect")
    graph.add_edge("series_architect", END)
    return graph.compile()


def build_blog_graph(context: GraphContext, manifest) -> object:
    if StateGraph is None:
        raise RuntimeError("langgraph is required to run the workflow. Install project dependencies first.")
    graph = StateGraph(BlogWorkflowState)

    def retrieve_guidance_node(state: BlogWorkflowState) -> BlogWorkflowState:
        part = state["current_part"]
        config = state["config"]
        approved_skills = context.memory_service.list_approved_skills() if config.enable_memory else []
        if not config.enable_memory or not config.use_memory:
            retrieval = _empty_retrieval(
                topic=config.topic,
                audience=config.target_audience,
                part_number=part.part_number,
                artifact_type="draft",
                max_skills=config.max_retrieved_skills,
            )
        else:
            retrieval = context.memory_service.retrieve_skills(
                SkillRetrievalQuery(
                    topic=config.topic,
                    audience=config.target_audience,
                    part_number=part.part_number,
                    artifact_type="draft",
                    max_skills=config.max_retrieved_skills,
                ),
                record_usage=False,
            )
            context.observability_service.log_skill_retrieval(
                run_id=manifest.run_id,
                metadata={
                    "part_number": part.part_number,
                    "retrieved_skill_ids": retrieval.retrieved_skill_ids,
                    "artifact_type": "draft",
                },
            )
        return {"retrieved_skills": retrieval, "approved_skills": approved_skills}

    def deepagent_build_node(state: BlogWorkflowState) -> BlogWorkflowState:
        part = state["current_part"]
        context.observability_service.log_node_event(
            run_id=manifest.run_id,
            node_name="deepagent_content_builder",
            metadata={
                "part_number": part.part_number,
                "topic": state["config"].topic,
                "builder": "deepagents",
            },
        )
        retrieval = state.get("retrieved_skills") or _empty_retrieval(
            topic=state["config"].topic,
            audience=state["config"].target_audience,
            part_number=part.part_number,
            artifact_type="draft",
            max_skills=state["config"].max_retrieved_skills,
        )
        result = context.deepagent_content_builder.build_blog(
            config=state["config"],
            outline=state["series_outline"],
            part=part,
            retrieved_guidance=retrieval,
            run_id=manifest.run_id,
        )
        context.artifact_service.write_markdown_artifact(
            manifest=manifest,
            artifact_type=ArtifactType.RESEARCH,
            folder="research",
            filename=deepagent_artifact_filename(part, suffix="research"),
            content=result.research_markdown,
            part_number=part.part_number,
        )
        context.artifact_service.write_markdown_artifact(
            manifest=manifest,
            artifact_type=ArtifactType.PLAN,
            folder="blog_plans",
            filename=deepagent_artifact_filename(part, suffix="plan"),
            content=result.plan_markdown,
            part_number=part.part_number,
        )
        draft = normalize_markdown_document(result.draft_markdown)
        path = context.artifact_service.write_markdown_artifact(
            manifest=manifest,
            artifact_type=ArtifactType.DRAFT,
            folder="drafts",
            filename=to_part_filename(part.part_number, part.slug),
            content=draft,
            part_number=part.part_number,
        )
        context.artifact_service.write_markdown_artifact(
            manifest=manifest,
            artifact_type=ArtifactType.ASSET,
            folder="assets",
            filename=deepagent_artifact_filename(part, suffix="deepagent-assets"),
            content=result.asset_markdown,
            part_number=part.part_number,
        )
        if result.manifest:
            context.artifact_service.write_json_artifact(
                manifest=manifest,
                artifact_type=ArtifactType.MANIFEST,
                folder="deepagent_manifests",
                filename=f"deepagent-{manifest.run_id}-part-{part.part_number}.json",
                payload=result.manifest,
                part_number=part.part_number,
            )
        context.observability_service.log_artifact_metadata(
            run_id=manifest.run_id,
            artifact_path=str(path),
            metadata={
                "part_number": part.part_number,
                "builder": "deepagents",
                "active_skill_ids": retrieval.retrieved_skill_ids,
                "deepagent_workspace": str(result.workspace) if result.workspace else "",
            },
        )
        context.artifact_service.update_part_status(manifest, part.part_number, PartStatus.DRAFTED)
        draft_lint_report = context.content_lint_service.lint_markdown(draft, state["config"])
        return {
            "draft_markdown": draft,
            "final_markdown": draft,
            "draft_lint_report": draft_lint_report,
            "retrieved_skills": retrieval,
        }

    def length_check_node(state: BlogWorkflowState) -> BlogWorkflowState:
        """Check if the draft meets the minimum word count; if not, request expansion."""
        config = state["config"]
        draft = state.get("final_markdown") or state.get("draft_markdown", "")
        word_count = len(draft.split())
        iteration = state.get("length_expansion_iteration", 0)
        max_expansions = 2  # Limit to avoid infinite loops

        if word_count >= config.min_word_count or iteration >= max_expansions:
            return {"length_expansion_iteration": iteration}

        # Use the improver agent to expand the draft
        part = state["current_part"]
        expand_prompt = (
            f"The current draft is {word_count} words, but the minimum target is {config.min_word_count} words. "
            f"Expand the article by adding more depth to thin sections: more architecture reasoning, "
            f"concrete production examples, tradeoff analysis, failure mode discussion, and system design detail. "
            f"Do NOT add filler. Every added paragraph must contain substantive technical content."
        )
        from ..schemas.review import BlogReviewReport, ReviewRecommendation, ReviewScorecard
        expansion_review = BlogReviewReport(
            part_number=part.part_number,
            slug=part.slug,
            title=part.title,
            scorecard=ReviewScorecard(
                structure_consistency=7, series_alignment=7, clarity_of_explanation=6,
                technical_accuracy=7, technical_freshness=6, depth_and_completeness=4,
                readability_and_tone=7, visuals_and_examples=6,
                engagement_and_learning_reinforcement=6, practical_relevance=6,
            ),
            strengths=["Draft structure is acceptable."],
            issues=[f"Draft is {word_count} words, under the minimum of {config.min_word_count}."],
            priority_fixes=[expand_prompt],
            suggested_additions=["Add more system design depth, production examples, and tradeoff analysis."],
            final_recommendation=ReviewRecommendation.REVISE,
            summary=f"Draft needs expansion from {word_count} to at least {config.min_word_count} words.",
            freshness_findings=[],
        )
        improve_retrieval = state.get("retrieved_skills") or _empty_retrieval(
            topic=config.topic, audience=config.target_audience,
            part_number=part.part_number, artifact_type="final", max_skills=config.max_retrieved_skills,
        )
        lint_report = context.content_lint_service.lint_markdown(draft, config)
        expanded = context.blog_improver_agent.run(
            config, part, draft, expansion_review, improve_retrieval,
            context.content_lint_service.lint_summary(lint_report),
        )
        expanded = normalize_markdown_document(expanded)
        context.artifact_service.write_markdown_artifact(
            manifest=manifest,
            artifact_type=ArtifactType.DRAFT,
            folder="drafts",
            filename=to_part_filename(part.part_number, part.slug),
            content=expanded,
            part_number=part.part_number,
        )
        new_lint = context.content_lint_service.lint_markdown(expanded, config)
        return {
            "draft_markdown": expanded,
            "final_markdown": expanded,
            "draft_lint_report": new_lint,
            "length_expansion_iteration": iteration + 1,
        }

    def review_node(state: BlogWorkflowState) -> BlogWorkflowState:
        part = state["current_part"]
        config = state["config"]
        draft_lint_report = state.get("draft_lint_report") or context.content_lint_service.lint_markdown(
            state["draft_markdown"], config
        )
        review_retrieval = (
            context.memory_service.retrieve_skills(
                SkillRetrievalQuery(
                    topic=config.topic,
                    audience=config.target_audience,
                    part_number=part.part_number,
                    artifact_type="review",
                    max_skills=config.max_retrieved_skills,
                ),
                record_usage=False,
            )
            if config.enable_memory and config.use_memory
            else _empty_retrieval(
                topic=config.topic,
                audience=config.target_audience,
                part_number=part.part_number,
                artifact_type="review",
                max_skills=config.max_retrieved_skills,
            )
        )
        report = context.blog_reviewer_agent.run(
            state["config"],
            part,
            state["draft_markdown"],
            review_retrieval,
            context.content_lint_service.lint_summary(draft_lint_report),
        )
        report = context.content_lint_service.enrich_review_report(
            report,
            draft_lint_report,
            review_retrieval.retrieved_skill_ids,
            config,
        )
        context.artifact_service.write_json_artifact(
            manifest=manifest,
            artifact_type=ArtifactType.REVIEW,
            folder="reviews",
            filename=to_part_filename(part.part_number, part.slug, suffix="review", extension="json"),
            payload=report.model_dump(mode="json"),
            part_number=part.part_number,
        )
        context.artifact_service.write_markdown_artifact(
            manifest=manifest,
            artifact_type=ArtifactType.REVIEW,
            folder="reviews",
            filename=to_part_filename(part.part_number, part.slug, suffix="review"),
            content=render_review_markdown(report),
            part_number=part.part_number,
        )
        context.observability_service.log_skill_adherence(
            run_id=manifest.run_id,
            metadata={
                "part_number": part.part_number,
                "active_skills_checked": report.active_skills_checked,
                "skills_followed": report.skills_followed,
                "skills_violated": report.skills_violated,
                "skill_adherence_score": report.skill_adherence_score,
            },
        )
        context.artifact_service.update_part_status(manifest, part.part_number, PartStatus.REVIEWED)
        return {
            "review_report": report,
            "retrieved_skills": review_retrieval,
            "draft_lint_report": draft_lint_report,
        }

    def improve_node(state: BlogWorkflowState) -> BlogWorkflowState:
        part = state["current_part"]
        approval_comments = ""
        refreshed_record = None
        if state.get("approval_record") and state["approval_record"].status == ApprovalDecision.CHANGES_REQUESTED:
            approval_comments = state["approval_record"].comments
            refreshed_record = context.approval_service.reset_to_pending(part.part_number, part.slug)
        review = state.get("review_report")
        if review is None:
            return {"final_markdown": state["draft_markdown"], "approval_record": refreshed_record}
        config = state["config"]
        draft_lint_report = state.get("draft_lint_report") or context.content_lint_service.lint_markdown(
            state["draft_markdown"], config
        )
        improve_retrieval = (
            context.memory_service.retrieve_skills(
                SkillRetrievalQuery(
                    topic=config.topic,
                    audience=config.target_audience,
                    part_number=part.part_number,
                    artifact_type="final",
                    max_skills=config.max_retrieved_skills,
                    issue_types=review.skills_violated,
                ),
                record_usage=False,
            )
            if config.enable_memory and config.use_memory
            else _empty_retrieval(
                topic=config.topic,
                audience=config.target_audience,
                part_number=part.part_number,
                artifact_type="final",
                max_skills=config.max_retrieved_skills,
            )
        )
        final_markdown = context.blog_improver_agent.run(
            state["config"],
            part,
            state["draft_markdown"],
            review,
            improve_retrieval,
            context.content_lint_service.lint_summary(draft_lint_report),
            approval_comments=approval_comments,
        )
        final_markdown = normalize_markdown_document(final_markdown)
        if not final_markdown.strip():
            final_markdown = state["draft_markdown"]
        context.artifact_service.write_markdown_artifact(
            manifest=manifest,
            artifact_type=ArtifactType.FINAL,
            folder="final",
            filename=to_part_filename(part.part_number, part.slug),
            content=final_markdown,
            part_number=part.part_number,
        )
        context.artifact_service.update_part_status(manifest, part.part_number, PartStatus.IMPROVED)
        iteration = state.get("approval_iteration", 0) + 1
        final_lint_report = context.content_lint_service.lint_markdown(final_markdown, config)
        return {
            "final_markdown": final_markdown,
            "final_lint_report": final_lint_report,
            "approval_record": refreshed_record,
            "approval_iteration": iteration,
            "retrieved_skills": improve_retrieval,
        }

    def asset_node(state: BlogWorkflowState) -> BlogWorkflowState:
        part = state["current_part"]
        final_markdown = state.get("final_markdown") or state["draft_markdown"]
        plan = context.asset_planner_agent.run(state["config"], part, final_markdown)
        context.artifact_service.write_json_artifact(
            manifest=manifest,
            artifact_type=ArtifactType.ASSET,
            folder="assets",
            filename=to_part_filename(part.part_number, part.slug, suffix="assets", extension="json"),
            payload=plan.model_dump(mode="json"),
            part_number=part.part_number,
        )
        context.artifact_service.write_markdown_artifact(
            manifest=manifest,
            artifact_type=ArtifactType.ASSET,
            folder="assets",
            filename=to_part_filename(part.part_number, part.slug, suffix="assets"),
            content=render_asset_plan_markdown(plan),
            part_number=part.part_number,
        )
        context.artifact_service.update_part_status(manifest, part.part_number, PartStatus.ASSET_PLANNED)
        return {"asset_plan": plan}

    def evaluation_node(state: BlogWorkflowState) -> BlogWorkflowState:
        part = state["current_part"]
        report = state.get("review_report") or _fallback_review(state)
        final_markdown = state.get("final_markdown") or state["draft_markdown"]
        # Use stricter final artifact validation instead of basic lint
        lint_report = context.content_lint_service.validate_final_artifact(
            final_markdown, state["config"]
        )
        evaluation = context.evaluation_service.evaluate_blog(
            manifest=manifest,
            config=state["config"],
            review_report=report,
            final_markdown=final_markdown,
            lint_report=lint_report,
            active_skill_ids=(state.get("retrieved_skills") or _empty_retrieval(topic="", audience="", part_number=part.part_number, artifact_type="draft", max_skills=0)).retrieved_skill_ids,
        )
        context.observability_service.log_evaluation_summary(
            run_id=manifest.run_id,
            metadata={
                "part_number": part.part_number,
                "overall_score": evaluation.overall_score,
                "skill_adherence_score": evaluation.skill_adherence_score,
            },
        )
        return {"blog_evaluation": evaluation, "final_lint_report": lint_report}

    def memory_update_node(state: BlogWorkflowState) -> BlogWorkflowState:
        if not state["config"].enable_memory:
            return {}
        part = state["current_part"]
        feedback_items = []
        if state.get("review_report") is not None:
            feedback_items.extend(
                context.memory_service.capture_review_feedback(
                    run_id=manifest.run_id,
                    report=state["review_report"],
                    artifact_path=str(
                        context.artifact_service.path_for_part("reviews", part.part_number, part.slug, suffix="review")
                    ),
                )
            )
        if state.get("blog_evaluation") is not None:
            feedback_items.extend(
                context.memory_service.capture_evaluation_feedback(
                    run_id=manifest.run_id,
                    evaluation=state["blog_evaluation"],
                    artifact_path=str(
                        context.artifact_service.path_for_part("evaluations/blog", part.part_number, part.slug, suffix="eval")
                    ),
                )
            )
        memory_result = context.memory_service.build_candidate_skills(
            topic=state["config"].topic,
            audience=state["config"].target_audience,
            config=state["config"],
        )
        context.observability_service.log_feedback_event(
            run_id=manifest.run_id,
            metadata={
                "part_number": part.part_number,
                "feedback_ids": [item.feedback_id for item in feedback_items],
                "candidate_skill_ids": [skill.id for skill in memory_result.candidate_skills_created],
            },
        )
        return {
            "feedback_items": feedback_items,
            "candidate_skills": memory_result.candidate_skills_created,
            "memory_update_result": memory_result,
            "approved_skills": context.memory_service.list_approved_skills(),
        }

    def approval_node(state: BlogWorkflowState) -> BlogWorkflowState:
        part = state["current_part"]
        record = context.approval_service.ensure_pending(part.part_number, part.slug)
        if record.status == ApprovalDecision.PENDING:
            context.artifact_service.update_part_status(
                manifest, part.part_number, PartStatus.WAITING_FOR_APPROVAL
            )
            return {"approval_record": record, "publish_ready": False}
        if record.status in {ApprovalDecision.APPROVED, ApprovalDecision.APPROVED_WITH_NOTES}:
            context.artifact_service.update_part_status(manifest, part.part_number, PartStatus.APPROVED)
            return {"approval_record": record, "publish_ready": True}
        if record.status == ApprovalDecision.REJECTED:
            context.artifact_service.update_part_status(manifest, part.part_number, PartStatus.REJECTED)
            return {"approval_record": record, "publish_ready": False, "rejected": True}
        return {"approval_record": record, "publish_ready": False}

    graph.add_node("retrieve_guidance", retrieve_guidance_node)
    graph.add_node("deepagent_build", deepagent_build_node)
    graph.add_node("length_check", length_check_node)
    graph.add_node("review", review_node)
    graph.add_node("improve", improve_node)
    graph.add_node("asset", asset_node)
    graph.add_node("evaluation", evaluation_node)
    graph.add_node("memory_update", memory_update_node)
    graph.add_node("approval", approval_node)

    graph.add_edge(START, "retrieve_guidance")
    graph.add_edge("retrieve_guidance", "deepagent_build")
    graph.add_edge("deepagent_build", "length_check")
    graph.add_conditional_edges(
        "length_check",
        route_after_length_check,
        {
            "length_check": "length_check",
            "review": "review",
            "asset": "asset",
            "evaluation": "evaluation",
            "memory_update": "memory_update",
            "approval": "approval",
            "complete": END,
        },
    )
    graph.add_conditional_edges(
        "review",
        route_after_review,
        {
            "improve": "improve",
            "asset": "asset",
            "evaluation": "evaluation",
            "memory_update": "memory_update",
            "approval": "approval",
            "complete": END,
        },
    )
    graph.add_conditional_edges(
        "improve",
        route_after_improve,
        {
            "asset": "asset",
            "evaluation": "evaluation",
            "memory_update": "memory_update",
            "approval": "approval",
            "complete": END,
        },
    )
    graph.add_conditional_edges("asset", route_after_asset, {"evaluation": "evaluation", "memory_update": "memory_update", "approval": "approval", "complete": END})
    graph.add_conditional_edges("evaluation", route_after_evaluation, {"memory_update": "memory_update", "approval": "approval", "complete": END})
    graph.add_conditional_edges("memory_update", route_after_memory, {"approval": "approval", "complete": END})
    graph.add_conditional_edges(
        "approval",
        route_after_approval,
        {
            "awaiting_human": END,
            "complete": END,
            "improve": "improve",
            "rejected": END,
        },
    )
    return graph.compile()
