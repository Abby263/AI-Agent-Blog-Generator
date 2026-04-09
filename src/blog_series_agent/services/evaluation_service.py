"""Evaluation services for blog, series, and run artifacts."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from ..config.settings import SeriesRunConfig
from ..schemas.approval import ApprovalDecision, ApprovalRecord
from ..schemas.artifacts import ArtifactType, RunManifest
from ..schemas.evaluation import (
    BlogEvaluation,
    ContentLintReport,
    CriterionScore,
    EvaluationIssue,
    EvaluationSeverity,
    EvaluationTrend,
    ImprovementOpportunity,
    RepeatedFailurePattern,
    RunEvaluation,
    SeriesEvaluation,
)
from ..schemas.review import BlogReviewReport
from ..schemas.series import BlogSeriesOutline
from ..utils.files import read_json
from ..utils.slug import to_part_filename


class EvaluationService:
    """Builds and persists evaluations in a dedicated layer."""

    def __init__(self, artifact_service) -> None:  # noqa: ANN001
        self.artifact_service = artifact_service

    def evaluate_blog(
        self,
        *,
        manifest: RunManifest,
        config: SeriesRunConfig,
        review_report: BlogReviewReport,
        final_markdown: str,
        lint_report: ContentLintReport,
        active_skill_ids: list[str],
    ) -> BlogEvaluation:
        lint_penalty = self._criterion_penalties(lint_report, config)
        criteria = [
            CriterionScore(
                name="structure_consistency",
                score=max(0.0, review_report.scorecard.structure_consistency - lint_penalty["structure_consistency"]),
                rationale="Derived from reviewer structure scoring with deterministic checks for required chapter sections.",
                evidence=review_report.strengths[:2] + [finding.message for finding in lint_report.findings if finding.finding_type == "missing_sections"][:1],
                severity=EvaluationSeverity.LOW if review_report.scorecard.structure_consistency >= 7 else EvaluationSeverity.MEDIUM,
                recommended_action="Tighten section ordering and preserve required chapter structure.",
            ),
            CriterionScore(
                name="series_alignment",
                score=review_report.scorecard.series_alignment,
                rationale="Derived from reviewer series-alignment scoring.",
                evidence=review_report.summary.split(".")[:2],
                severity=EvaluationSeverity.LOW if review_report.scorecard.series_alignment >= 7 else EvaluationSeverity.MEDIUM,
                recommended_action="Reinforce links to prior and next parts in the series.",
            ),
            CriterionScore(
                name="clarity_of_explanation",
                score=max(0.0, review_report.scorecard.clarity_of_explanation - lint_penalty["clarity_of_explanation"]),
                rationale="Derived from reviewer clarity scoring, with penalties for thin content that limits explanation depth.",
                evidence=review_report.issues[:2] + [f"Word count: {lint_report.word_count}"][:1],
                severity=EvaluationSeverity.LOW if review_report.scorecard.clarity_of_explanation >= 7 else EvaluationSeverity.HIGH,
                recommended_action="Prefer intuition-first explanations followed by architecture detail.",
            ),
            CriterionScore(
                name="technical_accuracy",
                score=review_report.scorecard.technical_accuracy,
                rationale="Derived from reviewer accuracy scoring.",
                evidence=review_report.freshness_findings[:2],
                severity=EvaluationSeverity.LOW if review_report.scorecard.technical_accuracy >= 7 else EvaluationSeverity.HIGH,
                recommended_action="Validate terminology and update stale technical claims.",
            ),
            CriterionScore(
                name="technical_freshness",
                score=max(0.0, review_report.scorecard.technical_freshness - lint_penalty["technical_freshness"]),
                rationale="Derived from reviewer freshness scoring, with deterministic penalties for weak or generic references.",
                evidence=review_report.freshness_findings[:2] + lint_report.weak_references[:1],
                severity=EvaluationSeverity.LOW if review_report.scorecard.technical_freshness >= 7 else EvaluationSeverity.HIGH,
                recommended_action="Refresh the article with current practice and modern framing.",
            ),
            CriterionScore(
                name="depth_and_completeness",
                score=max(0.0, review_report.scorecard.depth_and_completeness - lint_penalty["depth_and_completeness"]),
                rationale="Derived from reviewer depth scoring, penalizing under-target length and missing required chapter sections.",
                evidence=review_report.priority_fixes[:2] + [f"Configured word range: {config.min_word_count}-{config.max_word_count}"][:1],
                severity=EvaluationSeverity.LOW if review_report.scorecard.depth_and_completeness >= 7 else EvaluationSeverity.MEDIUM,
                recommended_action="Expand thin sections and add system-level detail where needed.",
            ),
            CriterionScore(
                name="readability_and_tone",
                score=review_report.scorecard.readability_and_tone,
                rationale="Derived from reviewer tone scoring.",
                evidence=review_report.issues[:2],
                severity=EvaluationSeverity.LOW if review_report.scorecard.readability_and_tone >= 7 else EvaluationSeverity.MEDIUM,
                recommended_action="Use a more human, teaching-first narrative voice.",
            ),
            CriterionScore(
                name="visuals_and_examples",
                score=max(0.0, review_report.scorecard.visuals_and_examples - lint_penalty["visuals_and_examples"]),
                rationale="Derived from reviewer visual scoring, with deterministic checks for placeholder visual artifacts.",
                evidence=review_report.suggested_additions[:2] + lint_report.placeholder_visuals[:1],
                severity=EvaluationSeverity.LOW if review_report.scorecard.visuals_and_examples >= 7 else EvaluationSeverity.MEDIUM,
                recommended_action="Add richer diagrams, tables, and practical examples.",
            ),
            CriterionScore(
                name="engagement_and_learning_reinforcement",
                score=review_report.scorecard.engagement_and_learning_reinforcement,
                rationale="Derived from reviewer engagement scoring.",
                evidence=review_report.suggested_additions[:2],
                severity=EvaluationSeverity.LOW if review_report.scorecard.engagement_and_learning_reinforcement >= 7 else EvaluationSeverity.MEDIUM,
                recommended_action="Add synthesis and stronger test-your-learning prompts.",
            ),
            CriterionScore(
                name="practical_relevance",
                score=max(0.0, review_report.scorecard.practical_relevance - lint_penalty["practical_relevance"]),
                rationale="Derived from reviewer practical relevance scoring, with penalties when references stay too generic.",
                evidence=review_report.strengths[:2] + lint_report.weak_references[:1],
                severity=EvaluationSeverity.LOW if review_report.scorecard.practical_relevance >= 7 else EvaluationSeverity.MEDIUM,
                recommended_action="Tie each section back to production engineering usage.",
            ),
        ]
        issues = [
            EvaluationIssue(
                issue_id=f"eval-{review_report.part_number}-{index}",
                issue_type="review_issue",
                severity=EvaluationSeverity.HIGH if "must" in issue.lower() or "missing" in issue.lower() else EvaluationSeverity.MEDIUM,
                description=issue,
                evidence=review_report.priority_fixes[:2],
                recommended_action=review_report.priority_fixes[index] if index < len(review_report.priority_fixes) else "Revise this section.",
                related_skill_ids=review_report.skills_violated,
            )
            for index, issue in enumerate(review_report.issues[:5])
        ]
        for finding in lint_report.findings:
            issues.append(
                EvaluationIssue(
                    issue_id=f"lint-{review_report.part_number}-{finding.finding_type}",
                    issue_type=finding.finding_type,
                    severity=finding.severity,
                    description=finding.message,
                    evidence=[f"Word count: {lint_report.word_count}"] if finding.finding_type == "under_target_length" else [],
                    recommended_action=finding.recommended_action,
                    related_skill_ids=review_report.skills_violated,
                )
            )
        evaluation = BlogEvaluation(
            part_number=review_report.part_number,
            slug=review_report.slug,
            title=review_report.title,
            criteria=criteria,
            summary=(
                f"Blog evaluation for part {review_report.part_number} combines reviewer judgment with deterministic "
                f"content checks. Final length: {lint_report.word_count} words."
            ),
            strengths=review_report.strengths,
            issues=issues,
            improvement_opportunities=[
                ImprovementOpportunity(
                    title="Address priority reviewer fixes",
                    priority=EvaluationSeverity.HIGH if review_report.priority_fixes else EvaluationSeverity.MEDIUM,
                    target_scope="blog",
                    rationale="Priority reviewer fixes and deterministic lint findings remain the clearest path to better quality.",
                    recommended_action="Implement the reviewer priority fixes and resolve deterministic content-lint findings.",
                    related_issues=[issue.issue_id for issue in issues],
                )
            ],
            active_skills_checked=active_skill_ids,
            skills_followed=review_report.skills_followed,
            skills_violated=review_report.skills_violated,
            skill_adherence_score=review_report.skill_adherence_score,
            skill_adherence_notes=review_report.skill_adherence_notes,
        )
        self.artifact_service.write_json_artifact(
            manifest=manifest,
            artifact_type=ArtifactType.EVALUATION,
            folder="evaluations/blog",
            filename=to_part_filename(review_report.part_number, review_report.slug, suffix="eval", extension="json"),
            payload=evaluation.model_dump(mode="json"),
            part_number=review_report.part_number,
        )
        self.artifact_service.write_markdown_artifact(
            manifest=manifest,
            artifact_type=ArtifactType.EVALUATION,
            folder="evaluations/blog",
            filename=to_part_filename(review_report.part_number, review_report.slug, suffix="eval"),
            content=self.render_blog_evaluation_markdown(evaluation, final_markdown, lint_report),
            part_number=review_report.part_number,
        )
        return evaluation

    def evaluate_series(
        self,
        *,
        manifest: RunManifest,
        outline: BlogSeriesOutline,
        blog_evaluations: list[BlogEvaluation],
    ) -> SeriesEvaluation:
        avg = round(sum(item.overall_score for item in blog_evaluations) / len(blog_evaluations), 2) if blog_evaluations else 0.0
        repeated_patterns = self._patterns_from_blog_evaluations(blog_evaluations)
        evaluation = SeriesEvaluation(
            topic=outline.topic,
            criteria=[
                CriterionScore(name="progression_quality", score=avg, rationale="Average of blog evaluations.", evidence=[outline.narrative_arc], recommended_action="Keep the learning journey progressive."),
                CriterionScore(name="topic_overlap", score=max(0.0, 10 - len(repeated_patterns)), rationale="Penalty from repeated issue patterns.", evidence=[pattern.summary for pattern in repeated_patterns], recommended_action="Reduce overlap between adjacent parts."),
                CriterionScore(name="continuity_between_parts", score=avg, rationale="Derived from per-part evaluations.", evidence=[part.title for part in outline.parts[:3]], recommended_action="Strengthen continuity callbacks."),
                CriterionScore(name="tone_and_structure_consistency", score=avg, rationale="Derived from evaluation consistency.", evidence=[item.summary for item in blog_evaluations[:2]], recommended_action="Preserve the chapter-style template across parts."),
                CriterionScore(name="coverage_gaps", score=max(0.0, 10 - len(outline.parts) / 4), rationale="Heuristic coverage estimate.", evidence=outline.learning_goals, recommended_action="Fill missing foundational or advanced topics where needed."),
            ],
            summary="Series-level evaluation aggregated from blog evaluations and the series outline.",
            coverage_gaps=[] if len(outline.parts) >= 10 else ["Series may be too short to cover both foundational and advanced topics."],
            repeated_patterns=repeated_patterns,
            improvement_opportunities=[
                ImprovementOpportunity(
                    title="Reduce repeated issue clusters across the series",
                    priority=EvaluationSeverity.MEDIUM,
                    target_scope="series",
                    rationale="Cross-series patterns indicate guidance gaps.",
                    recommended_action="Promote repeated feedback into reusable approved skills and apply them earlier in the pipeline.",
                    related_issues=[pattern.pattern_id for pattern in repeated_patterns],
                )
            ],
        )
        self.artifact_service.write_json_artifact(
            manifest=manifest,
            artifact_type=ArtifactType.EVALUATION,
            folder="evaluations/series",
            filename="series-eval.json",
            payload=evaluation.model_dump(mode="json"),
        )
        self.artifact_service.write_markdown_artifact(
            manifest=manifest,
            artifact_type=ArtifactType.EVALUATION,
            folder="evaluations/series",
            filename="series-eval.md",
            content=self.render_series_evaluation_markdown(evaluation),
        )
        return evaluation

    def evaluate_run(
        self,
        *,
        manifest: RunManifest,
        review_reports: list[BlogReviewReport],
        approvals: list[ApprovalRecord],
    ) -> RunEvaluation:
        average_review_score = round(sum(report.scorecard.total_score for report in review_reports) / len(review_reports), 2) if review_reports else 0.0
        approval_counter = Counter(record.status.value for record in approvals)
        repeated = self._patterns_from_reviews(review_reports)
        evaluation = RunEvaluation(
            run_id=manifest.run_id,
            topic=manifest.topic,
            num_parts_requested=manifest.num_parts,
            num_parts_completed=len({artifact.part_number for artifact in manifest.artifacts if artifact.part_number is not None}),
            average_review_score=average_review_score,
            approval_outcomes=dict(approval_counter),
            repeated_issue_patterns=repeated,
            retry_counts={"approval_loops": sum(1 for status in manifest.part_statuses.values() if status.name == "APPROVED")},
            human_revision_load=sum(1 for record in approvals if record.status == ApprovalDecision.CHANGES_REQUESTED),
            trends=[
                EvaluationTrend(
                    name="review_score_distribution",
                    direction="stable" if average_review_score >= 70 else "declining",
                    evidence=[str(report.scorecard.total_score) for report in review_reports[:5]],
                    summary="Run trend derived from review score distribution.",
                )
            ],
            improvement_opportunities=[
                ImprovementOpportunity(
                    title="Reduce human revision load",
                    priority=EvaluationSeverity.MEDIUM,
                    target_scope="run",
                    rationale="Changes requested during approval indicate preventable misses earlier in the flow.",
                    recommended_action="Use approved reusable skills during writing, review, and improvement.",
                    related_issues=[pattern.pattern_id for pattern in repeated],
                )
            ],
            summary="Run-level evaluation aggregated from review reports and approval outcomes.",
        )
        self.artifact_service.write_json_artifact(
            manifest=manifest,
            artifact_type=ArtifactType.EVALUATION,
            folder="evaluations/runs",
            filename=f"{manifest.run_id}-eval.json",
            payload=evaluation.model_dump(mode="json"),
        )
        return evaluation

    def load_blog_evaluation(self, part_id: str) -> BlogEvaluation | None:
        part_stem = part_id.removesuffix(".md").removesuffix(".json")
        matches = list((self.artifact_service.output_dir / "evaluations" / "blog").glob(f"{part_stem}-eval.json"))
        if not matches:
            return None
        return BlogEvaluation.model_validate(read_json(matches[0]))

    def latest_series_evaluation(self) -> SeriesEvaluation | None:
        path = self.artifact_service.latest_series_evaluation_path()
        if path is None:
            return None
        return SeriesEvaluation.model_validate(read_json(path))

    @staticmethod
    def render_blog_evaluation_markdown(
        evaluation: BlogEvaluation,
        final_markdown: str,
        lint_report: ContentLintReport,
    ) -> str:
        active_skills = [f"- {item}" for item in evaluation.active_skills_checked] or ["- None"]
        skills_followed = [f"- {item}" for item in evaluation.skills_followed] or ["- None"]
        skills_violated = [f"- {item}" for item in evaluation.skills_violated] or ["- None"]
        lint_findings = [f"- {finding.finding_type}: {finding.message}" for finding in lint_report.findings] or ["- None"]
        return "\n".join(
            [
                f"# Blog Evaluation: Part {evaluation.part_number} - {evaluation.title}",
                "",
                f"**Overall Score:** {evaluation.overall_score}/10",
                f"**Skill Adherence Score:** {evaluation.skill_adherence_score}/10",
                "",
                "## Summary",
                evaluation.summary,
                "",
                "## Criteria",
                *[
                    f"- **{criterion.name}:** {criterion.score}/10 - {criterion.rationale}"
                    for criterion in evaluation.criteria
                ],
                "",
                "## Active Skills Checked",
                *active_skills,
                "",
                "## Skills Followed",
                *skills_followed,
                "",
                "## Skills Violated",
                *skills_violated,
                "",
                "## Deterministic Lint Findings",
                *lint_findings,
                "",
                "## Improvement Opportunities",
                *[f"- {item.title}: {item.recommended_action}" for item in evaluation.improvement_opportunities],
                "",
                "## Final Artifact Length",
                str(len(final_markdown.split())),
            ]
        )

    @staticmethod
    def _criterion_penalties(lint_report: ContentLintReport, config: SeriesRunConfig) -> dict[str, float]:
        """Calibrated penalties that scale with severity, avoiding over-literal deductions."""
        penalties = {
            "structure_consistency": 0.0,
            "clarity_of_explanation": 0.0,
            "technical_freshness": 0.0,
            "depth_and_completeness": 0.0,
            "visuals_and_examples": 0.0,
            "practical_relevance": 0.0,
        }
        deficit = max(0, config.min_word_count - lint_report.word_count)
        deficit_pct = deficit / max(config.min_word_count, 1)
        # Scale penalties proportionally to the shortfall
        if deficit_pct >= 0.3:
            penalties["depth_and_completeness"] += 2.0
            penalties["clarity_of_explanation"] += 0.5
        elif deficit_pct >= 0.15:
            penalties["depth_and_completeness"] += 1.0
        elif deficit > 0:
            penalties["depth_and_completeness"] += 0.5
        if lint_report.missing_sections:
            num_missing = len(lint_report.missing_sections)
            # Proportional: 1-2 missing = small penalty, 5+ = large penalty
            if num_missing >= 5:
                penalties["structure_consistency"] += 2.0
                penalties["depth_and_completeness"] += 0.5
            elif num_missing >= 3:
                penalties["structure_consistency"] += 1.0
            else:
                penalties["structure_consistency"] += 0.5
        if lint_report.placeholder_visuals:
            penalties["visuals_and_examples"] += 1.5
        if lint_report.weak_references:
            if len(lint_report.weak_references) >= 2:
                penalties["technical_freshness"] += 1.0
                penalties["practical_relevance"] += 0.5
            else:
                penalties["practical_relevance"] += 0.5
        return penalties

    @staticmethod
    def render_series_evaluation_markdown(evaluation: SeriesEvaluation) -> str:
        coverage_gaps = [f"- {gap}" for gap in evaluation.coverage_gaps] or ["- None"]
        repeated_patterns = [f"- {pattern.issue_type}: {pattern.summary}" for pattern in evaluation.repeated_patterns] or ["- None"]
        return "\n".join(
            [
                f"# Series Evaluation: {evaluation.topic}",
                "",
                f"**Overall Score:** {evaluation.overall_score}/10",
                "",
                "## Summary",
                evaluation.summary,
                "",
                "## Criteria",
                *[f"- **{criterion.name}:** {criterion.score}/10 - {criterion.rationale}" for criterion in evaluation.criteria],
                "",
                "## Coverage Gaps",
                *coverage_gaps,
                "",
                "## Repeated Patterns",
                *repeated_patterns,
            ]
        )

    @staticmethod
    def _patterns_from_blog_evaluations(blog_evaluations: list[BlogEvaluation]) -> list[RepeatedFailurePattern]:
        counter: Counter[str] = Counter()
        affected: dict[str, list[int]] = {}
        for evaluation in blog_evaluations:
            for issue in evaluation.issues:
                counter[issue.issue_type] += 1
                affected.setdefault(issue.issue_type, []).append(evaluation.part_number)
        return [
            RepeatedFailurePattern(
                pattern_id=f"pattern-{issue_type}",
                issue_type=issue_type,
                frequency=frequency,
                affected_parts=sorted(set(affected.get(issue_type, []))),
                summary=f"{issue_type} appeared in {frequency} blog evaluations.",
                recommended_action=f"Create or refine reusable guidance for {issue_type}.",
            )
            for issue_type, frequency in counter.items()
            if frequency > 1
        ]

    @staticmethod
    def _patterns_from_reviews(review_reports: list[BlogReviewReport]) -> list[RepeatedFailurePattern]:
        counter: Counter[str] = Counter()
        affected: dict[str, list[int]] = {}
        for report in review_reports:
            for issue in report.issues:
                normalized = issue.split(":")[0].lower().replace(" ", "_")
                counter[normalized] += 1
                affected.setdefault(normalized, []).append(report.part_number)
        return [
            RepeatedFailurePattern(
                pattern_id=f"run-pattern-{issue_type}",
                issue_type=issue_type,
                frequency=frequency,
                affected_parts=sorted(set(affected.get(issue_type, []))),
                summary=f"{issue_type} appeared repeatedly during the run.",
                recommended_action="Convert repeated feedback into candidate reusable skills.",
            )
            for issue_type, frequency in counter.items()
            if frequency > 1
        ]
