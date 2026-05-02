# Security Policy

## Supported Versions

Security updates are applied to the current `main` branch.

## Reporting a Vulnerability

Do not open public issues for vulnerabilities that expose secrets, credentials, deployment tokens, API keys, or exploitable service behavior.

Report privately to the repository owner through GitHub or the project contact channel. Include:

- affected component
- reproduction steps
- expected impact
- relevant logs or screenshots with secrets redacted

## Secret Handling

- Never commit `.env`, `.env.*`, Vercel tokens, OpenAI keys, LangSmith keys, or deploy hook URLs.
- Use GitHub Actions secrets and Vercel environment variables for production credentials.
- Keep `.env.example` files placeholder-only.

## Deployment Protection

The public UI is intentionally accessible without Vercel SSO. Protect backend APIs separately if exposing a hosted FastAPI service.
