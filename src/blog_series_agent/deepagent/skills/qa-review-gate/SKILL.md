---
name: qa-review-gate
description: Run a strict self-review before handing artifacts back to LangGraph.
stages:
  - review
  - final
  - asset
---
# QA Review Gate Skill

## Self-Review Checklist

Review the generated package as a strict editor before the final response.

- Structure: mandatory chapter sections are present and ordered coherently.
- Grounding: claims that depend on external facts have clickable source links.
- Depth: explanations include mental models, architecture reasoning, tradeoffs, and failure modes.
- Visuals: each section has either a real credited image, Mermaid diagram, chart/table idea, or precise generation spec.
- Code: implementation-heavy sections contain valid fenced code/config and explain what it demonstrates.
- Continuity: the chapter connects to the previous and next part in the series.
- Skills: active retrieved guidance was followed or violations are explicitly corrected.

## Fix Before Returning

If a checklist item fails, revise the files first. Do not merely mention the problem in the final response.
