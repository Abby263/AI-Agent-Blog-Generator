"""Feedback logging, candidate skill extraction, approval, and retrieval."""

from __future__ import annotations

import fcntl
import json
from collections import Counter, defaultdict
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from ..config.settings import RunMode, SeriesRunConfig
from ..schemas.approval import ApprovalRecord
from ..schemas.evaluation import BlogEvaluation, EvaluationSeverity
from ..schemas.memory import (
    FeedbackItem,
    FeedbackSeverity,
    FeedbackSourceType,
    FeedbackType,
    MemoryUpdateResult,
    ReusableSkill,
    SkillRetrievalQuery,
    SkillRetrievalResult,
    SkillStatus,
    SkillTriggerConditions,
)
from ..schemas.review import BlogReviewReport
from ..services.rendering import render_skills_markdown
from ..utils.files import ensure_directory, read_json, write_json
from ..utils.slug import slugify


class MemoryService:
    """Manages raw feedback and approved reusable skills."""

    def __init__(self, root_dir: str | Path = "data/memory") -> None:
        self.root_dir = Path(root_dir)
        ensure_directory(self.root_dir)
        self.raw_feedback_log_path = self.root_dir / "raw_feedback_log.jsonl"
        self.raw_feedback_markdown_path = self.root_dir / "raw_feedback_log.md"
        self.candidate_skills_path = self.root_dir / "skill_candidates.json"
        self.approved_skills_path = self.root_dir / "approved_skills.json"
        self.approved_skills_markdown_path = self.root_dir / "approved_skills.md"
        self.retrieval_log_path = self.root_dir / "retrieval_log.jsonl"
        self._lock_path = self.root_dir / ".memory.lock"
        if not self.candidate_skills_path.exists():
            write_json(self.candidate_skills_path, [])
        if not self.approved_skills_path.exists():
            write_json(self.approved_skills_path, [])

    @contextmanager
    def _file_lock(self):
        """Acquire an exclusive file lock for concurrency-safe writes."""
        lock_file = self._lock_path.open("w")
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            lock_file.close()

    def add_feedback(self, item: FeedbackItem) -> FeedbackItem:
        with self.raw_feedback_log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(item.model_dump(mode="json"), default=str) + "\n")
        self._write_feedback_summary()
        return item

    def list_feedback(self) -> list[FeedbackItem]:
        if not self.raw_feedback_log_path.exists():
            return []
        items = []
        for line in self.raw_feedback_log_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                items.append(FeedbackItem.model_validate(json.loads(line)))
        return items

    def list_candidate_skills(self) -> list[ReusableSkill]:
        return [ReusableSkill.model_validate(item) for item in read_json(self.candidate_skills_path)]

    def list_approved_skills(self) -> list[ReusableSkill]:
        return [ReusableSkill.model_validate(item) for item in read_json(self.approved_skills_path)]

    def persist_candidate_skills(self, skills: list[ReusableSkill]) -> None:
        write_json(self.candidate_skills_path, [skill.model_dump(mode="json") for skill in skills])

    def persist_approved_skills(self, skills: list[ReusableSkill]) -> None:
        approved = [skill for skill in skills if skill.status == SkillStatus.APPROVED and skill.active]
        write_json(self.approved_skills_path, [skill.model_dump(mode="json") for skill in approved])
        self.approved_skills_markdown_path.write_text(
            render_skills_markdown("Approved Reusable Skills", approved),
            encoding="utf-8",
        )

    def capture_review_feedback(self, *, run_id: str, report: BlogReviewReport, artifact_path: str) -> list[FeedbackItem]:
        items: list[FeedbackItem] = []
        for issue in report.issues:
            items.append(
                self.add_feedback(
                    FeedbackItem(
                        feedback_id=f"fb-{uuid4().hex[:10]}",
                        source_type=FeedbackSourceType.REVIEWER,
                        source_artifact=artifact_path,
                        part_number=report.part_number,
                        blog_slug=report.slug,
                        raw_feedback=issue,
                        normalized_issue_type=self.classify_feedback(issue),
                        severity=self.infer_severity(issue),
                        suggested_fix=report.priority_fixes[0] if report.priority_fixes else "Revise the relevant section.",
                        reviewer="reviewer-agent",
                        run_id=run_id,
                    )
                )
            )
        for violated_skill in report.skills_violated:
            items.append(
                self.add_feedback(
                    FeedbackItem(
                        feedback_id=f"fb-{uuid4().hex[:10]}",
                        source_type=FeedbackSourceType.REVIEWER,
                        source_artifact=artifact_path,
                        part_number=report.part_number,
                        blog_slug=report.slug,
                        raw_feedback=f"Skill violated: {violated_skill}",
                        normalized_issue_type=FeedbackType.SKILL_VIOLATION,
                        severity=FeedbackSeverity.MEDIUM,
                        suggested_fix="Apply the active guidance explicitly in the revised draft.",
                        reviewer="reviewer-agent",
                        run_id=run_id,
                    )
                )
            )
        return items

    def capture_evaluation_feedback(self, *, run_id: str, evaluation: BlogEvaluation, artifact_path: str) -> list[FeedbackItem]:
        items: list[FeedbackItem] = []
        for issue in evaluation.issues:
            items.append(
                self.add_feedback(
                    FeedbackItem(
                        feedback_id=f"fb-{uuid4().hex[:10]}",
                        source_type=FeedbackSourceType.EVALUATION,
                        source_artifact=artifact_path,
                        part_number=evaluation.part_number,
                        blog_slug=evaluation.slug,
                        raw_feedback=issue.description,
                        normalized_issue_type=self.classify_feedback(issue.issue_type),
                        severity=self._from_eval_severity(issue.severity),
                        suggested_fix=issue.recommended_action,
                        reviewer="evaluation-agent",
                        run_id=run_id,
                    )
                )
            )
        return items

    def capture_approval_feedback(self, *, run_id: str | None, record: ApprovalRecord) -> list[FeedbackItem]:
        if not record.comments.strip():
            return []
        return [
            self.add_feedback(
                FeedbackItem(
                    feedback_id=f"fb-{uuid4().hex[:10]}",
                    source_type=FeedbackSourceType.APPROVAL,
                    source_artifact=record.final_path or record.draft_path or "",
                    part_number=record.part_number,
                    blog_slug=record.slug,
                    raw_feedback=record.comments,
                    normalized_issue_type=self.classify_feedback(record.comments),
                    severity=self.infer_severity(record.comments),
                    suggested_fix="Incorporate the human approval feedback before the next publish attempt.",
                    reviewer=record.reviewer_name,
                    run_id=run_id,
                )
            )
        ]

    def capture_manual_feedback(
        self,
        *,
        source_artifact: str,
        raw_feedback: str,
        normalized_issue_type: FeedbackType,
        severity: FeedbackSeverity,
        suggested_fix: str,
        reviewer: str,
        run_id: str | None = None,
        part_number: int | None = None,
        blog_slug: str | None = None,
    ) -> FeedbackItem:
        return self.add_feedback(
            FeedbackItem(
                feedback_id=f"fb-{uuid4().hex[:10]}",
                source_type=FeedbackSourceType.USER,
                source_artifact=source_artifact,
                part_number=part_number,
                blog_slug=blog_slug,
                raw_feedback=raw_feedback,
                normalized_issue_type=normalized_issue_type,
                severity=severity,
                suggested_fix=suggested_fix,
                reviewer=reviewer,
                run_id=run_id,
            )
        )

    def build_candidate_skills(
        self,
        *,
        topic: str,
        audience: str,
        config: SeriesRunConfig | None = None,
    ) -> MemoryUpdateResult:
        feedback_items = self.list_feedback()
        grouped: dict[str, list[FeedbackItem]] = defaultdict(list)
        for item in feedback_items:
            grouped[item.normalized_issue_type.value].append(item)

        with self._file_lock():
            existing_candidates = {skill.id: skill for skill in self.list_candidate_skills()}
            new_candidates: list[ReusableSkill] = []
            auto_approved_skill_ids: list[str] = []

            for issue_type, items in grouped.items():
                if len(items) < 3:
                    continue
                title, guidance_text, trigger_conditions = self._skill_blueprint(
                    issue_type=issue_type,
                    items=items,
                    topic=topic,
                    audience=audience,
                )
                skill_id = f"skill-{slugify(issue_type)}-{slugify(title)}"
                if skill_id in existing_candidates:
                    continue
                confidence = min(0.55 + 0.1 * len(items), 0.95)
                if confidence < 0.65:
                    continue
                skill = ReusableSkill(
                    id=skill_id,
                    title=title,
                    category=issue_type,
                    trigger_conditions=trigger_conditions,
                    guidance_text=guidance_text,
                    source_feedback_ids=[item.feedback_id for item in items],
                    confidence_score=confidence,
                    usage_count=0,
                    status=SkillStatus.CANDIDATE,
                    active=False,
                )
                existing_candidates[skill.id] = skill
                new_candidates.append(skill)

            self.persist_candidate_skills(list(existing_candidates.values()))

        for skill in new_candidates:
            if config and config.run_mode == RunMode.DEV and config.memory_auto_approve_in_dev:
                approved = self.approve_skill(skill.id)
                auto_approved_skill_ids.append(approved.id)

        return MemoryUpdateResult(
            feedback_items_logged=feedback_items,
            candidate_skills_created=new_candidates,
            auto_approved_skill_ids=auto_approved_skill_ids,
        )

    def approve_skill(self, skill_id: str) -> ReusableSkill:
        with self._file_lock():
            candidates = self.list_candidate_skills()
            approved = self.list_approved_skills()
            updated_candidates: list[ReusableSkill] = []
            selected: ReusableSkill | None = None
            for skill in candidates:
                if skill.id == skill_id:
                    selected = skill.model_copy(update={"status": SkillStatus.APPROVED, "active": True, "updated_at": datetime.now(timezone.utc)})
                else:
                    updated_candidates.append(skill)
            if selected is None:
                raise ValueError(f"Candidate skill not found: {skill_id}")
            approved = [skill for skill in approved if skill.id != skill_id] + [selected]
            self.persist_candidate_skills(updated_candidates)
            self.persist_approved_skills(approved)
            return selected

    def reject_skill(self, skill_id: str) -> ReusableSkill:
        with self._file_lock():
            candidates = self.list_candidate_skills()
            updated_candidates: list[ReusableSkill] = []
            selected: ReusableSkill | None = None
            for skill in candidates:
                if skill.id == skill_id:
                    selected = skill.model_copy(update={"status": SkillStatus.REJECTED, "active": False, "updated_at": datetime.now(timezone.utc)})
                    updated_candidates.append(selected)
                else:
                    updated_candidates.append(skill)
            if selected is None:
                raise ValueError(f"Candidate skill not found: {skill_id}")
            self.persist_candidate_skills(updated_candidates)
            return selected

    def retrieve_skills(self, query: SkillRetrievalQuery, *, record_usage: bool = True) -> SkillRetrievalResult:
        approved_skills = self.list_approved_skills()
        scored: list[tuple[int, ReusableSkill]] = []
        for skill in approved_skills:
            score = self._match_score(skill, query)
            if score > 0 and skill.active:
                scored.append((score, skill))
        scored.sort(key=lambda item: (-item[0], item[1].title))
        selected_skills = [skill for _, skill in scored[: query.max_skills]]
        if record_usage:
            for skill in selected_skills:
                skill.usage_count += 1
                skill.updated_at = datetime.now(timezone.utc)
            self.persist_approved_skills(approved_skills)
            self._append_retrieval_log(query, selected_skills)
        return SkillRetrievalResult(
            query=query,
            retrieved_skill_ids=[skill.id for skill in selected_skills],
            retrieved_guidance=[f"[{skill.id}] {skill.guidance_text}" for skill in selected_skills],
            retrieval_notes=[skill.title for skill in selected_skills],
        )

    def detect_repeated_patterns(self, feedback_items: list[FeedbackItem]) -> list[dict[str, object]]:
        counts = Counter(item.normalized_issue_type.value for item in feedback_items)
        return [
            {"issue_type": issue_type, "frequency": frequency}
            for issue_type, frequency in counts.items()
            if frequency > 1
        ]

    def recent_repeated_mistakes(self, limit: int = 3) -> list[str]:
        counts = Counter(item.normalized_issue_type.value for item in self.list_feedback())
        return [f"{issue_type} ({frequency}x)" for issue_type, frequency in counts.most_common(limit) if frequency > 1]

    @staticmethod
    def classify_feedback(text: str) -> FeedbackType:
        normalized = text.lower()
        if any(phrase in normalized for phrase in ("placeholder", "fake url", "example.com", "caption", "diagram", "visual", "image")):
            return FeedbackType.VISUAL_ISSUE
        if any(phrase in normalized for phrase in ("previous and next", "previous part", "next part", "continuity", "connect each part", "series callback", "overlap")):
            return FeedbackType.SERIES_CONTINUITY_ISSUE
        if any(phrase in normalized for phrase in ("mental model", "problem framing", "synthesis", "introduction", "section", "table of contents")):
            return FeedbackType.STRUCTURAL_ISSUE
        if "skill" in normalized and "violat" in normalized:
            return FeedbackType.SKILL_VIOLATION
        if "fresh" in normalized or "outdated" in normalized:
            return FeedbackType.FRESHNESS_ISSUE
        if "clar" in normalized or "confus" in normalized or "intro" in normalized or "explain" in normalized:
            return FeedbackType.CLARITY_ISSUE
        if "style" in normalized or "robotic" in normalized:
            return FeedbackType.STYLE_ISSUE
        if "tone" in normalized:
            return FeedbackType.TONE_ISSUE
        if "example" in normalized or "case study" in normalized:
            return FeedbackType.EXAMPLE_QUALITY_ISSUE
        if "citation" in normalized or "reference" in normalized:
            return FeedbackType.CITATION_ISSUE
        if "repeat" in normalized:
            return FeedbackType.REPETITION_ISSUE
        if "technical" in normalized or "accuracy" in normalized or "tradeoff" in normalized or "failure mode" in normalized:
            return FeedbackType.TECHNICAL_ISSUE
        return FeedbackType.STYLE_ISSUE

    @staticmethod
    def infer_severity(text: str) -> FeedbackSeverity:
        normalized = text.lower()
        if "critical" in normalized or "incorrect" in normalized or "broken" in normalized:
            return FeedbackSeverity.CRITICAL
        if "major" in normalized or "missing" in normalized or "must" in normalized:
            return FeedbackSeverity.HIGH
        if "minor" in normalized or "could" in normalized:
            return FeedbackSeverity.LOW
        return FeedbackSeverity.MEDIUM

    @staticmethod
    def _from_eval_severity(severity: EvaluationSeverity) -> FeedbackSeverity:
        return FeedbackSeverity(severity.value)

    @staticmethod
    def _skill_title(issue_type: str, suggested_fix: str) -> str:
        return f"Avoid {issue_type.replace('_', ' ')} by applying: {suggested_fix[:70]}"

    @staticmethod
    def _guidance_text(issue_type: str, suggested_fix: str) -> str:
        return f"When the content shows risk of {issue_type.replace('_', ' ')}, apply this guidance: {suggested_fix}"

    @classmethod
    def _skill_blueprint(
        cls,
        *,
        issue_type: str,
        items: list[FeedbackItem],
        topic: str,
        audience: str,
    ) -> tuple[str, str, SkillTriggerConditions]:
        combined = " ".join(item.raw_feedback.lower() for item in items)
        topic_keywords = cls._topic_keywords(topic)
        conditions = SkillTriggerConditions(
            topic_keywords=topic_keywords,
            audience_levels=[audience],
            issue_types=[issue_type],
            artifact_types=["draft", "review", "final"],
        )

        if issue_type == FeedbackType.VISUAL_ISSUE.value:
            title = "Use purposeful visuals instead of placeholders"
            guidance = (
                "When a section explains architecture, tradeoffs, or lifecycle flow, specify a concrete visual with "
                "placement, intent, and caption guidance. Never leave placeholder image URLs, captions, or example.com links."
            )
        elif issue_type == FeedbackType.SERIES_CONTINUITY_ISSUE.value:
            title = "Connect each part to the series journey"
            guidance = (
                "Explicitly connect the current part to the previous and next parts in the series so the article reads "
                "like a chapter in a book rather than a standalone post."
            )
        elif issue_type == FeedbackType.STRUCTURAL_ISSUE.value and "synthesis" in combined:
            title = "Add synthesis after dense enumerations"
            guidance = (
                "After dense lists, comparisons, or architecture walkthroughs, add a short synthesis paragraph that explains "
                "what matters, what to remember, and how the pieces relate."
            )
        elif issue_type == FeedbackType.STRUCTURAL_ISSUE.value and "mental model" in combined:
            title = "Place a mental model before deep architecture sections"
            guidance = (
                "Before detailed architecture or lifecycle sections, include a mental model that simplifies the system and "
                "gives the reader an intuition-first frame for the rest of the chapter."
            )
        elif issue_type == FeedbackType.CLARITY_ISSUE.value and any(
            phrase in combined for phrase in ("introduction", "intro", "opening", "definitions")
        ):
            title = "Open with a concrete problem before definitions"
            guidance = (
                "Start introductions with a relatable production problem or operating tension before formal definitions, "
                "then connect that setup to the system design concepts that follow."
            )
        elif issue_type == FeedbackType.CITATION_ISSUE.value:
            title = "Use concrete technical references"
            guidance = (
                "Prefer concrete engineering references with real URLs, docs, papers, or system write-ups over generic "
                "book-only references, especially for modern platform or production topics."
            )
        elif issue_type == FeedbackType.TECHNICAL_ISSUE.value:
            title = "Surface production tradeoffs and failure modes"
            guidance = (
                "For each major design choice, explain the operational tradeoffs, failure cases, and why a team would choose "
                "one approach over another in production."
            )
        elif issue_type == FeedbackType.EXAMPLE_QUALITY_ISSUE.value:
            title = "Ground concepts in concrete system examples"
            guidance = (
                "Each major concept should be anchored in at least one realistic system example, case study, or engineering "
                "scenario that shows how the idea changes design decisions."
            )
        else:
            title = cls._skill_title(issue_type, items[0].suggested_fix)
            guidance = cls._guidance_text(issue_type, items[0].suggested_fix)

        return title, guidance, conditions

    @staticmethod
    def _topic_keywords(topic: str) -> list[str]:
        keywords = {topic.lower()}
        for token in topic.lower().replace("/", " ").replace("-", " ").split():
            if len(token) > 2:
                keywords.add(token)
        return sorted(keywords)

    @staticmethod
    def _match_score(skill: ReusableSkill, query: SkillRetrievalQuery) -> int:
        score = 0
        conditions = skill.trigger_conditions
        if any(keyword in query.topic.lower() for keyword in conditions.topic_keywords):
            score += 3
        if query.audience in conditions.audience_levels:
            score += 2
        if query.part_number is not None and query.part_number in conditions.part_numbers:
            score += 2
        if query.blog_type in conditions.blog_types:
            score += 1
        if query.artifact_type in conditions.artifact_types:
            score += 2
        if set(query.issue_types).intersection(conditions.issue_types):
            score += 3
        return score

    def _append_retrieval_log(self, query: SkillRetrievalQuery, skills: list[ReusableSkill]) -> None:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query": query.model_dump(mode="json"),
            "retrieved_skill_ids": [skill.id for skill in skills],
        }
        with self.retrieval_log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")

    def _write_feedback_summary(self) -> None:
        feedback = self.list_feedback()
        lines = ["# Raw Feedback Log", ""]
        for item in feedback[-100:]:
            lines.extend(
                [
                    f"## {item.feedback_id}",
                    f"- **Type:** {item.normalized_issue_type}",
                    f"- **Severity:** {item.severity}",
                    f"- **Reviewer:** {item.reviewer}",
                    f"- **Artifact:** {item.source_artifact}",
                    f"- **Feedback:** {item.raw_feedback}",
                    f"- **Suggested Fix:** {item.suggested_fix}",
                    "",
                ]
            )
        self.raw_feedback_markdown_path.write_text("\n".join(lines), encoding="utf-8")
