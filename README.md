# Blog Series Agent

`blog-series-agent` is a production-oriented starter repository for generating long-form technical blog series with a LangGraph workflow. It produces book-like Medium articles that move from fundamentals to production realities, adds a formal human approval gate, evaluates outputs systematically, and learns from repeated feedback through explicit reusable guidance.

The system accepts a request such as:

```bash
uv run python -m blog_series_agent run --topic "ML System Design" --audience intermediate --parts 12 --use-memory true
```

and produces:

- a full series outline
- one draft Markdown file per blog
- research notes per blog
- reviewer reports in JSON and Markdown
- improved final Markdown files
- asset planning specs
- blog / series / run evaluations
- approval records
- raw feedback logs
- candidate and approved reusable skills
- run manifests for status tracking and inspection

## Architecture

The repository uses two LangGraph workflows plus service-level evaluation and memory layers:

- `outline graph`: topic research -> series architect
- `blog graph`: blog research -> retrieve approved skills -> writer -> reviewer -> improver -> asset planner -> evaluation -> memory update -> approval

The outer service layer orchestrates:

- run manifests and artifact persistence
- series-level and run-level evaluation
- raw feedback capture
- candidate skill extraction
- approved skill retrieval
- optional LangSmith tracing

## Why LangGraph

LangGraph is used for the stateful parts of the workflow where routing matters:

- optional review and improvement stages
- optional evaluation and memory update stages
- approval-required gating in production mode
- routing back to improvement when human reviewers request changes
- explicit per-part workflow state including retrieved skills and evaluation results

The service layer handles run manifests, disk persistence, cross-part aggregation, API/dashboard integration, and auditable memory retrieval.

## Blog Authoring Flow

Each blog is now generated in three explicit stages:

- series architect decides the ordered list of blog chapters
- per-blog chapter planner creates a `blog_plans/Part-X-...-plan.{json,md}` artifact with the table of contents and section targets
- section writer makes multiple LLM calls, one per planned section, before assembling the full Markdown article

This keeps generation inspectable and makes it easier to enforce chapter structure and minimum article length.

## Deterministic Quality Gates

The repo now includes a deterministic content-lint layer that runs alongside model-based review.

It checks for:

- under-target word count
- missing mandatory chapter sections
- placeholder or fake visual markers such as `example.com` links
- weak references

These findings are passed explicitly into the reviewer and improver prompts, persisted into blog evaluations, and surfaced in score penalties so the system does not over-credit shallow but well-formatted drafts.

## Evaluation Architecture

The evaluation layer is separate from approval and memory.

It produces:

- blog-level evaluation under `outputs/evaluations/blog/`
- series-level evaluation under `outputs/evaluations/series/`
- run-level evaluation under `outputs/evaluations/runs/`

Implemented models include:

- `CriterionScore`
- `BlogEvaluation`
- `SeriesEvaluation`
- `RunEvaluation`
- `EvaluationIssue`
- `EvaluationTrend`
- `RepeatedFailurePattern`
- `ImprovementOpportunity`

Blog evaluation covers:

- structure consistency
- series alignment
- clarity of explanation
- technical accuracy
- technical freshness
- depth and completeness
- readability and tone
- visuals and examples
- engagement and learning reinforcement
- practical relevance
- active skill adherence

Series evaluation checks:

- progression quality
- topic overlap
- continuity between parts
- tone and structure consistency
- coverage gaps

Run evaluation checks:

- number of blogs completed
- average review scores
- approval outcomes
- repeated issue patterns
- retry and revision load signals

## Outline Reuse

Single-blog reruns now reuse the latest matching outline for the same topic, audience, and part count instead of silently regenerating a different table of contents each time.

This keeps:

- part numbers stable across review loops
- approval records tied to the same artifact identity
- human feedback actionable on rerun

## Approval History vs Memory

These are intentionally separate.

Approval history is release-oriented:

- stored under `outputs/approval/`
- answers whether a specific artifact is publish-ready
- includes reviewer identity, decision, comments, and timestamps

Memory is learning-oriented:

- stored under `data/memory/`
- exists to improve future generations
- is never treated as approval state
- must remain inspectable and auditable

The repository does **not** merge approval records and learned memory into one concept or one store.

