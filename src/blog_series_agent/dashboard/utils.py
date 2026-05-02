"""Utility helpers for the Streamlit dashboard."""

from __future__ import annotations

from pathlib import Path

from ..schemas.artifacts import ArtifactRecord
from ..utils.files import read_json


def split_artifacts_by_format(artifacts: list[ArtifactRecord]) -> dict[str, list[ArtifactRecord]]:
    buckets = {"markdown": [], "json": [], "other": []}
    for artifact in artifacts:
        suffix = Path(artifact.path).suffix.lower()
        if suffix == ".md":
            buckets["markdown"].append(artifact)
        elif suffix == ".json":
            buckets["json"].append(artifact)
        else:
            buckets["other"].append(artifact)
    return buckets


def read_artifact_preview(path: str) -> str:
    artifact_path = Path(path)
    if artifact_path.suffix == ".json":
        payload = read_json(artifact_path)
        return str(payload)
    return artifact_path.read_text(encoding="utf-8")

