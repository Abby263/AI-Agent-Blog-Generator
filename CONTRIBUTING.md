# Contributing

This repository is maintained with a production-style branch and pull request workflow.

## Development Workflow

- Do not commit directly to `main`.
- Create a short-lived branch for every change. Agent-authored branches should use `codex/<short-description>`.
- Keep each branch focused on one logical change.
- Open a pull request into `main`.
- Merge only after CI passes and the Vercel preview deployment is healthy.
- Prefer squash merges so `main` stays readable.
- Delete branches after merge.

## Required Local Checks

Run these before opening or merging a pull request:

```bash
uv run python -m compileall -q src tests
uv run pytest
cd frontend
npm ci
npm run lint
npm run build
npm audit --audit-level=high
```

## Release and Deployment Policy

`main` is the production branch.

The Vercel project `ai-agent-blog-generator` is connected to this GitHub repository. Pull requests create preview deployments, and merges to `main` create production deployments automatically.

The production URL is:

```text
https://ai-agent-blog-generator-app.vercel.app
```

## Licensing

This project is licensed for noncommercial use under the PolyForm Noncommercial License 1.0.0. Commercial use is not granted by the repository license. See `LICENSE`, `NOTICE`, `COMMERCIAL.md`, and `LICENSE_POLICY.md`.

Do not switch the repository to AGPL to enforce commercial restrictions. AGPL permits commercial use; this project intentionally uses a noncommercial source-available license.
