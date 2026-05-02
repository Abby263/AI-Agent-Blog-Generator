You are researching one chapter in a technical blog series.

Series topic: $topic
Audience: $audience
Part number: $part_number
Part title: $part_title
Part purpose: $part_purpose
Series context:
$series_context

DeepAgent filesystem guidance:
$deepagent_guidance

Create targeted notes for a writer. Include examples, system design insights, and practical references that support deep technical writing.

Source-grounding requirements:
- Each practical_references entry must have a concrete title, source_type, and year where known.
- Prefer recent (last 3 years) engineering blogs, official documentation, or conference talks for production topics.
- Flag foundational references (textbooks, seminal papers) with recency="foundational".
- Set credibility to "primary", "practitioner", "secondary", or "unknown".
- Do NOT invent URLs. Omit the url field if you are not confident in the exact link.
- Populate freshness_notes listing areas where practices are rapidly changing or where the reader should verify current state.
- Populate citation_anchors with 3-5 specific claims or facts from the research that the writer should cite inline (e.g., "Netflix uses X for Y - cite Netflix tech blog 2023").

Return only structured data matching the expected schema.
