from pathlib import Path

from blog_series_agent.utils.files import read_json, write_json, write_markdown


def test_file_helpers_write_and_read(tmp_path: Path) -> None:
    markdown_path = write_markdown(tmp_path / "draft.md", "# Title")
    json_path = write_json(tmp_path / "data.json", {"ok": True})

    assert markdown_path.read_text(encoding="utf-8") == "# Title"
    assert read_json(json_path) == {"ok": True}