## Memory Architecture

The implemented learning loop uses two explicit memory layers plus a candidate-skill approval buffer:

### 1. Raw feedback log

Source of truth for learning inputs:

- `data/memory/raw_feedback_log.jsonl`
- `data/memory/raw_feedback_log.md`

Each entry includes:

- `feedback_id`
- `source_type`
- `source_artifact`
- `part_number`
- `blog_slug`
- `raw_feedback`
- `normalized_issue_type`
- `severity`
- `suggested_fix`
- `reviewer`
- `timestamp`

### 2. Approved reusable skills

Only approved reusable guidance influences future runs by default:

- `data/memory/approved_skills.json`
- `data/memory/approved_skills.md`

Each approved skill includes:

- `id`
- `title`
- `category`
- `trigger_conditions`
- `guidance_text`
- `source_feedback_ids`
- `confidence_score`
- `usage_count`
- `status`
- `active`
- `created_at`
- `updated_at`

### Candidate-skill approval buffer

Candidate skills are staged separately before promotion:

- `data/memory/skill_candidates.json`

This is not treated as the active memory layer. It is a review buffer for human control.

## Raw Feedback Lifecycle

Feedback is captured from:

- reviewer outputs
- evaluation issues
- approval comments
- explicit user/API/CLI submissions

The system normalizes comments into structured feedback items. Repeated patterns are then grouped into candidate reusable skills. Candidate skills can be approved into the active reusable skill store or rejected and kept inactive.

Example raw feedback entry:

```json
{
  "feedback_id": "fb-1234abcd",
  "source_type": "reviewer",
  "source_artifact": "outputs/reviews/Part-1-introduction-review.md",
  "part_number": 1,
  "blog_slug": "introduction",
  "raw_feedback": "The introduction jumps into definitions before the real-world problem.",
  "normalized_issue_type": "clarity_issue",
  "severity": "medium",
  "suggested_fix": "Open with a concrete real-world problem before definitions.",
  "reviewer": "reviewer-agent"
}
```

## Approved Skill Lifecycle

1. Feedback enters the raw feedback log.
2. `memory build` groups repeated issues into candidate skills.
3. A human approves or rejects each candidate skill.
4. Only approved active skills are stored in `approved_skills.json`.
5. Future runs retrieve only relevant approved skills.

Example approved skill entry:

```json
{
  "id": "skill-clarity-open-with-problem",
  "title": "Lead introductions with a concrete problem",
  "category": "clarity_issue",
  "trigger_conditions": {
    "topic_keywords": ["ml system design"],
    "audience_levels": ["intermediate"],
    "artifact_types": ["draft", "review", "final"],
    "issue_types": ["clarity_issue"]
  },
  "guidance_text": "When opening a chapter, begin with a relatable production problem before defining the concept.",
  "source_feedback_ids": ["fb-1234abcd", "fb-5678efgh"],
  "confidence_score": 0.75,
  "usage_count": 3,
  "status": "approved",
  "active": true
}
```

## Explicit Guidance Retrieval

Memory is retrieved guidance, not hidden prompt mutation.

Before writing, reviewing, and improving a blog, the system retrieves only relevant approved skills based on:

- topic
- audience
- part number
- artifact type
- known issue categories where applicable

The retrieved guidance is passed explicitly into prompts as named inputs:

- `retrieved_guidance`
- `active_skills`
- `recent_mistakes`
- `violated_skills`

Example retrieved guidance passed to a run:

```text
Retrieved approved skills:
- [skill-clarity-open-with-problem] When opening a chapter, begin with a relatable production problem before defining the concept.
- [skill-series-bridge] Explicitly connect each post to the previous and next part in the series.
```

This is logged and inspectable through:

- run artifacts
- retrieval preview endpoints and CLI
- `data/memory/retrieval_log.jsonl`
- LangSmith metadata when enabled

## Reviewer Skill-Adherence Checks

The reviewer does not only score the article itself. It also checks:

- which active skills were provided
- which skills were followed
- which skills were violated
- a `skill_adherence_score`
- explanatory `skill_adherence_notes`

These are stored in both review and evaluation outputs.

## LangSmith Integration

LangSmith is optional.

