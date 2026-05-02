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

Content uniqueness rules — STRICTLY ENFORCE:
- Every section must introduce information that is NOT already covered in any previous section of this article.
- Do NOT repeat the same concept, comparison, or takeaway across multiple sections. Each section earns its place by adding something new.
- The "Synthesis", "Key Takeaways", "Conclusion", and "Test Your Learning" sections must NOT restate the same comparison table, the same list of tradeoffs, or the same core points that were already covered — instead, zoom out, connect to the broader series, or push the reader toward applying the concept.
- If you catch yourself writing "as mentioned above" or "as we discussed", that is a red flag that you are repeating yourself — rewrite to add new depth instead.

Visual uniqueness rules — STRICTLY ENFORCE:
- Use real Markdown image syntax `![alt](url)` when a verified source image URL is available from research, and place a credit line immediately after it: `_Image credit: [Source Name](Source URL)_`.
- Use `[Image: detailed description]` only when no verified source image URL is available.
- Each `[Image: ...]` block in the article must be UNIQUE. Do NOT place a nearly identical or identical image description in more than one section.
- Use a maximum of ONE comparison table image. If you have already shown a batch vs. streaming table, do not show another one.
- Each visual must teach something NEW that words in the same section do not fully convey.
- Describe: what the visual shows, why it matters here, what the reader takes away.

Reference quality rules:
- References must name the real organization or author. NEVER invent an author name (e.g., "John Doe", "Jane Smith"). If you do not know the author, use just the organization name (e.g., "Netflix Engineering Blog", "Confluent Documentation").
- Prefer real, verifiable sources: engineering blogs from Airbnb, Netflix, Uber, Stripe, Meta, Google, Lyft; arXiv papers; official tool docs (Apache Kafka, Apache Flink, Great Expectations, dbt, MLflow).
- Do NOT invent URLs. Omit the URL entirely if you cannot verify it.
- Cite inline using the format: `(Organization/Author, Title, Year)` or `[Author et al., Year]`.

Depth and concreteness rules:
- Name REAL companies and REAL systems in examples: Netflix (Kafka, Flink, Mantis), Uber (Michelangelo), Airbnb (Zipline feature store), Lyft (Flyte), LinkedIn (Voldemort, Kafka origin), Twitter/X (real-time pipelines).
- Include at least one concrete number or benchmark per major section (e.g., "Kafka sustains >1 million messages/sec per broker", "Airbnb's Zipline serves features at p99 <10ms").
- Use specific tool names and explain WHY they are chosen, not just THAT they exist.
- Avoid generic prose like "this is important" or "plays a critical role" — state the specific mechanism or consequence instead.

Mandatory quality requirements:
- Stay within or very near the target word range. Under-shooting the minimum is a failure.
- NEVER use fake image URLs, `example.com`, `unsplash.com`, `placeholder.com`, or `lorem ipsum`.
- Every embedded real image must have a clickable image credit link.
- Include concrete production concerns: latency, throughput, data quality, experimentation, deployment, monitoring, tradeoffs.
- Connect this post to previous and next parts so the series feels continuous.

Return Markdown only.
