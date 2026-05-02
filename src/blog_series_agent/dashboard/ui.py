"""Streamlit dashboard UI."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from blog_series_agent.config.settings import SeriesRunConfig, get_settings
from blog_series_agent.dashboard.utils import read_artifact_preview, split_artifacts_by_format
from blog_series_agent.services.container import build_application_services
from blog_series_agent.services.pipeline import PipelineService

st.set_page_config(page_title="Blog Series Agent", layout="wide")

services = build_application_services()
pipeline = PipelineService(**services)
artifact_service = services["artifact_service"]
approval_service = services["approval_service"]
evaluation_service = services["evaluation_service"]
memory_service = services["memory_service"]
settings = get_settings()

st.title("Blog Series Agent Dashboard")

page = st.sidebar.radio(
    "Navigate",
    [
        "Start Run",
        "Latest Outline",
        "Blog Inspector",
        "Compare Drafts",
        "Evaluations",
        "Feedback Browser",
        "Skill Memory",
        "Retrieval Preview",
        "Run History",
        "Approval",
    ],
)

if page == "Start Run":
    st.subheader("Start a New Run")
    with st.form("new_run"):
        topic = st.text_input("Topic", value="ML System Design")
        audience = st.selectbox("Audience", ["beginner", "intermediate", "advanced"], index=1)
        num_parts = st.number_input("Number of parts", min_value=1, max_value=20, value=12)
        st.caption("Blog generation uses the DeepAgents content builder.")
        use_memory = st.toggle("Use approved skill memory", value=True)
        enable_web_search = st.toggle("Enable web search/fetch tools", value=settings.blog_series_enable_web_search)
        run_in_background = st.toggle("Run in background", value=False)
        submitted = st.form_submit_button("Generate series")
        if submitted:
            overrides = settings.default_run_overrides()
            overrides["use_memory"] = use_memory
            overrides["enable_web_search"] = enable_web_search
            config = SeriesRunConfig(
                topic=topic,
                audience=audience,
                num_parts=int(num_parts),
                model=settings.default_model_config(),
                output_dir=settings.blog_series_output_dir,
                **overrides,
            )
            if run_in_background:
                import threading
                from uuid import uuid4

                task_id = f"dashboard-{uuid4().hex[:8]}"

                def _run_bg():
                    pipeline.run_series(config)

                thread = threading.Thread(target=_run_bg, name=task_id, daemon=True)
                thread.start()
                st.info(f"Series generation started in background (thread: {task_id}). Check Run History for results.")
            else:
                with st.spinner("Running full series generation..."):
                    manifest = pipeline.run_series(config)
                st.success(f"Run complete: {manifest.run_id} ({manifest.status})")

elif page == "Latest Outline":
    st.subheader("Latest Outline")
    outline_path = artifact_service.latest_outline_path()
    if outline_path:
        st.markdown(Path(outline_path).read_text(encoding="utf-8"))
    else:
        st.info("No outline has been generated yet.")

elif page == "Blog Inspector":
    st.subheader("Blog Artifact Inspector")
    manifests = artifact_service.list_manifests()
    part_ids = sorted(
        {
            Path(artifact.path).stem.replace("-review", "").replace("-assets", "").replace("-approval", "").replace("-eval", "")
            for manifest in manifests
            for artifact in manifest.artifacts
            if artifact.part_number is not None
        }
    )
    if part_ids:
        selected = st.selectbox("Select part", part_ids)
        artifacts = artifact_service.artifacts_for_part(selected)
        evaluation = evaluation_service.load_blog_evaluation(selected)
        buckets = split_artifacts_by_format(artifacts)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Markdown Artifacts", len(buckets["markdown"]))
        with col2:
            st.metric("JSON Artifacts", len(buckets["json"]))
        with col3:
            st.metric("Other Artifacts", len(buckets["other"]))
        if evaluation:
            st.info(
                f"Evaluation: overall {evaluation.overall_score}/10, skill adherence {evaluation.skill_adherence_score}/10"
            )
        for artifact in artifacts:
            with st.expander(Path(artifact.path).name, expanded=False):
                preview = read_artifact_preview(artifact.path)
                if artifact.path.endswith(".md"):
                    st.markdown(preview)
                else:
                    st.code(preview, language="json")
    else:
        st.info("No part artifacts are available yet.")

elif page == "Compare Drafts":
    st.subheader("Side-by-Side Draft Comparison")
    manifests = artifact_service.list_manifests()
    part_ids = sorted(
        {
            Path(artifact.path).stem.replace("-review", "").replace("-assets", "").replace("-approval", "").replace("-eval", "")
            for manifest in manifests
            for artifact in manifest.artifacts
            if artifact.part_number is not None
        }
    )
    if part_ids:
        selected_part = st.selectbox("Select part to compare", part_ids, key="compare-part")
        part_number_str = selected_part.split("-")[1] if "-" in selected_part else "1"
        slug = "-".join(selected_part.split("-")[2:]) if selected_part.count("-") >= 2 else selected_part

        draft_path = artifact_service.output_dir / "drafts" / f"{selected_part}.md"
        final_path = artifact_service.output_dir / "final" / f"{selected_part}.md"

        col_left, col_right = st.columns(2)
        with col_left:
            st.markdown("### Draft Version")
            if draft_path.exists():
                draft_content = draft_path.read_text(encoding="utf-8")
                st.metric("Word Count", len(draft_content.split()))
                st.markdown(draft_content[:5000] + ("\n\n*... truncated ...*" if len(draft_content) > 5000 else ""))
            else:
                st.info("No draft artifact found for this part.")
        with col_right:
            st.markdown("### Final Version")
            if final_path.exists():
                final_content = final_path.read_text(encoding="utf-8")
                st.metric("Word Count", len(final_content.split()))
                st.markdown(final_content[:5000] + ("\n\n*... truncated ...*" if len(final_content) > 5000 else ""))
            else:
                st.info("No final artifact found for this part.")

        if draft_path.exists() and final_path.exists():
            draft_words = len(draft_path.read_text(encoding="utf-8").split())
            final_words = len(final_path.read_text(encoding="utf-8").split())
            delta = final_words - draft_words
            st.markdown("### Comparison Summary")
            summary_col1, summary_col2, summary_col3 = st.columns(3)
            with summary_col1:
                st.metric("Draft Words", draft_words)
            with summary_col2:
                st.metric("Final Words", final_words)
            with summary_col3:
                st.metric("Word Delta", f"{'+' if delta > 0 else ''}{delta}")

            review_path = artifact_service.output_dir / "reviews" / f"{selected_part}-review.json"
            if review_path.exists():
                review_data = read_artifact_preview(str(review_path))
                with st.expander("Review Report", expanded=False):
                    st.code(review_data, language="json")
    else:
        st.info("No part artifacts available for comparison.")

elif page == "Evaluations":
    st.subheader("Evaluation Summaries")
    series_eval = evaluation_service.latest_series_evaluation()
    if series_eval:
        st.metric("Latest Series Score", series_eval.overall_score)
        st.write(series_eval.summary)
        st.json(series_eval.model_dump(mode="json"))
    else:
        st.info("No series evaluation available yet.")
    blog_eval_files = sorted((artifact_service.output_dir / "evaluations" / "blog").glob("Part-*-eval.json"))
    for path in blog_eval_files[-10:]:
        evaluation = read_artifact_preview(str(path))
        with st.expander(path.name, expanded=False):
            st.code(evaluation, language="json")

elif page == "Feedback Browser":
    st.subheader("Raw Feedback Log")
    feedback = memory_service.list_feedback()
    st.metric("Feedback Events", len(feedback))
    for item in reversed(feedback[-50:]):
        with st.expander(f"{item.feedback_id} [{item.normalized_issue_type}] {item.reviewer}", expanded=False):
            st.json(item.model_dump(mode="json"))

elif page == "Skill Memory":
    st.subheader("Candidate and Approved Skills")
    candidates = memory_service.list_candidate_skills()
    approved = memory_service.list_approved_skills()
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Candidate Skills", len(candidates))
        for skill in candidates:
            with st.expander(skill.title, expanded=False):
                st.json(skill.model_dump(mode="json"))
                action = st.radio(
                    f"Action for {skill.id}",
                    ["none", "approve", "reject"],
                    key=f"action-{skill.id}",
                    horizontal=True,
                )
                if st.button(f"Apply {action}", key=f"apply-{skill.id}") and action != "none":
                    if action == "approve":
                        memory_service.approve_skill(skill.id)
                    else:
                        memory_service.reject_skill(skill.id)
                    st.rerun()
    with col2:
        st.metric("Approved Skills", len(approved))
        for skill in approved:
            with st.expander(skill.title, expanded=False):
                st.json(skill.model_dump(mode="json"))

elif page == "Retrieval Preview":
    st.subheader("Retrieved Guidance Preview")
    topic = st.text_input("Topic", value="ML System Design")
    audience = st.selectbox("Audience", ["beginner", "intermediate", "advanced"], index=1, key="retrieval-audience")
    part_number = st.number_input("Part number", min_value=1, max_value=20, value=1)
    artifact_type = st.selectbox("Artifact type", ["draft", "review", "final", "evaluation"])
    if st.button("Preview retrieved skills"):
        retrieval = pipeline.preview_memory_retrieval(
            topic=topic,
            audience=audience,
            part_number=int(part_number),
            artifact_type=artifact_type,
        )
        st.json(retrieval.model_dump(mode="json"))

elif page == "Run History":
    st.subheader("Run History")
    manifests = artifact_service.list_manifests()
    for manifest in reversed(manifests):
        with st.expander(f"{manifest.run_id} [{manifest.status}] - {manifest.topic}", expanded=False):
            st.json(manifest.model_dump(mode="json"))

elif page == "Approval":
    st.subheader("Human Approval")
    part_id = st.text_input("Part ID", value="Part-1-introduction")
    reviewer = st.text_input("Reviewer name", value="editor")
    status = st.selectbox(
        "Decision",
        ["approved", "approved_with_notes", "changes_requested", "rejected"],
    )
    comments = st.text_area("Comments")
    if st.button("Submit approval"):
        record = approval_service.submit_approval(
            part_id=part_id,
            status=status,
            reviewer_name=reviewer,
            comments=comments,
        )
        memory_service.capture_approval_feedback(run_id=None, record=record)
        st.success(f"Approval saved: {record.status}")
        st.json(record.model_dump(mode="json"))
