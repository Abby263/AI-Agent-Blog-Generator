from pathlib import Path

from blog_series_agent.config.settings import RunMode, SeriesRunConfig, load_run_config


def test_series_run_config_validation() -> None:
    config = SeriesRunConfig(
        topic="RAG Systems",
        audience="intermediate",
        num_parts=8,
        run_mode=RunMode.DEV,
        approval_required=False,
    )
    assert config.topic == "RAG Systems"
    assert config.enable_web_search is False


def test_load_run_config(tmp_path: Path) -> None:
    config_path = tmp_path / "run.yaml"
    config_path.write_text(
        "topic: AI Agents\n"
        "target_audience: intermediate\n"
        "num_parts: 10\n"
        "run_mode: review\n"
        "enable_web_search: true\n"
        "approval_required: true\n",
        encoding="utf-8",
    )

    config = load_run_config(config_path)
    assert config.topic == "AI Agents"
    assert config.num_parts == 10
    assert config.enable_web_search is True
