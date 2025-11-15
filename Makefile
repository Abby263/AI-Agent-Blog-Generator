.PHONY: install start stop restart clean test lint format help

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

## help: Show this help message
help:
	@echo "$(BLUE)AI Agent Blog Series Generator - Available Commands:$(NC)"
	@echo ""
	@grep -E '^## ' $(MAKEFILE_LIST) | sed 's/## /  $(GREEN)/' | sed 's/:/$(NC):/'
	@echo ""

## install: Install dependencies using Poetry
install:
	@echo "$(BLUE)Installing dependencies...$(NC)"
	poetry install
	@echo "$(GREEN)✓ Dependencies installed$(NC)"
	@echo "$(YELLOW)Don't forget to install Mermaid CLI: npm install -g @mermaid-js/mermaid-cli$(NC)"

## setup: Initial setup (install + create directories)
setup: install
	@echo "$(BLUE)Creating directories...$(NC)"
	mkdir -p output images logs
	@echo "$(GREEN)✓ Directories created$(NC)"
	@echo "$(YELLOW)Remember to configure .env file with your API keys$(NC)"

## start: Generate a single blog (requires TOPIC variable)
start:
	@if [ -z "$(TOPIC)" ]; then \
		echo "$(YELLOW)Usage: make start TOPIC='Real-Time Fraud Detection'$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Starting blog generation for: $(TOPIC)$(NC)"
	poetry run python main.py --topic "$(TOPIC)" $(ARGS)

## series: Generate a blog series (requires TOPICS variable)
series:
	@if [ -z "$(TOPICS)" ]; then \
		echo "$(YELLOW)Usage: make series SERIES='ML Systems' TOPICS='Bot Detection,ETA Prediction'$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Starting blog series generation$(NC)"
	poetry run python main.py --series "$(SERIES)" --topics $(shell echo $(TOPICS) | tr ',' ' ')

## studio: Start LangSmith Studio UI
studio:
	@echo "$(BLUE)Starting LangSmith Studio UI...$(NC)"
	@echo "$(YELLOW)Access the UI at: http://localhost:8123$(NC)"
	poetry run langgraph dev --no-browser

## validate: Validate environment and configuration
validate:
	@echo "$(BLUE)Validating environment...$(NC)"
	poetry run python main.py --dry-run
	@echo "$(GREEN)✓ Validation complete$(NC)"

## test: Run tests
test:
	@echo "$(BLUE)Running tests...$(NC)"
	poetry run pytest tests/ -v
	@echo "$(GREEN)✓ Tests complete$(NC)"

## lint: Run linting checks
lint:
	@echo "$(BLUE)Running linting...$(NC)"
	poetry run pylint src/ --max-line-length=100
	@echo "$(GREEN)✓ Linting complete$(NC)"

## format: Format code with black
format:
	@echo "$(BLUE)Formatting code...$(NC)"
	poetry run black src/ main.py
	@echo "$(GREEN)✓ Formatting complete$(NC)"

## typecheck: Run type checking with mypy
typecheck:
	@echo "$(BLUE)Running type checks...$(NC)"
	poetry run mypy src/
	@echo "$(GREEN)✓ Type checking complete$(NC)"

## clean: Clean generated files and caches
clean:
	@echo "$(BLUE)Cleaning generated files...$(NC)"
	rm -rf output/* images/* logs/*
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

## clean-all: Clean everything including Poetry virtual environment
clean-all: clean
	@echo "$(BLUE)Removing virtual environment...$(NC)"
	poetry env remove --all
	@echo "$(GREEN)✓ Complete cleanup done$(NC)"

## logs: Show recent logs
logs:
	@if [ -f logs/workflow.log ]; then \
		tail -n 100 logs/workflow.log; \
	else \
		echo "$(YELLOW)No logs found$(NC)"; \
	fi

## config: Show current configuration
config:
	@echo "$(BLUE)Current Configuration:$(NC)"
	@cat config/workflow_config.yaml

## shell: Start Poetry shell
shell:
	poetry shell

## update: Update dependencies
update:
	@echo "$(BLUE)Updating dependencies...$(NC)"
	poetry update
	@echo "$(GREEN)✓ Dependencies updated$(NC)"

## example: Run example blog generation
example:
	@echo "$(BLUE)Running example blog generation...$(NC)"
	make start TOPIC="Real-Time Fraud Detection" ARGS="--requirements 'Scale: 1M TPS, Latency: <50ms'"

## docs: Generate documentation
docs:
	@echo "$(BLUE)Documentation available in docs/ folder$(NC)"
	@echo "  - multi-agent-blog-workflow-design.md"
	@echo "  - workflow-architecture-overview.md"
	@echo "  - implementation-checklist.md"

