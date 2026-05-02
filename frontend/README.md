# Agentic Blog Series UI

Next.js control-plane UI for the LangGraph + DeepAgents blog-series pipeline.

Live deployment: [ai-agent-blog-generator-app.vercel.app](https://ai-agent-blog-generator-app.vercel.app)

## Local Development

```bash
npm ci
npm run dev
```

Open `http://localhost:3000`.

The UI talks to the FastAPI service. Start the backend separately:

```bash
uv run python -m blog_series_agent api
```

Set the backend URL in the UI header or with:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## Vercel

Deploy this directory as the `ai-agent-blog-generator` Vercel project. Configure:

```bash
NEXT_PUBLIC_API_BASE_URL=https://your-fastapi-host.example.com
```

If you are using the local FastAPI service, keep the editable API URL field and point it at a reachable backend.
