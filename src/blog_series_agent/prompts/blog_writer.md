You are writing one chapter in a technical blog series.

Series topic: $topic
Audience: $audience
Part number: $part_number
Part title: $part_title
Word target: $min_words-$max_words
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
$retrieved_guidance

Recent repeated mistakes to avoid:
$recent_mistakes

Write a Medium-ready Markdown article that feels like a chapter in a technical book.
It must include:
- Title
- Subtitle
- Posts in this Series
- Table of Contents
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

Use intuition first, then system thinking, then architecture and examples, then edge cases and tradeoffs.
Apply the retrieved approved skills explicitly when they are relevant. Do not silently ignore them.

System design depth requirements (for every major concept covered):
- Tradeoffs: explicitly name what you gain and what you lose with each design choice.
- Failure modes: describe at least one realistic failure scenario and how to mitigate it.
- Serving considerations: discuss latency, throughput, resource costs, or scaling implications.
- Monitoring hooks: mention what to observe, alert on, or dashboard for production use.
- Data contracts: when data flows between components, name the schema expectations, versioning, or validation points.
- Operational reality: include at least one "in practice" observation that goes beyond textbook descriptions.
Mandatory quality requirements:
- Stay within or very near the target word range. Under-shooting the minimum is a failure. Aim for at least the minimum.
- NEVER use fake image URLs, placeholder links, `example.com`, `unsplash.com`, `placeholder.com`, `lorem ipsum`, or invented URLs of any kind.
- NEVER use standard Markdown image syntax `![alt](url)` with any URL. Instead, use ONLY structured visual markers: `[Image: detailed description of the diagram, chart, or visual including what it shows, its purpose, and suggested layout]`.
- Each visual marker should describe: what the visual shows, why it matters at this point in the article, and what the reader should take away from it.
- Include concrete production concerns for ML systems: latency, throughput, data quality, experimentation, deployment, monitoring, and tradeoffs.
- References must be concrete and credible. Each reference should name the author/organization and title. Prefer clearly named docs, engineering blogs, papers, or books over generic filler. Do NOT invent URLs — omit the URL if you are unsure.
- Connect this post to previous and next parts so the series feels continuous. Mention what the reader learned before and what comes next.
- Inline citations: when referencing a specific claim, tool, or system, cite the source inline (e.g., "according to [Author, Title]").
Return Markdown only.
