You are writing one section of a technical blog chapter.

Series topic: $topic
Audience: $audience
Part number: $part_number
Part title: $part_title
Part subtitle: $part_subtitle
Chapter summary:
$chapter_summary

Series continuity:
- Previous callback: $previous_part_callback
- Next teaser: $next_part_teaser

Series navigation:
$series_navigation

Section heading: $section_heading
Section purpose:
$section_purpose
Section key points:
$section_key_points
Suggested subsections:
$section_subsections
Target words for this section: $target_words
Hard maximum words for this section: $section_max_words
Requires purposeful visual: $visual_requirement

Completed sections so far:
$completed_sections

Research summary:
$research_summary

Section-supported points from research:
$supporting_points

Practical references:
$practical_references

Exact source links for this section:
$source_links

Citation anchors:
$citation_anchors

Retrieved approved skills:
$active_skills

Recent repeated mistakes to avoid:
$recent_mistakes

DeepAgent filesystem guidance:
$deepagent_guidance

Required section visual:
$visual_spec

Image URL to embed if available:
$image_url
Image credit URL:
$image_credit_url
Image credit text:
$image_credit_text
Image alt text:
$image_alt_text

Code example required:
$code_required
Suggested code example title:
$code_example_title
Suggested code example language:
$code_example_language
Suggested code example:
$code_example
Code example notes:
$code_example_notes

Write only the Markdown for this section.

Hard rules:
- Start with the section heading using Markdown heading syntax.
- Do not repeat the article title, subtitle, posts list, or table of contents.
- Stay close to the target word count for this section.
- Do not exceed the hard maximum word count for this section.
- Use concrete system-design reasoning, not generic filler.
- If the section is "Detailed Core Sections", use subsection headings for the planned subsections.
- If `image_url` is available, embed a real Markdown image using that exact URL.
- Every real image must be followed by an image credit line in this form: `_Image credit: [Credit Text](Credit URL)_`.
- If no image_url is available, use a fallback `[Image: ...]` marker.
- If referencing a concrete claim or system, cite inline using the source title or organization when possible.
- Keep continuity with previous and next parts when relevant.
- Avoid duplicating points already covered by earlier sections.
- End the section with a `#### Sources for This Section` block listing the concrete sources used in the section as clickable Markdown links.
- If `code_required` is Yes, include at least one fenced code block using the suggested language. The code must be syntactically valid and concrete, not pseudocode fragments.

Return Markdown only.
