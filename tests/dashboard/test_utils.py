from pathlib import Path

from blog_series_agent.schemas.artifacts import ArtifactRecord, ArtifactType
from blog_series_agent.dashboard.utils import read_artifact_preview, split_artifacts_by_format


def test_dashboard_utils(tmp_path: Path) -> None:
    markdown = tmp_path / "draft.md"
    markdown.write_text("# Title", encoding="utf-8")

    artifacts = [
        ArtifactRecord(artifact_type=ArtifactType.DRAFT, path=str(markdown), part_number=1),
    ]
    buckets = split_artifacts_by_format(artifacts)

    assert len(buckets["markdown"]) == 1
    assert read_artifact_preview(str(markdown)) == "# Title"

