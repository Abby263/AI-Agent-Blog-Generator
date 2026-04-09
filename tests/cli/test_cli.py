from pathlib import Path

from typer.testing import CliRunner

from blog_series_agent.cli import _resolve_part_id, app
from blog_series_agent.config.settings import AppSettings

runner = CliRunner()


def test_cli_help_smoke() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "LangGraph-based technical blog series generator" in result.stdout


def test_cli_memory_help_smoke() -> None:
    result = runner.invoke(app, ["memory", "--help"])
    assert result.exit_code == 0
    assert "Memory and reusable skill commands" in result.stdout


def test_cli_feedback_help_smoke() -> None:
    result = runner.invoke(app, ["feedback", "--help"])
    assert result.exit_code == 0
    assert "Structured feedback commands" in result.stdout


def test_resolve_part_id_without_slug(monkeypatch, tmp_path: Path) -> None:
    final_dir = tmp_path / "final"
    final_dir.mkdir(parents=True)
    (final_dir / "Part-1-introduction-to-ml-system-design.md").write_text("content", encoding="utf-8")

    monkeypatch.setattr(
        "blog_series_agent.cli.get_settings",
        lambda: AppSettings(blog_series_output_dir=tmp_path),
    )

    assert _resolve_part_id(1) == "Part-1-introduction-to-ml-system-design"
