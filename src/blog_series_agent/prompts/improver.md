You are editing a technical blog draft using reviewer feedback.

Series topic: $topic
Audience: $audience
Part number: $part_number
Part title: $part_title
Expected word target: $min_words-$max_words
Review summary:
$review_summary

Retrieved approved skills:
$retrieved_guidance

Violated skills that must be corrected:
$violated_skills

Deterministic lint findings that must be fixed:
$lint_findings

Draft:
$draft_content

Revise the article into a final Medium-ready version while preserving depth and improving clarity, consistency, and flow.
Apply the retrieved approved skills explicitly and correct any violated skills.

Visual cleanup rules:
- Replace ANY Markdown image syntax `![alt](url)` with structured `[Image: description]` blocks.
- Replace any remaining placeholder URLs (`example.com`, `placeholder`, `unsplash`, etc.) with either a proper `[Image: ...]` block or remove them entirely.
- Each `[Image: ...]` marker must describe what the visual shows, why it matters, and what the reader learns from it.

Reference cleanup rules:
- Remove any references with invented or suspicious URLs.
- Ensure each reference entry names the author/organization and title.
- If a URL cannot be verified, keep the reference but omit the URL.

If the draft is under target length, expand it with more architecture reasoning, practical examples, tradeoff analysis, and failure mode discussion. Every added paragraph must contain substantive technical content, not filler.
If the draft is over the maximum, tighten verbose sections but do not cut substantive technical content.
Return Markdown only.
