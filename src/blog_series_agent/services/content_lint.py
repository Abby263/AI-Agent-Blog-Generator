"""Deterministic content linting and review enrichment."""

from __future__ import annotations

import ast
import json
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

        unresolved_image_blocks = self._detect_unresolved_image_blocks(markdown)

        # Detect fake image URLs via regex patterns
        fake_image_urls = self._detect_fake_image_urls(markdown)
        if fake_image_urls:
            placeholder_visuals = sorted(set(placeholder_visuals) | set(fake_image_urls))
        if unresolved_image_blocks:
            placeholder_visuals = sorted(set(placeholder_visuals) | set(unresolved_image_blocks))

        weak_references = self._weak_reference_findings(markdown)
        ungrouped_reference_issues = self._reference_quality_findings(markdown)
        duplicate_images = self._detect_duplicate_image_blocks(markdown)
        fake_authors = self._detect_fake_authors(markdown)
        image_credit_issues = self._image_credit_issues(markdown)
        code_issues = self._code_block_issues(markdown)

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
        if duplicate_images:
            findings.append(
                ContentLintFinding(
                    finding_type="duplicate_image_blocks",
                    severity=EvaluationSeverity.MEDIUM,
                    message=f"Found {len(duplicate_images)} duplicate or near-duplicate [Image: ...] block(s). Each visual must be unique.",
                    recommended_action="Remove duplicate [Image: ...] blocks. Each section must have a distinct visual, or no visual at all.",
                )
            )
        if fake_authors:
            findings.append(
                ContentLintFinding(
                    finding_type="fake_author_names",
                    severity=EvaluationSeverity.HIGH,
                    message=f"References contain likely invented author names: {', '.join(fake_authors[:5])}.",
                    recommended_action="Replace invented author names with real organization names (e.g., 'Netflix Engineering Blog') or remove the reference.",
                )
            )
        if image_credit_issues:
            findings.append(
                ContentLintFinding(
                    finding_type="missing_image_credits",
                    severity=EvaluationSeverity.HIGH,
                    message=f"Found image credit issues: {'; '.join(image_credit_issues)}.",
                    recommended_action="Every embedded image must include a clickable image credit line.",
                )
            )
        if code_issues:
            findings.append(
                ContentLintFinding(
                    finding_type="code_example_issues",
                    severity=EvaluationSeverity.MEDIUM,
                    message=f"Code example issues: {'; '.join(code_issues)}.",
                    recommended_action="Add syntactically valid, runnable code/config examples to implementation-heavy sections.",
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

        # Check for unresolved placeholder image blocks in final artifacts
        unresolved_images = self._detect_unresolved_image_blocks(markdown)
        if unresolved_images:
            report.findings.append(
                ContentLintFinding(
                    finding_type="unresolved_image_placeholders",
                    severity=EvaluationSeverity.HIGH,
                    message=f"Final artifact still contains placeholder image blocks: {', '.join(unresolved_images)}.",
                    recommended_action="Replace placeholder image blocks with real source images plus credit lines, or provide a much more specific asset spec.",
                )
            )
            report.placeholder_visuals = sorted(set(report.placeholder_visuals) | set(unresolved_images))

        image_credit_issues = self._image_credit_issues(markdown)
        if image_credit_issues:
            report.findings.append(
                ContentLintFinding(
                    finding_type="missing_image_credits",
                    severity=EvaluationSeverity.HIGH,
                    message=f"Embedded image credit issues: {'; '.join(image_credit_issues)}.",
                    recommended_action="Add a clickable image credit line for every embedded image.",
                )
            )

        # Check that key sections have substantive content (not just headers).
        # Only look for the section at actual heading markers (lines starting with #), not in TOC.
        critical_sections = ["introduction", "key takeaways", "conclusion"]
        for section in critical_sections:
            # Find a line that starts with # and contains the section name — skip TOC entries
            heading_match = re.search(
                r"^#{1,3}\s+" + re.escape(section),
                lowered,
                re.MULTILINE,
            )
            if heading_match is None:
                continue
            idx = heading_match.start()
            # Find end: next heading of same or higher level
            section_end = re.search(r"^#{1,3}\s+", lowered[idx + 1:], re.MULTILINE)
            end_pos = (idx + 1 + section_end.start()) if section_end else len(markdown)
            section_content = markdown[idx:end_pos].strip()
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

    @staticmethod
    def _detect_duplicate_image_blocks(markdown: str) -> list[str]:
        """Find [Image: ...] blocks with near-identical descriptions (deduplication signal)."""
        import re as _re
        blocks = _re.findall(r"\[Image:\s*([^\]]+)\]", markdown, _re.IGNORECASE)
        if len(blocks) <= 1:
            return []

        def _normalise(s: str) -> str:
            # Lower-case, strip punctuation, collapse whitespace
            s = s.lower()
            s = _re.sub(r"[^a-z0-9\s]", " ", s)
            return " ".join(s.split())

        seen: list[str] = []
        duplicates: list[str] = []
        for block in blocks:
            norm = _normalise(block)
            # Check if this block is substantially similar to any we have already seen
            for prior in seen:
                # Jaccard similarity on word sets
                a = set(norm.split())
                b = set(prior.split())
                if not a or not b:
                    continue
                jaccard = len(a & b) / len(a | b)
                if jaccard >= 0.6:  # 60%+ word overlap → near-duplicate
                    duplicates.append(block[:80])
                    break
            else:
                seen.append(norm)
        return duplicates

    @staticmethod
    def _detect_unresolved_image_blocks(markdown: str) -> list[str]:
        blocks = re.findall(r"\[Image:\s*([^\]]+)\]", markdown, re.IGNORECASE)
        return [block[:80] for block in blocks]

    @staticmethod
    def _image_credit_issues(markdown: str) -> list[str]:
        issues: list[str] = []
        lines = markdown.splitlines()
        image_pattern = re.compile(r"!\[[^\]]*\]\((https?://[^\)]+)\)")
        for index, line in enumerate(lines):
            if image_pattern.search(line) is None:
                continue
            window = "\n".join(lines[index + 1:index + 4])
            if re.search(r"_Image credit:\s+\[[^\]]+\]\((https?://[^\)]+)\)_", window) is None:
                issues.append(f"embedded image on line {index + 1} is missing a clickable credit line")
        return issues

    def _code_block_issues(self, markdown: str) -> list[str]:
        issues: list[str] = []
        code_blocks = self._extract_code_blocks(markdown)
        implementation_sections = [
            "detailed core sections",
            "system / architecture thinking",
            "how this works in modern systems",
            "real-world examples",
        ]
        lowered = markdown.lower()
        if any(section in lowered for section in implementation_sections) and not code_blocks:
            issues.append("implementation-heavy article has no fenced code/config example")
            return issues

        for language, code in code_blocks:
            lang = (language or "").strip().lower()
            stripped = code.strip()
            if not stripped:
                issues.append("empty fenced code block detected")
                continue
            if lang in {"python", "py"}:
                try:
                    ast.parse(stripped)
                except SyntaxError as exc:
                    issues.append(f"python code block has syntax error: {exc.msg}")
            elif lang == "json":
                try:
                    json.loads(stripped)
                except json.JSONDecodeError as exc:
                    issues.append(f"json code block is invalid: {exc.msg}")
            elif lang in {"yaml", "yml"}:
                try:
                    import yaml

                    yaml.safe_load(stripped)
                except Exception as exc:  # noqa: BLE001
                    issues.append(f"yaml code block is invalid: {exc}")
        return issues

    @staticmethod
    def _extract_code_blocks(markdown: str) -> list[tuple[str, str]]:
        return re.findall(r"```([a-zA-Z0-9_-]*)\n(.*?)```", markdown, re.DOTALL)

    # Known placeholder / generic first-name+last-name patterns used by LLMs when fabricating references
    _FAKE_AUTHOR_RE = re.compile(
        r"\b(john doe|jane doe|jane smith|john smith|"
        r"smith,\s*j\.|doe,\s*a\.|johnson,\s*l\.|brown,\s*r\.|harris,\s*j\.|"
        r"gonzalez,\s*[a-z]\.|cheng,\s*a\.|lee,\s*a\.|jones,\s*r\.)\b",
        re.IGNORECASE,
    )

    @classmethod
    def _detect_fake_authors(cls, markdown: str) -> list[str]:
        """Return a list of likely-fabricated author strings found in the references section."""
        lower = markdown.lower()
        ref_start = lower.rfind("# references")
        if ref_start == -1:
            ref_start = lower.rfind("## references")
        search_zone = markdown[ref_start:] if ref_start != -1 else markdown
        matches = cls._FAKE_AUTHOR_RE.findall(search_zone)
        # De-duplicate, preserve order
        seen: set[str] = set()
        result: list[str] = []
        for m in matches:
            key = m.lower()
            if key not in seen:
                seen.add(key)
                result.append(m)
        return result

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
