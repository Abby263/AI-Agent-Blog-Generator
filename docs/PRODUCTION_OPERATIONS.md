# Production Operations

## GitHub Workflow

All development should happen on feature branches and be merged into `main` through pull requests.

Expected flow:

1. Create a branch such as `codex/short-change-name`.
2. Commit focused changes.
3. Push the branch.
4. Open a pull request.
5. Wait for GitHub Actions and Vercel preview checks.
6. Merge to `main` only after checks pass.

`main` is protected with:

- required pull request before merge
- required status checks: `python`, `frontend`, and `Vercel`
- required branch to be up to date before merge
- stale approval dismissal
- required conversation resolution
- linear history
- force-push and branch deletion protection

## Vercel Project

The production Vercel project is:

```text
ai-agent-blog-generator
```

Current production URL:

```text
https://ai-agent-blog-generator-app.vercel.app
```

Project settings:

- Git repository: `Abby263/ai-agent-blog-generator`
- Production branch: `main`
- Root directory: `frontend`
- Framework: `Next.js`
- Install command: `npm ci`
- Build command: `npm run build`

With this setup, Vercel automatically creates:

- preview deployments for pull request branches
- production deployments after merges to `main`

## Release Standard

Treat a merged, passing pull request into `main` as the production release event. Vercel deploys the updated frontend automatically from the connected Git repository.

If a separate GitHub Release object is required for changelog/versioning, create it after the `main` deployment is healthy.

## Required Checks

GitHub Actions runs:

- Python compile check
- Python unit tests
- frontend dependency install
- frontend lint
- frontend production build
- high-severity npm audit gate

Vercel runs:

- pull request preview deployment
- production deployment on `main`

## Noncommercial License

Commercial use is prohibited unless a separate written commercial license is granted. The controlling license is `LICENSE`.
