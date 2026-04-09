You are analyzing normalized feedback events from a technical content pipeline.

Normalized feedback:
$normalized_feedback

Group repeated issues into reusable, auditable writing skills.

For each proposed skill:
- make the guidance reusable across future generations
- keep it specific enough to improve writing quality
- include trigger conditions
- tie it back to the source feedback ids
- prefer guidance that a reviewer can verify later
- set confidence_score between 0.65 and 0.95 based on how clear and actionable the pattern is

Quality filter - do NOT create skills for:
- One-off feedback items that appeared only once
- Vague or generic guidance like "improve quality" or "make it better"
- Feedback about typos, formatting, or trivial stylistic preferences
- Issues that are already covered by existing skills in the candidate list

Each skill's guidance_text should be concrete enough that a writer can apply it without further interpretation. Bad: "Improve references." Good: "Each reference must name the author or organization, include the title, and specify the year. Omit URLs if not verifiable."

Return only structured reusable skill objects.
