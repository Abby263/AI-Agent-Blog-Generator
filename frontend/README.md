# Atlas — UI

Next.js 16 + React 19 control plane for the editorial agent pipeline.

Live deployment: [ai-agent-blog-generator-app.vercel.app](https://ai-agent-blog-generator-app.vercel.app)

## Local development

```bash
npm install
npm run dev                              # http://127.0.0.1:3000
```

Start the FastAPI backend separately:

```bash
uv run blog-series-agent api             # http://127.0.0.1:8000
```

The backend URL is editable on the **Settings** page (persisted to
`localStorage`); the build-time default is `NEXT_PUBLIC_API_BASE_URL`.

## Theming

Light, dark, and system are toggleable from the top header bar or Settings.
Preference is per-device and respects `prefers-color-scheme` when set to
*System*.

## Screenshots

Screenshots used in the root README are reproducible via Playwright:

```bash
# Backend on a free port
BLOG_SERIES_CORS_ORIGINS="*" uv run uvicorn blog_series_agent.api.app:app --port 8123 &

# Built UI
npm run build && PORT=4321 npm run start &

# Capture light + dark variants for every page
SCREENSHOT_API_BASE=http://127.0.0.1:8123 npm run screenshots
```

Output is written to `../docs/assets/`.

## Deploy

Configured for Vercel. Set:

```bash
NEXT_PUBLIC_API_BASE_URL=https://your-fastapi-host.example.com
```
