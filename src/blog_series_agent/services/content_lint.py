"""Deterministic content linting and review enrichment."""

from __future__ import annotations

import re

from ..config.settings import SeriesRunConfig
from ..schemas.evaluation import ContentLintFinding, ContentLintReport, EvaluationSeverity
from ..schemas.review import BlogReviewReport


class ContentLintService:
    """Finds deterministic content issues that the model often under-reports."""

    REQUIRED_SECTION_PATTERNS = [
        "posts in this series",
        "table of contents",
        "introduction",
        "mental model",
        "problem framing",
        "detailed core sections",
        "system / architecture thinking",
        "real-world examples",
        "tradeoffs / failure cases",
        "how this works in modern systems",
        "synthesis / if you step back",
        "key takeaways",
        "test your learning",
        "conclusion",
        "references",
    ]

    PLACEHOLDER_PATTERNS = [
        "example.com",
        "link-to-",
        "placeholder",
        "your-url-here",
        "insert-link",
        "todo:",
        "tbd",
        "lorem ipsum",
    ]

    FAKE_IMAGE_PATTERNS = [
        r"!\[.*?\]\(https?://.*?example\.com",
        r"!\[.*?\]\(https?://.*?placeholder",
        r"!\[.*?\]\(https?://via\.placeholder",
        r"!\[.*?\]\(https?://.*?unsplash\.com",
        r"!\[.*?\]\(https?://.*?picsum",
        r"!\[.*?\]\(https?://.*?lorempixel",
        r"!\[.*?\]\(https?://.*?dummyimage",
        r"!\[.*?\]\(https?://imgur\.com/[a-zA-Z0-9]+\)",
    ]

    def lint_markdown(self, markdown: str, config: SeriesRunConfig) -> ContentLintReport:
        lowered = markdown.lower()
        word_count = len(markdown.split())
        missing_sections = [section for section in self.REQUIRED_SECTION_PATTERNS if section not in lowered]
        placeholder_visuals = sorted({match for match in self.PLACEHOLDER_PATTERNS if match in lowered})

        # Detect fake image URLs via regex patterns
        fake_image_urls = self._detect_fake_image_urls(markdown)
        if fake_image_urls:
            placeholder_visuals = sorted(set(placeholder_visuals) | set(fake_image_urls))

        weak_references = self._weak_reference_findings(markdown)
        ungrouped_reference_issues = self._reference_quality_findings(markdown)

        findings: list[ContentLintFinding] = []
        if word_count < config.min_word_count:
            findings.append(
                ContentLintFinding(
                    finding_type="under_target_length",
                    severity=EvaluationSeverity.HIGH,
                    message=f"Article is {word_count} words, below the configured minimum of {config.min_word_count}.",
                    recommended_action="Expand the article with more systems detail, examples, and tradeoff analysis.",
                )
            )
        if missing_sections:
            findings.append(
                ContentLintFinding(
                    finding_type="missing_sections",
                    severity=EvaluationSeverity.HIGH,
                    message=f"Missing required sections: {', '.join(missing_sections)}.",
                    recommended_action="Add the missing required chapter sections explicitly.",
                )
            )
        if placeholder_visuals:
            findings.append(
                ContentLintFinding(
                    finding_type="placeholder_visuals",
                    severity=EvaluationSeverity.HIGH,
                    message=f"Found placeholder or fake visual markers: {', '.join(placeholder_visuals)}.",
                    recommended_action="Replace placeholder image links with explicit [Image: ...] descriptions or real artifact specs.",
                )
            )
        if weak_references:
            findings.append(
                ContentLintFinding(
                    finding_type="weak_references",
                    severity=EvaluationSeverity.MEDIUM,
                    message="References section appears weak, generic, or insufficiently technical.",
                    recommended_action="Add more concrete and current technical references or clearly label foundational sources.",
                )
            )
        if ungrouped_reference_issues:
            findings.append(
                ContentLintFinding(
                    finding_type="reference_quality",
                    severity=EvaluationSeverity.MEDIUM,
                    message=f"Reference quality issues: {'; '.join(ungrouped_reference_issues)}.",
                    recommended_action="Ensure references include titles, authors/orgs, and are verifiable. Remove invented URLs.",
                )
            )

        return ContentLintReport(
            word_count=word_count,
            missing_sections=missing_sections,
            placeholder_visuals=placeholder_visuals,
            weak_references=weak_references,
            findings=findings,
        )

    def validate_final_artifact(self, markdown: str, config: SeriesRunConfig) -> ContentLintReport:
        """Run a stricter validation pass on the final artifact (post-improvement)."""
        report = self.lint_markdown(markdown, config)
        lowered = markdown.lower()

        # Additional checks for final artifacts
        # Check that references section has real content
        ref_start = lowered.rfind("## references")
        if ref_start == -1:
            ref_start = lowered.rfind("# references")
        if ref_start != -1:
            ref_section = markdown[ref_start:]
            ref_lines = [line.strip() for line in ref_section.splitlines() if line.strip().startswith("- ")]
            if len(ref_lines) < 3:
                report.findings.append(
                    ContentLintFinding(
                        finding_type="insufficient_references",
                        severity=EvaluationSeverity.MEDIUM,
                        message=f"Final artifact has only {len(ref_lines)} reference entries. Minimum 3 expected.",
                        recommended_action="Add at least 3 concrete, named technical references.",
                    )
                )

        # Check for residual markdown image syntax that should have been replaced
        image_pattern = re.compile(r"!\[.*?\]\(https?://[^\)]+\)")
        image_matches = image_pattern.findall(markdown)
        if image_matches:
            report.findings.append(
                ContentLintFinding(
                    finding_type="residual_image_urls",
                    severity=EvaluationSeverity.HIGH,
                    message=f"Final artifact still contains {len(image_matches)} Markdown image URL(s). These should be [Image: ...] blocks.",
                    recommended_action="Replace all ![alt](url) patterns with [Image: description] blocks.",
                )
            )
            report.placeholder_visuals = sorted(set(report.placeholder_visuals) | {"residual markdown image URLs"})

        # Check that key sections have substantive content (not just headers)
        critical_sections = ["introduction", "key takeaways", "conclusion"]
        for section in critical_sections:
            idx = lowered.find(section)
            if idx != -1:
                # Check the content after the section header
                section_end = lowered.find("\n#", idx + len(section))
                if section_end == -1:
                    section_end = len(markdown)
                section_content = markdown[idx:section_end].strip()
                section_words = len(section_content.split())
                if section_words < 30:
                    report.findings.append(
                        ContentLintFinding(
                            finding_type="thin_section",
                            severity=EvaluationSeverity.MEDIUM,
                            message=f"Section '{section}' has only {section_words} words. It may be too thin.",
                            recommended_action=f"Expand the '{section}' section with more substantive content.",
                        )
                    )

        return report

    def lint_summary(self, report: ContentLintReport) -> str:
        if not report.findings:
            return "No deterministic lint issues were found."
        lines = [f"- {finding.finding_type}: {finding.message}" for finding in report.findings]
        return "\n".join(lines)

    def enrich_review_report(
        self,
        report: BlogReviewReport,
        lint_report: ContentLintReport,
        active_skill_ids: list[str],
        config: SeriesRunConfig,
    ) -> BlogReviewReport:
        issues = list(report.issues)
        priority_fixes = list(report.priority_fixes)
        suggested_additions = list(report.suggested_additions)
        strengths = list(report.strengths)
        scorecard = report.scorecard.model_copy()

        if active_skill_ids and not report.active_skills_checked:
            report.active_skills_checked = active_skill_ids
        if not active_skill_ids and not report.skill_adherence_notes:
            report.skill_adherence_notes = ["No active approved skills were provided for this run."]

        for finding in lint_report.findings:
            issues.append(f"[Lint] {finding.message}")
            priority_fixes.append(finding.recommended_action)

        if lint_report.word_count:
            strengths.append(f"Draft length: {lint_report.word_count} words")

        # Calibrated penalties: avoid over-penalizing near-misses and stylistic issues.
        # Reserve large penalties for genuinely missing content, not minor shortfalls.
        deficit = max(0, config.min_word_count - lint_report.word_count)
        deficit_pct = deficit / max(config.min_word_count, 1)
        if deficit_pct >= 0.3:  # More than 30% under target
            scorecard.depth_and_completeness = max(0, scorecard.depth_and_completeness - 3)
            scorecard.engagement_and_learning_reinforcement = max(
                0, scorecard.engagement_and_learning_reinforcement - 1
            )
        elif deficit_pct >= 0.15:  # 15-30% under target
            scorecard.depth_and_completeness = max(0, scorecard.depth_and_completeness - 2)
        elif deficit > 0:  # Slightly under target
            scorecard.depth_and_completeness = max(0, scorecard.depth_and_completeness - 1)

        if lint_report.missing_sections:
            # Scale penalty by how many sections are missing relative to total
            missing_ratio = len(lint_report.missing_sections) / len(self.REQUIRED_SECTION_PATTERNS)
            if missing_ratio >= 0.3:
                scorecard.structure_consistency = max(0, scorecard.structure_consistency - 2)
                scorecard.series_alignment = max(0, scorecard.series_alignment - 1)
            elif missing_ratio >= 0.1:
                scorecard.structure_consistency = max(0, scorecard.structure_consistency - 1)
            # Don't penalize series_alignment for 1-2 missing sections - they may just be named differently

        if lint_report.placeholder_visuals:
            scorecard.visuals_and_examples = max(0, scorecard.visuals_and_examples - 2)
            suggested_additions.append("Replace placeholder/fake image URLs with explicit diagram specs.")

        if lint_report.weak_references:
            # Only penalize if multiple weak reference indicators are present
            if len(lint_report.weak_references) >= 2:
                scorecard.technical_freshness = max(0, scorecard.technical_freshness - 1)
                scorecard.practical_relevance = max(0, scorecard.practical_relevance - 1)
            else:
                scorecard.practical_relevance = max(0, scorecard.practical_relevance - 1)

        report.issues = list(dict.fromkeys(issues))
        report.priority_fixes = list(dict.fromkeys(priority_fixes))
        report.suggested_additions = list(dict.fromkeys(suggested_additions))
        report.strengths = list(dict.fromkeys(strengths))
        report.scorecard = scorecard
        return report

    def _detect_fake_image_urls(self, markdown: str) -> list[str]:
        """Detect fake image URLs using regex patterns."""
        found: list[str] = []
        for pattern in self.FAKE_IMAGE_PATTERNS:
            if re.search(pattern, markdown, re.IGNORECASE):
                found.append(f"fake image URL matching {pattern[:40]}")
        # Also detect bare markdown images pointing to suspicious domains
        for match in re.finditer(r"!\[.*?\]\((https?://[^\)]+)\)", markdown):
            url = match.group(1).lower()
            if any(domain in url for domain in ("placeholder", "example.com", "lorempixel", "dummyimage", "picsum")):
                found.append(f"suspicious image URL: {match.group(1)[:60]}")
        return found

    @staticmethod
    def _reference_quality_findings(markdown: str) -> list[str]:
        """Check reference entries for quality: named sources, no invented URLs."""
        issues: list[str] = []
        lower = markdown.lower()
        ref_start = lower.rfind("## references")
        if ref_start == -1:
            ref_start = lower.rfind("# references")
        if ref_start == -1:
            return []
        ref_section = markdown[ref_start:]
        ref_lines = [line.strip() for line in ref_section.splitlines() if line.strip().startswith("- ")]
        # Check for vague references with no author/org/title
        vague_count = 0
        for line in ref_lines:
            # A good reference should have at least a proper name or title
            if len(line) < 20 or line.count(" ") < 3:
                vague_count += 1
        if vague_count > len(ref_lines) // 2 and ref_lines:
            issues.append(f"{vague_count}/{len(ref_lines)} references appear too vague or short")
        # Check for generic filler references
        generic_markers = ["various sources", "multiple articles", "online resources", "see also"]
        for marker in generic_markers:
            if marker in lower[ref_start:]:
                issues.append(f"generic reference filler detected: '{marker}'")
        return issues

    @staticmethod
    def _weak_reference_findings(markdown: str) -> list[str]:
        lower = markdown.lower()
        if "references" not in lower:
            return ["No references section found."]
        reference_lines = [line.strip() for line in markdown.splitlines() if line.strip().startswith("- ")]
        weak: list[str] = []
        if len(reference_lines) < 3:
            weak.append("Too few reference entries.")
        if not any(("http" in line or "www." in line) for line in reference_lines):
            weak.append("No linked implementation references detected.")
        if re.search(r"example\.com|link-to-", lower):
            weak.append("Placeholder references or URLs detected.")
        return weak
