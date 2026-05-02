You are improving one section of a technical blog chapter.

Series topic: $topic
Audience: $audience
Part number: $part_number
Part title: $part_title
Expected article word target: $min_words-$max_words

Section heading: $section_heading
Section purpose:
$section_purpose
Section target words: $section_target_words
Section visual requirement:
$visual_spec

Section-level research summary:
$section_research_summary

Section-level sources:
$section_sources

Source links for this section:
$source_links

Retrieved approved skills:
$retrieved_guidance

Violated skills that must be corrected:
$violated_skills

DeepAgent filesystem guidance:
$deepagent_guidance

Review summary:
$review_summary

Deterministic lint findings:
$lint_findings

Approval comments:
$approval_comments

Draft section:
$draft_section

Revise only this section.

Hard rules:
- Start with the same section heading in Markdown.
- Keep the substance technically grounded in the listed section sources.
- If a concrete image URL is available, embed it with standard Markdown image syntax and add a credit line: `_Image credit: [Credit Text](Credit URL)_`.
- If no concrete image URL is available, include one purposeful `[Image: ...]` block in this section.
- End with a `#### Sources for This Section` block listing the sources used in this section as clickable Markdown links.
- Preserve or add a syntactically valid fenced code block when the section is implementation-heavy.
- Remove placeholder URLs, fake image links, and generic filler.
- Improve clarity, continuity, tradeoff reasoning, and practical relevance without collapsing nuance.

Return Markdown only.
