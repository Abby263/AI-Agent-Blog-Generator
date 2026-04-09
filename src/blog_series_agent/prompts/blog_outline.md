You are planning the table of contents for one chapter in a technical blog series.

Series topic: $topic
Audience: $audience
Part number: $part_number
Part title: $part_title
Target length: $min_words-$max_words
Part purpose:
$part_purpose
Prerequisite context:
$prerequisite_context
Key concepts that must appear:
$key_concepts
Recommended diagrams:
$recommended_diagrams
Dependencies on earlier parts:
$dependency_context
Series navigation:
$series_navigation

Research packet:
$research_summary

Retrieved approved skills:
$active_skills

Plan a chapter that feels like a book chapter, not a listicle.

You must produce:
- a strong subtitle
- a concise chapter_summary
- a previous_part_callback and next_part_teaser
- a section_plans list that covers the full article

Hard requirements for section_plans:
- Include these headings exactly once:
  - Introduction
  - Mental Model / Simplification Layer
  - Problem Framing
  - Detailed Core Sections
  - System / Architecture Thinking
  - Real-world Examples
  - Tradeoffs / Failure Cases
  - How This Works in Modern Systems
  - Synthesis / If You Step Back
  - Key Takeaways
  - Test Your Learning
  - Conclusion
  - References
- Each section must have a concrete purpose and 3-6 key points.
- Each section must have a realistic target_words value.
- The sum of target_words should meet or slightly exceed the minimum target length.
- For Detailed Core Sections, include 3-5 subsections that map to the actual concepts of this part.
- Mark requires_visual=true only when a visual would materially improve comprehension.
- Make this plan specific to the current part, not generic boilerplate.

Return only structured data matching the expected schema.
