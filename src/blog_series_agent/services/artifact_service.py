"""Artifact persistence service."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from ..config.settings import SeriesRunConfig
from ..schemas.artifacts import ArtifactRecord, ArtifactType, PartStatus, RunManifest, RunStatus
from ..utils.files import ensure_directory, read_json, write_json, write_markdown
from ..utils.slug import to_part_filename


class ArtifactService:
    """Handles output directories, filenames, and run manifests."""

    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)
        ensure_directory(self.output_dir)
        for folder in [
            "series_outline",
            "research",
            "drafts",
            "reviews",
            "final",
            "assets",
            "approval",
            "evaluations/blog",
            "evaluations/series",
            "evaluations/runs",
            "manifests",
        ]:
            ensure_directory(self.output_dir / folder)

    def create_run_manifest(self, config: SeriesRunConfig) -> RunManifest:
        run_id = datetime.now(timezone.utc).strftime("run-%Y%m%d-%H%M%S-") + uuid4().hex[:8]
        manifest = RunManifest(
            run_id=run_id,
            topic=config.topic,
            target_audience=config.target_audience,
            num_parts=config.num_parts,
            status=RunStatus.PENDING,
            selected_parts=config.selected_parts,
        )
        self.save_manifest(manifest)
        return manifest

    def save_manifest(self, manifest: RunManifest) -> Path:
        manifest.updated_at = datetime.now(timezone.utc)
        path = self.output_dir / "manifests" / f"{manifest.run_id}.json"
        write_json(path, manifest.model_dump(mode="json"))
        return path

    def load_manifest(self, run_id: str) -> RunManifest:
        payload = read_json(self.output_dir / "manifests" / f"{run_id}.json")
        return RunManifest.model_validate(payload)

    def list_manifests(self) -> list[RunManifest]:
        manifests = []
        for path in sorted((self.output_dir / "manifests").glob("run-*.json")):
            manifests.append(RunManifest.model_validate(read_json(path)))
        return manifests

    def path_for_outline(self, extension: str) -> Path:
        return self.output_dir / "series_outline" / f"series_outline.{extension}"

    def path_for_part(self, folder: str, part_number: int, slug: str, suffix: str = "", extension: str = "md") -> Path:
        return self.output_dir / folder / to_part_filename(part_number, slug, suffix=suffix, extension=extension)

    def write_markdown_artifact(
        self,
        *,
        manifest: RunManifest,
        artifact_type: ArtifactType,
        folder: str,
        filename: str,
        content: str,
        part_number: int | None = None,
    ) -> Path:
        path = write_markdown(self.output_dir / folder / filename, content)
        self._record_artifact(manifest, artifact_type, path, part_number)
        return path

    def write_json_artifact(
        self,
        *,
        manifest: RunManifest,
        artifact_type: ArtifactType,
        folder: str,
        filename: str,
        payload: Any,
        part_number: int | None = None,
    ) -> Path:
        path = write_json(self.output_dir / folder / filename, payload)
        self._record_artifact(manifest, artifact_type, path, part_number)
        return path

    def update_part_status(self, manifest: RunManifest, part_number: int, status: PartStatus) -> None:
        manifest.part_statuses[part_number] = status
        self.save_manifest(manifest)

    def set_status(self, manifest: RunManifest, status: RunStatus, error: str | None = None) -> None:
        manifest.status = status
        manifest.error = error
        self.save_manifest(manifest)

    def artifacts_for_part(self, part_id: str) -> list[ArtifactRecord]:
        matches = []
        stem = part_id.removesuffix(".md").removesuffix(".json")
        for manifest in self.list_manifests():
            for artifact in manifest.artifacts:
                path = Path(artifact.path)
                if path.stem == stem or stem in path.stem:
                    matches.append(artifact)
        return matches

    def latest_outline_path(self) -> Path | None:
        path = self.path_for_outline("md")
        return path if path.exists() else None

    def latest_series_evaluation_path(self) -> Path | None:
        path = self.output_dir / "evaluations" / "series" / "series-eval.json"
        return path if path.exists() else None

    def _record_artifact(
        self,
        manifest: RunManifest,
        artifact_type: ArtifactType,
        path: Path,
        part_number: int | None,
    ) -> None:
        manifest.artifacts.append(
            ArtifactRecord(artifact_type=artifact_type, path=str(path), part_number=part_number)
        )
        self.save_manifest(manifest)
