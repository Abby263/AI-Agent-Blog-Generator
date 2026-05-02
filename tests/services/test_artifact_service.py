from pathlib import Path

from blog_series_agent.config.settings import SeriesRunConfig
from blog_series_agent.schemas.artifacts import ArtifactType
from blog_series_agent.services.artifact_service import ArtifactService


def test_artifact_service_persists_manifest_and_artifacts(tmp_path: Path) -> None:
    service = ArtifactService(tmp_path)
    config = SeriesRunConfig(topic="ML System Design", audience="intermediate", num_parts=12)
    manifest = service.create_run_manifest(config)

    service.write_markdown_artifact(
        manifest=manifest,
        artifact_type=ArtifactType.DRAFT,
        folder="drafts",
        filename="Part-1-introduction.md",
        content="# Intro",
        part_number=1,
    )

    loaded = service.load_manifest(manifest.run_id)
    assert loaded.artifacts[0].artifact_type == ArtifactType.DRAFT
    assert "Part-1-introduction.md" in loaded.artifacts[0].path

