# AI Agent Content Series Generator

A sophisticated **multi-agent workflow** using **LangGraph** and **LangSmith** to automatically generate long-form content (blogs, news, tutorials, reviews) with consistent structure, diagrams, and citations.

## Features

✨ **9 Specialized AI Agents**:
- 🎯 Supervisor: Orchestrates workflow and routing
- 🔍 Research: Web search and information gathering
- 📋 Outline: Structure creation and planning
- ✍️ Content Writer: Section-by-section writing
- 💻 Code Generator: Python implementation examples
- 📊 Diagram: Mermaid → PNG diagram generation
- 📚 Reference: Citation management
- ✅ QA: Automated quality checks
- 🔧 Integration: Final assembly and formatting

🚀 **Key Capabilities**:
- Generates multi-format content (editorial/news/tutorial/review) with configurable target lengths
- Automatically plans multi-chapter series with continuity
- Creates diagrams (Mermaid → PNG) plus optional code snippets
- Captures sources, metrics, and references for each section
- Live progress tracking and download-ready Markdown via REST API + Next.js UI

⚙️ **Technical Stack**:
- **LangGraph**: Workflow orchestration
- **LangSmith**: Tracing and monitoring
- **OpenAI GPT-4**: Language model
- **Tavily**: Web search tool
- **Pydantic**: State validation
- **Mermaid**: Diagram generation

## Installation

### Prerequisites

- **Python 3.11+** (required for LangSmith Studio UI in-memory server)
  - Python 3.9-3.10 will work for CLI usage only (without Studio UI)
  - Recommended: Python 3.12+ for best compatibility
- **Node.js** (for Mermaid CLI diagram generation)
- **Mermaid CLI** (for converting diagram code blocks to PNG images)
- **uv** (recommended) or Poetry (for dependency management)

### Setup

1. **Clone the repository**:
```bash
git clone <repository-url>
cd ai-agent-blog-series-generator
```

2. **Install uv** (if not already installed):
```bash
# On macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Alternative: using pip or Homebrew
pip install uv  # or: brew install uv
```

3. **Install Mermaid CLI** (for diagram generation):
```bash
# Install globally via npm
npm install -g @mermaid-js/mermaid-cli

# Verify installation
mmdc --version
```

4. **Install Python dependencies**:
```bash
# Create virtual environment and install dependencies
uv sync
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .  # Install project in editable mode
uv pip install -U "langgraph-cli[inmem]"  # For LangSmith Studio UI
```

**What gets installed:**
- `langgraph` and `langgraph-cli` for workflow orchestration and UI
- `langchain` and `langchain-openai` for LLM integration
- `langsmith` for tracing and monitoring
- All other project dependencies from `pyproject.toml`


**Quick Start Summary** (complete setup in one go):
```bash
# 1. Clone and navigate
git clone <repository-url>
cd ai-agent-blog-series-generator

# 2. Install Mermaid CLI (for diagrams)
npm install -g @mermaid-js/mermaid-cli

# 3. Install backend dependencies
uv sync
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .

# 4. Create .env and add keys
cp .env.example .env  # or touch .env && edit

# 5. Run backend API
uvicorn main:app --reload

# 6. Install frontend deps (first time only)
cd frontend && npm install

# 7. Start Next.js UI
npm run dev
```

⚠️ **Important**: Always ensure the virtual environment is activated before running any commands. If packages are not found, check that you see `(ai-agent-blog-series-generator-py3.12)` in your terminal prompt.

5. **Configure environment variables**:

Create a `.env` file in the project root with your API keys:

```bash
touch .env
```

Add the following to your `.env` file:

```bash
# Required API Keys
OPENAI_API_KEY=your_openai_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here

# Model selection (defaults to GPT-5 Nano)
PRIMARY_LLM_MODEL=gpt-5-nano
SECONDARY_LLM_MODEL=gpt-5-nano
# Optional legacy override
OPENAI_MODEL_NAME=gpt-5-nano

# Optional: LangSmith for tracing and monitoring
LANGSMITH_API_KEY=your_langsmith_api_key_here

# LangSmith project name (automatically set if not provided)
LANGSMITH_PROJECT=ml-blog-generation

# Enable LangSmith tracing (automatically set when LANGSMITH_API_KEY is provided)
LANGSMITH_TRACING_V2=true
```

