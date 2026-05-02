from blog_series_agent.utils.research import (
    extract_source_notes_from_evidence,
    sanitize_research_meta,
    sanitize_supporting_points,
)


def test_extract_source_notes_from_evidence_preserves_exact_urls() -> None:
    evidence = """
[1] TensorFlow Serving
URL: https://www.tensorflow.org/tfx/guide/serving
Serving docs.

Title: ONNX Runtime Performance
URL: https://onnxruntime.ai/docs/performance/
Performance docs.
"""

    notes = extract_source_notes_from_evidence(evidence)

    assert [note.url for note in notes] == [
        "https://www.tensorflow.org/tfx/guide/serving",
        "https://onnxruntime.ai/docs/performance/",
    ]
    assert notes[0].source_type == "documentation"


def test_sanitize_research_meta_removes_failed_search_boilerplate() -> None:
    text = """
Web search evidence could not be retrieved in this session.

Use an explicit latency budget and validate queueing, compute, and network time separately.
"""

    assert sanitize_research_meta(text) == (
        "Use an explicit latency budget and validate queueing, compute, and network time separately."
    )


def test_sanitize_supporting_points_removes_meta_failures() -> None:
    points = [
        "No results found for targeted query.",
        "Bounded queues prevent unbounded tail latency.",
    ]

    assert sanitize_supporting_points(points) == ["Bounded queues prevent unbounded tail latency."]
