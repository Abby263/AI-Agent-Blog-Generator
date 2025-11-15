# AI Agent Blog Series Generator

A sophisticated **multi-agent workflow** using **LangGraph** and **LangSmith** to automatically generate high-quality ML system design blog posts.

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
- Generates 8,000-10,000 word technical blogs
- Creates 10-15 architectural diagrams
- Produces 15-25 code examples
- Includes 20-30 references with sources
- Follows consistent ML system design template
- Real-world examples from Netflix, Uber, Google, etc.

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

3. **Install dependencies**:
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

# 2. Install uv if needed
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Install dependencies and activate virtual environment
uv sync
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .  # Install project in editable mode
uv pip install -U "langgraph-cli[inmem]"

# 4. Create .env file and add your API keys
touch .env
# Edit .env with your OPENAI_API_KEY, TAVILY_API_KEY, etc.

# 5. Validate setup (ensure virtual environment is active)
python main.py --dry-run

# 6. Start LangSmith Studio UI (ensure virtual environment is active)
langgraph dev --no-browser
# Or run a blog directly: python main.py --topic "Your Topic"
```

⚠️ **Important**: Always ensure the virtual environment is activated before running any commands. If packages are not found, check that you see `(ai-agent-blog-series-generator-py3.12)` in your terminal prompt.

4. **Install Mermaid CLI** (for diagram generation):
```bash
npm install -g @mermaid-js/mermaid-cli
# or
brew install mermaid-cli
```

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

6. **Validate setup**:

```bash
# Ensure virtual environment is activated
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Validate environment and configuration
python main.py --dry-run

# Or using Make
make validate
```

You should see output like:
```
✓ Required environment variables found
✓ LangSmith API key for tracing (optional) configured
✓ Configuration loaded from config/workflow_config.yaml
✓ Dry run: Environment and configuration validated
✓ Ready to generate blogs!
```

**If using LangSmith Studio UI**, also verify the server can start:
```bash
# Ensure virtual environment is activated
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Quick test (will exit after 3 seconds)
langgraph dev --help

# If you see help output, the installation is correct
```

## Usage

### Option 1: LangSmith Studio UI (Recommended for Interactive Use)

**Requirements:** Python 3.11+ (Python 3.12+ recommended)

```bash
# Start LangSmith Studio UI (Make handles activation automatically)
make studio
# Or manually: langgraph dev --no-browser

# The UI will be available at: http://localhost:8123
```

**What you can do in LangSmith Studio:**
- ✨ **Visual Configuration**: Configure all parameters through an intuitive UI
- 📊 **Real-time Monitoring**: Watch agents execute in real-time
- 🔍 **Debug Mode**: Step through the workflow and inspect state at each step
- 📈 **Performance Metrics**: View latency, token usage, and costs
- 🎯 **Interrupt & Resume**: Pause workflow for human review and resume later
- 📝 **Full Tracing**: Complete visibility into all agent interactions

**Configurable Parameters in UI:**
- **topic**: Blog topic (e.g., "Real-Time Fraud Detection")
- **requirements**: System requirements (e.g., "Scale: 1M TPS, Latency: <50ms")
- **author**: Author name (default: "AI Agent")
- **target_length**: Word count (500-50000, default: 8000)
- **include_code**: Include code examples (true/false)
- **include_diagrams**: Include diagrams (true/false)
- **tone**: Writing tone (professional/casual/academic)
- **content_type**: Content type (blog/news/tutorial/review)

**Access the UI:**
1. Open browser and navigate to `http://localhost:8123`
2. Select the "agent" graph
3. Configure parameters in the input panel
4. Click "Start" to run the workflow
5. Monitor execution in real-time with full tracing

---

### Option 2: Quick Start with Make Commands

The easiest way to run the application is using the included Makefile:

```bash
# Validate your setup (recommended first step)
make validate

# Generate a single blog
make start TOPIC="Real-Time Fraud Detection"

# Generate a blog with custom requirements
make start TOPIC="Video Recommendation Systems" ARGS="--requirements 'Scale: 1B users, Latency: <100ms' --author 'Your Name'"

# Generate a blog series
make series SERIES="ML System Design" TOPICS="Bot Detection,ETA Prediction,Search Ranking"

# Run example blog generation
make example

# View recent logs
make logs
```

---

### Option 3: Direct Python Commands

**Note:** Ensure virtual environment is activated (see Installation section).

#### Single Blog Generation

Ensure virtual environment is activated:
```bash
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

Basic blog generation:
```bash
python main.py --topic "Real-Time Fraud Detection"

# With custom requirements and author
python main.py --topic "Video Recommendation Systems" \
    --requirements "Scale: 1B users, Latency: <100ms" \
    --author "Your Name"
```

#### Blog Series Generation

```bash
python main.py --series "ML System Design" \
    --topics "Bot Detection" "ETA Prediction" "Search Ranking" \
    --author "Your Name"
```

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
| `--series` | Blog series name | `--series "ML System Design"` |
| `--topics` | List of topics for blog series | `--topics "Bot Detection" "ETA Prediction"` |
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

workflow:
  checkpoints:
    enabled: true
    locations: [after_research, after_outline, after_qa]
  
  retry:
    max_attempts: 3
    backoff_strategy: "exponential"
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

