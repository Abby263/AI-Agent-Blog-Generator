"""Application and run configuration."""

from __future__ import annotations

from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class RunMode(str, Enum):
    """Execution mode for the content pipeline."""

    DEV = "dev"
    REVIEW = "review"
    PRODUCTION = "production"


class ModelConfig(BaseModel):
    """Model execution settings."""

    model_config = {"protected_namespaces": ()}

    provider: str = "openai"
    model_name: str = "gpt-4o-mini"
    temperature: float = 0.3
    max_tokens: int = 4000
    api_base: str | None = None


class SeriesRunConfig(BaseModel):
    """Typed run configuration shared by CLI, API, and dashboard."""

    topic: str
    target_audience: str = Field(default="intermediate", alias="audience")
    num_parts: int = 12
    output_dir: Path = Path("outputs")
    selected_parts: list[int] = Field(default_factory=list)
    model: ModelConfig = Field(default_factory=ModelConfig)
    enable_review: bool = True
    enable_improve: bool = True
    enable_asset_plan: bool = True
    enable_human_approval: bool = True
    enable_evaluation: bool = True
    enable_memory: bool = True
    use_memory: bool = True
    max_retrieved_skills: int = 5
    memory_auto_approve_in_dev: bool = False
    min_word_count: int = 2000
    max_word_count: int = 3000
    run_mode: RunMode = RunMode.PRODUCTION
    approval_required: bool = True
    series_title: str | None = None
    enable_langsmith: bool = False
    langsmith_project: str = "blog-series-agent"
    langsmith_api_key_env: str = "LANGSMITH_API_KEY"
    langsmith_endpoint: str | None = None
    langsmith_trace_prompts: bool = False
    langsmith_trace_artifacts: bool = False
    # Grounded web research (DuckDuckGo + URL fetching)
    enable_web_search: bool = False
    web_search_max_results: int = 6
    web_fetch_max_chars: int = 5000
    web_max_fetches_per_section: int = 3

    model_config = {"protected_namespaces": (), "populate_by_name": True}

    @field_validator("num_parts")
    @classmethod
    def validate_num_parts(cls, value: int) -> int:
        if value < 1:
            raise ValueError("num_parts must be at least 1")
        return value

    @field_validator("max_word_count")
    @classmethod
    def validate_word_counts(cls, value: int, info: Any) -> int:
        min_words = info.data.get("min_word_count", 0)
        if value < min_words:
            raise ValueError("max_word_count must be >= min_word_count")
        return value

    @field_validator("approval_required")
    @classmethod
    def validate_approval_required(cls, value: bool, info: Any) -> bool:
        run_mode = info.data.get("run_mode", RunMode.PRODUCTION)
        if run_mode == RunMode.PRODUCTION and value is False:
            raise ValueError("approval_required must be true in production mode")
        return value


class AppSettings(BaseSettings):
    """Environment-backed application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    openai_api_key: str | None = None
    openai_base_url: str | None = None
    blog_series_model: str = "gpt-4o-mini"
    blog_series_temperature: float = 0.3
    blog_series_max_tokens: int = 4000
    blog_series_output_dir: Path = Path("outputs")
    blog_series_log_level: str = "INFO"
    blog_series_enable_evaluation: bool = True
    blog_series_enable_memory: bool = True
    blog_series_use_memory: bool = True
    blog_series_max_retrieved_skills: int = 5
    blog_series_memory_auto_approve_in_dev: bool = False
    blog_series_enable_langsmith: bool = False
    blog_series_langsmith_project: str = "blog-series-agent"
    blog_series_langsmith_api_key_env: str = "LANGSMITH_API_KEY"
    blog_series_langsmith_endpoint: str | None = None
    blog_series_langsmith_trace_prompts: bool = False
    blog_series_langsmith_trace_artifacts: bool = False
    # Grounded web research (DuckDuckGo + URL fetching)
    blog_series_enable_web_search: bool = False
    blog_series_web_search_max_results: int = 6
    blog_series_web_fetch_max_chars: int = 5000
    blog_series_web_max_fetches_per_section: int = 3
    blog_series_cors_origins: str = "*"

    def default_model_config(self) -> ModelConfig:
        """Build the default model configuration from environment settings."""

        return ModelConfig(
            provider="openai",
            model_name=self.blog_series_model,
            temperature=self.blog_series_temperature,
            max_tokens=self.blog_series_max_tokens,
            api_base=self.openai_base_url,
        )

    def default_run_overrides(self) -> dict[str, Any]:
        """Return shared run-level settings sourced from the environment."""

        return {
            "enable_evaluation": self.blog_series_enable_evaluation,
            "enable_memory": self.blog_series_enable_memory,
            "use_memory": self.blog_series_use_memory,
            "max_retrieved_skills": self.blog_series_max_retrieved_skills,
            "memory_auto_approve_in_dev": self.blog_series_memory_auto_approve_in_dev,
            "enable_langsmith": self.blog_series_enable_langsmith,
            "langsmith_project": self.blog_series_langsmith_project,
            "langsmith_api_key_env": self.blog_series_langsmith_api_key_env,
            "langsmith_endpoint": self.blog_series_langsmith_endpoint,
            "langsmith_trace_prompts": self.blog_series_langsmith_trace_prompts,
            "langsmith_trace_artifacts": self.blog_series_langsmith_trace_artifacts,
            "enable_web_search": self.blog_series_enable_web_search,
            "web_search_max_results": self.blog_series_web_search_max_results,
            "web_fetch_max_chars": self.blog_series_web_fetch_max_chars,
            "web_max_fetches_per_section": self.blog_series_web_max_fetches_per_section,
        }


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """Return cached application settings."""

    return AppSettings()


def load_run_config(path: str | Path) -> SeriesRunConfig:
    """Load a run configuration from YAML or JSON-compatible YAML."""

    config_path = Path(path)
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    return SeriesRunConfig.model_validate(raw)
