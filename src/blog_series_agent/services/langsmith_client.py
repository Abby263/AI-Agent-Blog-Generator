"""Optional LangSmith client wrapper."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

try:
    from langsmith import Client
except ImportError:  # pragma: no cover - optional dependency at runtime
    Client = None  # type: ignore[assignment]


class LangSmithClient:
    """Very small wrapper around the optional LangSmith client."""

    def __init__(
        self,
        *,
        enabled: bool,
        project: str,
        api_key_env: str,
        endpoint: str | None = None,
    ) -> None:
        self.enabled = enabled and Client is not None and bool(os.getenv(api_key_env))
        self.project = project
        self.endpoint = endpoint
        self._client = None
        if self.enabled:
            kwargs: dict[str, Any] = {"api_key": os.getenv(api_key_env)}
            if endpoint:
                kwargs["api_url"] = endpoint
            self._client = Client(**kwargs)

    def create_run(
        self,
        *,
        name: str,
        run_id: str,
        run_type: str,
        metadata: dict[str, Any],
        inputs: dict[str, Any] | None = None,
    ) -> None:
        if not self.enabled or self._client is None:
            return
        self._client.create_run(
            id=run_id,
            name=name,
            run_type=run_type,
            project_name=self.project,
            inputs=inputs or {},
            extra={"metadata": metadata},
            start_time=datetime.now(timezone.utc),
        )

    def update_run(
        self,
        *,
        run_id: str,
        outputs: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        if not self.enabled or self._client is None:
            return
        kwargs: dict[str, Any] = {
            "run_id": run_id,
            "end_time": datetime.now(timezone.utc),
        }
        if outputs is not None:
            kwargs["outputs"] = outputs
        if metadata is not None:
            kwargs["extra"] = {"metadata": metadata}
        if error is not None:
            kwargs["error"] = error
        self._client.update_run(**kwargs)