**Getting API Keys:**
- **OpenAI**: [OpenAI Platform](https://platform.openai.com/api-keys)
- **Tavily**: [Tavily](https://tavily.com/)
- **LangSmith**: [LangSmith](https://smith.langchain.com/) (optional)

6. **Run the backend and UI**:

```bash
# Backend API (FastAPI)
uvicorn main:app --reload
# Health check
curl http://localhost:8000/api/health

# Frontend (Next.js)
cd frontend
npm install          # first run
npm run dev          # http://localhost:3000
```

## Usage

#### REST API Mode

You can now run the workflow as a REST API (ideal for frontend integration):

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Key endpoints:
- `GET /` or `/api/health` – status checks.
- `POST /api/blogs` – single blog generation (`topic`, `requirements`, etc.).
- `POST /api/series` – synchronous multi-blog generation.
- `POST /api/series/jobs` – enqueue long-running series generation and return `job_id`.
- `GET /api/series/jobs/{job_id}` – poll progress, retrieve chapter content, and download paths once finished.

### Frontend (Next.js)

A starter frontend lives in `frontend/` (Next.js 15 + Tailwind). It consumes the
FastAPI endpoints and provides simple forms for single/series generation.

```bash
# 1. Start FastAPI backend
uvicorn main:app --reload

# 2. Configure frontend env
cd frontend
cp .env.local.example .env.local  # adjust NEXT_PUBLIC_API_BASE_URL if needed

# 3. Run the Next.js dev server
npm run dev
```

Visit `http://localhost:3000` to access the UI. Ensure the backend is running so
API calls succeed.

#### Docker & Azure Container Apps

Docker images are provided for both services:

```bash
# Build images locally
docker build -f Dockerfile.backend -t blog-backend .
docker build -f Dockerfile.frontend -t blog-frontend .

# Orchestration (local)
docker-compose up --build
```

Deploying to Azure Container Apps typically follows this flow:

```bash
# Push images to Azure Container Registry
az acr build --registry <ACR_NAME> --image blog-backend:latest -f Dockerfile.backend .
az acr build --registry <ACR_NAME> --image blog-frontend:latest -f Dockerfile.frontend .

# Create Container Apps (backend)
az containerapp create --name blog-backend --resource-group <RG> --image <ACR_LOGIN>/blog-backend:latest --target-port 8000 --ingress external --env-vars OPENAI_API_KEY=... TAVILY_API_KEY=... PRIMARY_LLM_MODEL=gpt-5-nano

# Frontend (point NEXT_PUBLIC_API_BASE_URL to backend URL)
az containerapp create --name blog-frontend --resource-group <RG> --image <ACR_LOGIN>/blog-frontend:latest --target-port 3000 --ingress external --env-vars NEXT_PUBLIC_API_BASE_URL=https://<backend-base-url>
```

Adjust secrets with Azure Key Vault or Container Apps secrets as needed.


#### Rendering Mermaid Diagrams

Blog posts embed Mermaid code blocks for every diagram placeholder. During
integration these blocks are automatically rendered to PNG files using the
Mermaid CLI (if installed), so the final markdown already references concrete
images. You can re-render or regenerate diagrams at any time with:

```bash
python -m src.utils.render_mermaid_program --input output
```

Key options:
- Use `--dry-run` to list diagrams without writing files.
- `--images-dir` overrides the image directory from the diagram agent config.

The script scans each markdown file separately, renders diagrams with Mermaid
CLI, and replaces only the matching code block with an image reference—no
combining of multiple blogs or outputs.

#### Validation and Testing

```bash
# Ensure virtual environment is activated
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Validate setup without running (dry run)
python main.py --dry-run

# Test with debug logging
python main.py --topic "Machine Learning Basics" --log-level DEBUG
```

#### Advanced Options

```bash
# Custom configuration and output
python main.py --topic "Fraud Detection" \
    --config custom_config.yaml \
    --output custom_output/

# With debug logging
python main.py --topic "Large-Scale Recommendation Systems" \
    --requirements "Netflix-scale, 200M+ users, <100ms latency" \
    --author "Senior ML Engineer" \
    --log-level DEBUG
```

### Command Line Arguments Reference

| Argument | Description | Example |
|----------|-------------|---------|
| `--topic` | Blog topic for single blog generation | `--topic "Real-Time Fraud Detection"` |
| `--requirements` | Optional system requirements/specifications | `--requirements "Scale: 1M TPS, Latency: <50ms"` |
| `--target-length` | Target word count per blog | `--target-length 5000` |
| `--content-type` | Content type (blog/news/tutorial/review) | `--content-type news` |
| `--series` | Blog series name | `--series "ML System Design"` |
| `--topics` | List of topics for blog series | `--topics "Bot Detection" "ETA Prediction"` |
| `--series-count` | Number of blogs to generate when using `--series` | `--series-count 5` |
| `--author` | Author name (default: "AI Agent") | `--author "John Doe"` |
| `--output` | Custom output directory | `--output custom_output/` |
| `--config` | Path to configuration file | `--config config/prod_config.yaml` |
| `--log-level` | Logging level (DEBUG/INFO/WARNING/ERROR) | `--log-level DEBUG` |
| `--dry-run` | Validate setup without running workflow | `--dry-run` |

## Configuration

Edit `config/workflow_config.yaml` to customize:

- **LLM settings**: Model, temperature, max tokens
- **Agent configuration**: Per-agent LLM and parameters
- **Workflow settings**: Checkpoints, retry policy, timeouts
- **Quality standards**: Thresholds and weights
- **Output format**: Directories and file patterns

### Key Configuration Sections

```yaml
llm:
  primary:
    model: "gpt-4"
    temperature: 0.7
    max_tokens: 4000

agents:
  supervisor:
    temperature: 0.3
  content_writer:
    temperature: 0.7
    parallel_sections: 6
  research:
    web_search:
      max_queries: 8  # limit how many search queries are issued per topic

workflow:
  checkpoints:
    enabled: true
    locations: [after_research, after_outline, after_qa]
  
  retry:
    max_attempts: 3
    backoff_strategy: "exponential"
  
  langgraph:
    recursion_limit: 75  # Raise this if you hit GraphRecursionError
    max_revision_loops: 3   # Max QA revision cycles before human review
```

## Project Structure

```
ai-agent-blog-series-generator/
├── src/
│   ├── agents/              # 9 specialized agents
│   │   ├── base_agent.py
│   │   ├── supervisor_agent.py
│   │   ├── research_agent.py
│   │   ├── outline_agent.py
│   │   ├── content_writer_agent.py
│   │   ├── code_generator_agent.py
│   │   ├── diagram_agent.py
│   │   ├── reference_agent.py
│   │   ├── qa_agent.py
│   │   └── integration_agent.py
│   ├── workflow/            # LangGraph workflow
│   │   ├── graph.py
│   │   ├── nodes.py
│   │   └── routing.py
│   ├── tools/               # Agent tools
│   │   ├── web_search.py
│   │   ├── diagram_generator.py
│   │   └── code_validator.py
│   ├── schemas/             # Pydantic schemas
│   │   └── state.py
│   └── utils/               # Utilities
│       ├── config_loader.py
│       ├── llm_factory.py
│       ├── logger.py
│       └── prompt_loader.py
├── config/                  # Configuration files
│   └── workflow_config.yaml
├── src/
│   ├── prompts/             # Agent prompts
│   │   └── agent_prompts.md
├── output/                  # Generated blogs
├── images/                  # Generated diagrams
├── logs/                    # Log files
├── main.py                  # CLI entry point
├── app.py                   # LangSmith Studio UI entry point
├── langgraph.json          # LangGraph configuration
├── pyproject.toml          # Dependencies
├── Makefile                # Development commands
└── README.md               # This file
```

## Workflow Architecture

```
User Input → Supervisor → Research → Outline → 
Content Writer (parallel sections) → Code Generator → 
Diagram Generator → Reference Manager → QA → 
Integration → Final Blog
```

### Conditional Routing

- **Content Writer**: Loops until all sections complete
- **QA Check**: Routes to integration (pass) or revision (fail)
- **Human Review**: Optional checkpoints for approval

## Output

Generated blog posts include:

- **Markdown file** with complete content
- **Diagrams** (PNG images in `images/` folder)
- **Code examples** integrated throughout
- **References** with valid URLs
- **Table of contents** auto-generated
- **Metadata** (author, date, quality score)

### Example Output Structure

```markdown
# ML System Design: Real-Time Fraud Detection

**Author**: AI Agent
**Date**: 2025-01-15

## Table of Contents
1. Introduction
2. Problem Statement
3. Feature Engineering
...

## Introduction
[Content with real-world examples, diagrams, code...]

## References
[1] Netflix Engineering Blog - https://...
[2] Uber Engineering Blog - https://...
```

## Monitoring with LangSmith

The workflow integrates with LangSmith for tracing, metrics, performance monitoring, debugging, and quality evaluation.

- 📊 **Tracing**: Visualize agent execution flow
- 📈 **Metrics**: Track latency, tokens, costs
- ⚡ **Performance**: Monitor agent response times
- 🐛 **Debugging**: Identify and fix issues
- 📝 **Evaluation**: Assess output quality

Configure in your `.env` file (only `LANGSMITH_API_KEY` is required, others are set automatically):
```bash
# Required for LangSmith integration
LANGSMITH_API_KEY=your_langsmith_api_key_here

# Optional - these are set automatically if not provided:
# LANGSMITH_PROJECT=ml-blog-generation
# LANGSMITH_TRACING_V2=true
```

The workflow will automatically:
- Enable tracing when `LANGSMITH_API_KEY` is provided
- Set the project name to "ml-blog-generation" (configurable in `config/workflow_config.yaml`)
- Enable LangSmith tracing v2

## Development

### Makefile Commands for Development

The project includes comprehensive Makefile commands for development tasks:

```bash
# Setup and installation
make setup          # Initial setup (install + create directories)
make install         # Install dependencies using Poetry

# Running the application
make studio          # Start LangSmith Studio UI (handles activation)
make validate        # Validate environment and configuration
make start TOPIC="Your Topic"              # Generate single blog
make series SERIES="Series Name" TOPICS="Topic1,Topic2"  # Generate series
make example         # Run example blog generation

# Development and testing
make test            # Run tests
make lint            # Run linting checks
make format          # Format code with black
make typecheck       # Run type checking with mypy

# Maintenance
make clean           # Clean generated files and caches
make clean-all       # Clean everything including virtual environment
make logs            # Show recent logs
make config          # Show current configuration
make update          # Update dependencies

# Utilities
make shell           # Start Poetry shell
make help            # Show all available commands
```

### Manual Development Commands

**Note:** Ensure virtual environment is activated, or use `uv run` prefix:

```bash
# Running Tests
pytest tests/ -v  # or: uv run pytest tests/ -v

# Code Quality
black src/ main.py                    # Format code
pylint src/ --max-line-length=100    # Lint code
mypy src/                             # Type checking
```

### Adding New Agents

1. Create agent class in `src/agents/`
2. Inherit from `BaseAgent`
3. Implement `execute()` method
4. Add node function in `src/workflow/nodes.py`
5. Update workflow graph in `src/workflow/graph.py`

## Customization

### Custom Prompts

Edit `src/prompts/agent_prompts.md` to customize agent behavior.

### Custom Templates

Modify `config/workflow_config.yaml` under `template:` section.

### Blog Series Configuration

Create custom series:

```python
from src.schemas.state import BlogSeriesConfig

series = BlogSeriesConfig(
    series_name="Advanced ML Systems",
    number_of_blogs=5,
    topics=[
        "Distributed Training",
        "Model Serving at Scale",
        "Feature Stores",
        "Online Learning",
        "A/B Testing Infrastructure"
    ],
    author="Your Name",
    output_directory="output/advanced-ml"
)
```

## Troubleshooting

### LangSmith Studio UI Issues

**"Python 3.11+ required" or "langgraph: command not found"**
- Upgrade to Python 3.11+ (3.12+ recommended)
- Reinstall dependencies: `rm -rf .venv && uv sync && uv pip install -U "langgraph-cli[inmem]"`
- Verify: `langgraph --version`

**"Cannot find graph" or UI not loading**
- Ensure `langgraph.json` and `app.py` exist in project root
- Verify configuration: `cat langgraph.json`

**"Port 8123 already in use"**
- Kill existing process: `pkill -f "langgraph dev"`
- Use different port: `langgraph dev --no-browser --port 8124`

**Workflow fails to start**
- Validate setup: `python main.py --dry-run`
- Check `.env` file exists and has required API keys
- Reinstall dependencies: `uv sync`

### Environment Variable Issues

**Missing API keys**
- Ensure `.env` file exists in project root
- Add required keys: `OPENAI_API_KEY`, `TAVILY_API_KEY`
- Validate: `make validate` or `python main.py --dry-run`

**Permission errors**
- Ensure `.env` is readable: `chmod 644 .env`

### Other Issues

**Mermaid CLI not found**
```bash
npm install -g @mermaid-js/mermaid-cli
```

### Memory Issues

Reduce parallel execution in config:
```yaml
agents:
  content_writer:
    parallel_sections: 3  # Reduce from 6
```

### Quality Check Failures

Adjust thresholds in config:
```yaml
quality:
  minimum_score: 6.0  # Lower from 7.0
```

## Performance

Expected performance metrics:

- **End-to-end time**: 30-45 minutes per blog
- **Token usage**: 150K-200K tokens per blog
- **Cost**: $6-10 per blog (GPT-4)
- **Quality score**: 7.5-9.0/10

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

[Your License Here]

## Acknowledgments

- LangChain team for LangGraph and LangSmith
- OpenAI for GPT-4
- Tavily for web search capabilities

## Support

For issues, questions, or contributions:
- GitHub Issues: [Link to issues]
- Documentation: See `docs/` folder
- Email: [Your Email]

---

Built with ❤️ using LangGraph and LangSmith
