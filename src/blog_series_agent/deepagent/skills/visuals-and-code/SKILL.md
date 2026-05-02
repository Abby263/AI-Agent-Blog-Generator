---
name: visuals-and-code
description: Add useful teaching visuals and working code/config examples.
stages:
  - section_research
  - draft
  - final
  - asset
  - review
---
# Visuals And Code Skill

## Visuals

- Prefer extracted source images when available from credible pages.
- Every embedded image must use Markdown image syntax and a nearby credit line:
  `_Image credit: [Source Name](https://source-url)_`
- If a real image URL is unavailable, use a specific `[Image: ...]` diagram spec
  that a designer can execute.
- Visuals should teach architecture, lifecycle, tradeoff, monitoring, or data
  flow concepts.

## Code

- Architecture-heavy sections need at least one fenced code/config block.
- Code must be syntactically valid for the declared language.
- Use implementation-oriented examples: deployment config, evaluation script,
  validation schema, monitoring rule, or routing policy.
- Explain what the code demonstrates after the block.
