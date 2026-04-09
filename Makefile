PYTHON ?= python3.11

.PHONY: install test api dashboard run-outline

install:
	uv sync --extra dev

test:
	uv run pytest

api:
	uv run python -m blog_series_agent api

dashboard:
	uv run python -m blog_series_agent dashboard

run-outline:
	uv run python -m blog_series_agent outline --topic "ML System Design" --audience intermediate --parts 12

