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

DeepAgent filesystem guidance:
$deepagent_guidance

Deterministic lint findings that must be fixed:
$lint_findings

Draft:
$draft_content

Revise the article into a final Medium-ready version while preserving depth and improving clarity, consistency, and flow.
Apply the retrieved approved skills explicitly and correct any violated skills.

Visual deduplication rules — MANDATORY:
- Scan the entire draft for `[Image: ...]` blocks. If two or more blocks describe the same visual (e.g., the same comparison table, the same architecture diagram), keep the FIRST occurrence only and DELETE all duplicates.
- A near-duplicate counts as a duplicate: "Comparison table of batch vs streaming" and "Comparison of Batch vs. Streaming Data Ingestion Methods" are the same image.
- After deduplication, verify every remaining `[Image: ...]` block teaches something distinct that is not taught by any other image block.
- Prefer real Markdown images when a verified image URL is available from the research packet or source material.
- Every real image must include a credit line in the form `_Image credit: [Credit Text](Credit URL)_`.
- Replace only fake or placeholder image URLs. Verified source images are allowed and preferred.

Content deduplication rules — MANDATORY:
- Scan the entire draft for repeated explanations of the same concept. If the same core comparison (e.g., batch vs. streaming tradeoffs) appears verbatim or near-verbatim in more than one section, consolidate it into the most appropriate section and remove the repetitions.
- The "Synthesis", "Key Takeaways", "Conclusion", and "Test Your Learning" sections must zoom out or help the reader APPLY the concept — they must NOT be rewrites of earlier sections. If they repeat prior content, replace the repetitive paragraphs with new insight, a zoomed-out perspective, or actionable guidance.
- If you catch phrases like "as mentioned above", "as we discussed", or "as highlighted earlier" followed by a restatement, DELETE the restatement and replace with new depth.

Reference cleanup rules — MANDATORY:
- Remove any reference with an obviously invented author name ("John Doe", "Jane Smith", "Smith, J.", "Doe, A.", etc.). If the source itself is real but the author name is uncertain, keep the source using only the organization name.
- Ensure each reference names a real organization or verifiable author. Acceptable: "Netflix Engineering Blog", "Apache Kafka Documentation", "Confluent Blog", "Uber Engineering", "Airbnb Engineering", "arXiv:XXXX.XXXXX".
- Do NOT invent URLs. If a URL cannot be verified, keep the reference but omit the URL field entirely.
- Inline citations should use: `(Organization, Title, Year)` or `[Author et al., Year]`.
- Every `Sources for This Section` block must use clickable Markdown links when a source URL exists.

Depth upgrade rules:
- If the draft is under target length, expand with: more architecture reasoning, concrete production examples (named companies, real tools, specific numbers), tradeoff analysis, failure mode discussion. Every added paragraph must contain substantive technical content, not filler.
- If any section is purely generic (could apply to any topic, not specifically to this one), rewrite it with topic-specific depth.
- Where examples mention "a company" or "an organization" without naming them, replace with a real named example if one exists in the research packet.
- Ensure implementation-heavy sections include at least one syntactically valid fenced code or config example.

If the draft is over the maximum, tighten verbose sections but do not cut substantive technical content.
Return Markdown only.