Enable it through config or environment:

- `BLOG_SERIES_ENABLE_LANGSMITH=true`
- `LANGSMITH_API_KEY=...`
- `BLOG_SERIES_LANGSMITH_PROJECT=blog-series-agent`
- `BLOG_SERIES_LANGSMITH_API_KEY_ENV=LANGSMITH_API_KEY`
- `BLOG_SERIES_LANGSMITH_ENDPOINT=` if using a custom endpoint

Supported observability hooks include:

- start and finish run traces
- node event logging
- artifact metadata logging
- evaluation summaries
- feedback events
- skill retrieval metadata
- skill adherence metadata

If LangSmith is not configured, the repository still works normally.

## Repository Layout

```text
src/blog_series_agent/
  agents/        Prompt-driven workflow agents
  api/           FastAPI app and routes
  config/        Environment and YAML config models
  dashboard/     Streamlit launcher and UI
  graphs/        LangGraph state, routing, builders
  models/        LLM abstraction layer
  prompts/       External prompt templates
  schemas/       Pydantic domain and API schemas
  services/      Pipeline, approval, evaluation, memory, observability
  utils/         File, prompt, logging, slug helpers
outputs/
  series_outline/
  research/
  drafts/
  reviews/
  final/
  assets/
  approval/
  evaluations/
  manifests/
data/
  memory/
tests/
configs/
```

## Setup

Requirements:

- Python 3.11+
- `uv`
- an OpenAI-compatible API key for live generation

Install:

```bash
uv sync --extra dev
cp .env.example .env
```

Key environment variables:

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `BLOG_SERIES_MODEL`
- `BLOG_SERIES_TEMPERATURE`
- `BLOG_SERIES_MAX_TOKENS`
- `BLOG_SERIES_OUTPUT_DIR`
- `BLOG_SERIES_ENABLE_EVALUATION`
- `BLOG_SERIES_ENABLE_MEMORY`
- `BLOG_SERIES_USE_MEMORY`
- `BLOG_SERIES_MAX_RETRIEVED_SKILLS`
- `BLOG_SERIES_ENABLE_LANGSMITH`
- `LANGSMITH_API_KEY`
- `BLOG_SERIES_LANGSMITH_PROJECT`
- `BLOG_SERIES_LANGSMITH_TRACE_PROMPTS`
- `BLOG_SERIES_LANGSMITH_TRACE_ARTIFACTS`

## CLI

Generate a full series:

```bash
uv run python -m blog_series_agent run --topic "ML System Design" --audience intermediate --parts 12 --use-memory true
```

Generate only the outline:

```bash
uv run python -m blog_series_agent outline --topic "AI Agents"
```

Generate one part:

```bash
uv run python -m blog_series_agent write --topic "ML System Design" --part 4 --use-memory true
```

Review an existing draft:

```bash
uv run python -m blog_series_agent review --file outputs/drafts/Part-4-feature-pipelines.md
```

Improve an existing draft:

```bash
uv run python -m blog_series_agent improve --draft outputs/drafts/Part-4-feature-pipelines.md --review outputs/reviews/Part-4-feature-pipelines-review.json
```

Evaluate a generated part:

```bash
uv run python -m blog_series_agent evaluate --part 4
```

Evaluate the latest series:

```bash
uv run python -m blog_series_agent evaluate-series
```

Submit explicit feedback:

```bash
uv run python -m blog_series_agent feedback add --part 4 --type clarity_issue --comment "Lead with the production pain point."
```

Build candidate skills from repeated feedback:

```bash
uv run python -m blog_series_agent memory build --topic "ML System Design" --audience intermediate
```

List candidate and approved skills:

```bash
uv run python -m blog_series_agent memory list
```

Approve or reject a candidate skill:

```bash
uv run python -m blog_series_agent memory approve --skill-id skill-clarity-open-with-problem
uv run python -m blog_series_agent memory reject --skill-id skill-clarity-open-with-problem
```

Preview retrieval:

```bash
uv run python -m blog_series_agent memory retrieve --topic "ML System Design" --part 1
```

Launch the API:

```bash
uv run python -m blog_series_agent api
```

Launch the dashboard:

```bash
uv run python -m blog_series_agent dashboard
```

