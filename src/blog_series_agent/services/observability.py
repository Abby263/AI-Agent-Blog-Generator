"""Observability and optional LangSmith tracing."""

from __future__ import annotations

import logging
from typing import Any

from ..config.settings import SeriesRunConfig
from .langsmith_client import LangSmithClient

logger = logging.getLogger(__name__)


class ObservabilityService:
    """Structured observability with optional LangSmith integration."""

    def __init__(self) -> None:
        self._client: LangSmithClient | None = None

    def configure_for_run(self, config: SeriesRunConfig) -> None:
        self._client = LangSmithClient(
            enabled=config.enable_langsmith,
            project=config.langsmith_project,
            api_key_env=config.langsmith_api_key_env,
            endpoint=config.langsmith_endpoint,
        )

    def start_run_trace(self, *, run_id: str, name: str, metadata: dict[str, Any], inputs: dict[str, Any] | None = None) -> None:
        logger.info("start_run_trace", extra={"run_id": run_id})
        if self._client is not None:
            self._client.create_run(name=name, run_id=run_id, run_type="chain", metadata=metadata, inputs=inputs)

    def log_node_event(self, *, run_id: str, node_name: str, metadata: dict[str, Any]) -> None:
        logger.info("node_event %s", node_name, extra={"run_id": run_id})
        if self._client is not None:
            self._client.create_run(
                name=node_name,
                run_id=f"{run_id}:{node_name}:{metadata.get('part_number', 'series')}",
                run_type="tool",
                metadata=metadata,
            )

    def log_artifact_metadata(self, *, run_id: str, artifact_path: str, metadata: dict[str, Any]) -> None:
        logger.info("artifact_metadata %s", artifact_path, extra={"run_id": run_id})
        if self._client is not None:
            self._client.update_run(run_id=run_id, metadata={"artifact_path": artifact_path, **metadata})

    def log_evaluation_summary(self, *, run_id: str, metadata: dict[str, Any]) -> None:
        logger.info("evaluation_summary", extra={"run_id": run_id})
        if self._client is not None:
            self._client.update_run(run_id=run_id, metadata=metadata)

    def log_feedback_event(self, *, run_id: str | None, metadata: dict[str, Any]) -> None:
        logger.info("feedback_event", extra={"run_id": run_id or "feedback"})
        if run_id and self._client is not None:
            self._client.update_run(run_id=run_id, metadata={"feedback_event": metadata})

    def log_skill_retrieval(self, *, run_id: str, metadata: dict[str, Any]) -> None:
        logger.info("skill_retrieval", extra={"run_id": run_id})
        if self._client is not None:
            self._client.update_run(run_id=run_id, metadata={"skill_retrieval": metadata})

    def log_skill_adherence(self, *, run_id: str, metadata: dict[str, Any]) -> None:
        logger.info("skill_adherence", extra={"run_id": run_id})
        if self._client is not None:
            self._client.update_run(run_id=run_id, metadata={"skill_adherence": metadata})

    def finish_run_trace(self, *, run_id: str, outputs: dict[str, Any] | None = None, error: str | None = None) -> None:
        logger.info("finish_run_trace", extra={"run_id": run_id})
        if self._client is not None:
            self._client.update_run(run_id=run_id, outputs=outputs, error=error)

