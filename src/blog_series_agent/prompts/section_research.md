You are preparing section-level research for one section of a technical blog chapter.

Series topic: $topic
Audience: $audience
Part number: $part_number
Part title: $part_title
Chapter summary:
$chapter_summary

Section heading: $section_heading
Section purpose:
$section_purpose
Section key points:
$section_key_points
Suggested subsections:
$section_subsections
Section requires visual: $section_requires_visual

Part-level research summary:
$blog_research_summary

Candidate references from part-level research:
$blog_references

Citation anchors:
$citation_anchors

DeepAgent filesystem guidance:
$deepagent_guidance

Return structured output matching the schema.

Hard rules:
- Produce research that is SPECIFIC to this section only — do not repeat generic chapter-level background that will already appear in other sections.
- Include at least 2 source notes. Every source note must include the EXACT source URL when available so the final blog can render a clickable link.
- Source notes must name the REAL organization or author — NEVER invent names like "John Doe" or "Jane Smith". If the exact author is unknown, use the organization name (e.g., "Netflix Engineering Blog", "Apache Kafka Documentation", "Uber Engineering Blog").
- Prefer credible sources: engineering blogs (Netflix, Uber, Airbnb, Stripe, Meta, Google, Lyft, LinkedIn), arXiv papers, official tool documentation (Apache, Confluent, MLflow, dbt, Great Expectations, Feast, Tecton), conference papers (NeurIPS, ICML, VLDB, SIGMOD, SysML).
- The visual spec must describe ONE concrete, unique visual: architecture diagram, comparison table, workflow chart, or decision tree. It must explain what the visual teaches and why it belongs in this section specifically.
- The visual spec must NOT be a generic "comparison table of X vs Y" that could apply to the whole chapter — it must be specific to this section's angle.
- If the evidence includes a usable image, populate `image_url`, `image_credit_url`, `image_credit_text`, and `image_alt_text`. Use the exact image URL if available; use the page URL as the credit link when the image asset itself has no separate credit page.
- Supporting points must be SPECIFIC and CONCRETE:
  - Include at least one real company name and how they solve this problem (e.g., "Netflix uses Kafka with consumer groups for exactly-once delivery").
  - Include at least one specific metric or benchmark (e.g., "Kafka sustains >1M msgs/sec per broker; Flink achieves sub-second latency at petabyte scale").
  - Include at least one failure mode or operational pitfall specific to this section's topic.
- Do NOT write generic observations like "data quality is important" — name the specific mechanism, tool, or architectural decision that enforces it.
- The research_summary field must be written so the blog writer can directly use it to write a substantive, technically precise section — not as a vague outline.
- When the section is implementation-heavy (for example: Detailed Core Sections, System / Architecture Thinking, How This Works in Modern Systems, or Real-world Examples), provide one ORIGINAL runnable or syntactically valid code/config example via `code_example`, plus `code_example_language`, `code_example_title`, and `code_example_notes`.