## FastAPI

Important routes:

- `POST /runs/series`
- `POST /runs/outline`
- `POST /runs/blog`
- `POST /runs/review`
- `POST /runs/improve`
- `GET /runs/{run_id}`
- `GET /runs/{run_id}/artifacts`
- `GET /blogs/{part_id}`
- `POST /approval/{part_id}`
- `POST /evaluation/blog/{part_id}`
- `GET /evaluation/blog/{part_id}`
- `POST /evaluation/series`
- `POST /feedback`
- `GET /feedback`
- `POST /memory/build`
- `GET /memory/raw-feedback`
- `GET /memory/skills`
- `POST /memory/{skill_id}/approve`
- `POST /memory/{skill_id}/reject`
- `GET /memory/retrieval-preview`
- `GET /series/latest`

Example:

```bash
curl -X POST http://127.0.0.1:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "part_number": 4,
    "blog_slug": "feature-pipelines",
    "source_artifact": "Part-4-feature-pipelines",
    "raw_feedback": "The article needs a stronger synthesis section.",
    "normalized_issue_type": "clarity_issue",
    "severity": "medium",
    "suggested_fix": "Add a synthesis paragraph after dense enumerations.",
    "reviewer": "editor"
  }'
```

## Streamlit Dashboard

The dashboard is intentionally practical, not decorative. It now supports:

- start a run with or without memory retrieval
- inspect the latest outline
- browse artifact bundles by part
- inspect blog and series evaluations
- browse the raw feedback log
- inspect candidate and approved skills
- approve or reject candidate skills
- preview retrieved guidance
- inspect run manifests
- submit approval decisions

## Output Conventions

Examples:

- `outputs/series_outline/series_outline.md`
- `outputs/research/topic_research.md`
- `outputs/research/Part-1-introduction-research.md`
- `outputs/drafts/Part-1-introduction.md`
- `outputs/reviews/Part-1-introduction-review.json`
- `outputs/final/Part-1-introduction.md`
- `outputs/assets/Part-1-introduction-assets.md`
- `outputs/approval/Part-1-introduction-approval.json`
- `outputs/evaluations/blog/Part-1-introduction-eval.json`
- `outputs/evaluations/series/series-eval.json`
- `outputs/evaluations/runs/run-<id>-eval.json`
- `outputs/manifests/run-<timestamp>-<id>.json`

## Design Decisions

- `uv` is used for simple and consistent dependency management.
- Prompt templates live in external files so writing style, review criteria, and retrieved guidance placement can evolve without changing business logic.
- Approval and memory are separated intentionally to avoid turning a release-control record into an opaque learning store.
- Retrieved skills are passed into prompts explicitly and logged instead of silently mutating prompt text behind the scenes.
- Evaluation is a dedicated layer with separate artifacts so generation quality can be inspected independently of approval status.
- LangSmith is optional and wrapped behind an observability service so local development does not depend on external tracing.

## Testing

Run:

```bash
uv run pytest
```

The included test suite covers:

- schema validation
- review skill-adherence parsing
- evaluation scoring
- prompt loading
- file naming and persistence
- routing logic
- approval persistence
- evaluation persistence
- raw feedback logging
- approved skill persistence
- relevant skill retrieval
- CLI smoke
- FastAPI smoke
- dashboard utility logic

## Limitations

- Blog and series evaluation are currently aggregation-heavy and lean on reviewer outputs instead of a separate evaluator LLM in the main runtime path.
- Candidate skill extraction is deterministic today; the repository includes the prompt hook for LLM-based extraction but does not yet make that the default execution path.
- LangSmith integration logs run/node metadata and summaries, but it is not a full checkpointed replay system.
- API execution is synchronous and local-process oriented, not a distributed job queue.
- Streamlit actions are intended for local inspection and moderation, not multi-user production deployment.

## Safe and Transparent Learning Behavior

This repository deliberately avoids a black-box memory system.

- raw feedback is inspectable
- candidate skills are inspectable
- approved skills are inspectable
- retrieval previews are inspectable
- skill usage is logged
- reviewer skill adherence is inspectable

If the system learns a bad habit, it can be rejected explicitly instead of silently continuing to shape future outputs.
