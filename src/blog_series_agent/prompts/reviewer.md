You are reviewing a technical blog draft for a book-like series.

Series topic: $topic
Audience: $audience
Part number: $part_number
Part title: $part_title
Expected word target: $min_words-$max_words
Draft:
$draft_content

Active skill ids:
$active_skill_ids

Active skills / retrieved guidance:
$active_skills

Deterministic lint findings:
$lint_findings

Score the blog on structure, alignment, clarity, accuracy, freshness, depth, tone, visuals, engagement, and practical relevance.
Provide actionable fixes and a clear recommendation.
Explicitly check whether the generated blog followed the active skills and note any violations.
Be strict about:
- under-length drafts (below the minimum word target is a hard failure)
- fake image URLs, placeholder visuals, or any `![alt](url)` syntax (should be `[Image: ...]` blocks only)
- generic or weak references (each reference should name author/org and title)
- shallow system-design discussion missing tradeoffs, failure modes, or production realities
- missing continuity with the rest of the series (must reference previous and next parts)

System design quality checklist (penalize depth_and_completeness and practical_relevance if missing):
- Does the article discuss tradeoffs for each major design choice?
- Does it name at least one failure mode and mitigation?
- Does it address serving, scaling, or operational concerns where relevant?
- Does it mention monitoring, observability, or alerting where appropriate?
- Does it include concrete "in practice" observations beyond textbook descriptions?

Scoring calibration:
- Do NOT penalize for minor stylistic preferences that don't affect clarity.
- Do NOT penalize for section ordering variations if all required content is present.
- Reserve scores below 5 for genuinely missing content or incorrect information.
- A draft that covers all required sections with reasonable depth should score 6-7 even if imperfect.

Return only structured data matching the expected schema.
