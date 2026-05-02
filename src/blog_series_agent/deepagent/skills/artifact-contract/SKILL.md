---
name: artifact-contract
description: Enforce the exact workspace files and machine-readable manifest expected by the LangGraph pipeline.
stages:
  - research
  - plan
  - draft
  - asset
  - review
---
# Artifact Contract Skill

## Required Files

Write these files at the workspace root. Do not bury them in subdirectories.

- `research.md`
- `plan.md`
- `draft.md`
- `assets.md`
- `manifest.json`

## Manifest Contract

`manifest.json` must be valid JSON and include:

- `source_urls`: list of exact source links used in the article.
- `image_urls`: list of image URLs embedded or considered.
- `sections`: list of section names in `draft.md`.
- `active_skill_ids`: list of retrieved skill IDs passed in the task.
- `missing_evidence`: list of any sections that could not be grounded.

## Validation Before Final Answer

Before finishing, inspect your own files and verify:

- Every URL in `draft.md` is also represented in `manifest.json`.
- Every substantial section has `#### Sources for This Section`.
- Every embedded Markdown image has a nearby `_Image credit: [name](url)_`.
- `draft.md` contains no `example.com`, fake placeholder image captions, or internal failure notes.
