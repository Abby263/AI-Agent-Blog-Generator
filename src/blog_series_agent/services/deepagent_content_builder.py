"""DeepAgents-backed content builder for one blog chapter.

This module keeps the DeepAgents integration behind one adapter. The graph
still owns release gates such as review, improvement, evaluation, memory, and
approval, but research/planning/drafting are delegated to one filesystem-backed
DeepAgent run instead of several nested ReAct loops.
"""

from __future__ import annotations

import json
import logging
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage

from ..config.settings import SeriesRunConfig
from ..models.base import BaseLLMClient
from ..schemas.memory import SkillRetrievalResult
from ..schemas.series import BlogSeriesOutline, BlogSeriesPart
from ..utils.markdown import normalize_markdown_document
from ..utils.slug import to_part_filename
from .deepagent_profile import DeepAgentProfile
from .research_tools import ResearchToolkit

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class DeepAgentBuildResult:
    """Canonical files produced by the DeepAgents content builder."""

    research_markdown: str
    plan_markdown: str
    draft_markdown: str
    asset_markdown: str
    manifest: dict[str, Any] = field(default_factory=dict)
    workspace: Path | None = None
    response_text: str = ""


class DeepAgentContentBuilder:
    """Create and invoke the official DeepAgents content-builder runtime."""

    def __init__(
        self,
        *,
        llm: BaseLLMClient,
        profile: DeepAgentProfile,
        research_toolkit: ResearchToolkit | None = None,
    ) -> None:
        self.llm = llm
        self.profile = profile
        self.research_toolkit = research_toolkit

    def build_blog(
        self,
        *,
        config: SeriesRunConfig,
        outline: BlogSeriesOutline,
        part: BlogSeriesPart,
        retrieved_guidance: SkillRetrievalResult,
        run_id: str,
    ) -> DeepAgentBuildResult:
        """Build research, plan, draft, and asset notes for one blog part."""

        workspace = self._prepare_workspace(config.output_dir, run_id, part)
        agent = self._create_agent(workspace)
        task = self._render_task(
            config=config,
            outline=outline,
            part=part,
            retrieved_guidance=retrieved_guidance,
        )
        logger.info("DeepAgents content builder — part %d: %s", part.part_number, part.title)
        result = agent.invoke(
            {"messages": [HumanMessage(content=task)]},
            config={"configurable": {"thread_id": f"{run_id}-part-{part.part_number}"}},
        )
        response_text = self._last_message_text(result)
        files = self._read_expected_files(workspace, fallback=response_text)
        return DeepAgentBuildResult(
            research_markdown=files["research.md"],
            plan_markdown=files["plan.md"],
            draft_markdown=normalize_markdown_document(files["draft.md"]),
            asset_markdown=files["assets.md"],
            manifest=self._read_manifest(workspace),
            workspace=workspace,
            response_text=response_text,
        )

    def _create_agent(self, workspace: Path):
        """Create the DeepAgent. Kept small so tests can override it."""

        try:
            from deepagents import create_deep_agent
            from deepagents.backends import FilesystemBackend
        except ImportError as exc:  # pragma: no cover - dependency should be installed
            raise RuntimeError(
                "deepagents is required for the content builder. "
                "Install with `uv add 'deepagents>=0.5.3,<0.6.0'`."
            ) from exc

        tools = self._tools()
        return create_deep_agent(
            model=self._chat_model(),
            memory=[".deepagent_profile/AGENTS.md"],
            skills=[".deepagent_profile/skills"],
            tools=tools,
            subagents=self._subagents(tools),
            backend=FilesystemBackend(root_dir=workspace, virtual_mode=True),
            system_prompt=(
                "You are the single content-builder coordinator for a technical blog-series pipeline. "
                "Use the filesystem tools to create the requested artifacts exactly. "
                "Use research tools and subagents when available; do not fabricate sources."
            ),
        )

    def _chat_model(self) -> Any:
        model = self.llm.as_chat_model()
        if model is None:
            raise RuntimeError("The configured LLM client cannot expose a LangChain chat model for DeepAgents.")
        return model

    def _tools(self) -> list[Any]:
        if not self.research_toolkit or not self.research_toolkit.enabled:
            return []
        return self.research_toolkit.as_langchain_tools()

    def _subagents(self, tools: list[Any]) -> list[dict[str, Any]]:
        tool_by_name = {getattr(tool, "name", ""): tool for tool in tools}
        subagents: list[dict[str, Any]] = []
        for spec in self.profile.subagents.values():
            subagent: dict[str, Any] = {
                "name": spec.name,
                "description": spec.description,
                "system_prompt": spec.system_prompt,
            }
            resolved_tools = [tool_by_name[name] for name in spec.tools if name in tool_by_name]
            if resolved_tools:
                subagent["tools"] = resolved_tools
            if spec.model:
                subagent["model"] = spec.model
            subagents.append(subagent)
        return subagents

    def _prepare_workspace(self, output_dir: Path, run_id: str, part: BlogSeriesPart) -> Path:
        workspace = output_dir / "deepagent_workspaces" / run_id / f"part-{part.part_number}-{part.slug}"
        workspace.mkdir(parents=True, exist_ok=True)
        profile_dir = workspace / ".deepagent_profile"
        if profile_dir.exists():
            shutil.rmtree(profile_dir)
        profile_dir.mkdir(parents=True, exist_ok=True)
        memory_path = self.profile.root_dir / "AGENTS.md"
        if memory_path.exists():
            shutil.copy2(memory_path, profile_dir / "AGENTS.md")
        else:
            (profile_dir / "AGENTS.md").write_text(self.profile.memory, encoding="utf-8")
        skills_src = self.profile.root_dir / "skills"
        skills_dest = profile_dir / "skills"
        if skills_src.exists():
            shutil.copytree(skills_src, skills_dest)
        else:
            skills_dest.mkdir(parents=True, exist_ok=True)
        return workspace

    @staticmethod
    def _render_task(
        *,
        config: SeriesRunConfig,
        outline: BlogSeriesOutline,
        part: BlogSeriesPart,
        retrieved_guidance: SkillRetrievalResult,
    ) -> str:
        guidance = "\n".join(
            f"- {item}" for item in retrieved_guidance.retrieved_guidance
        ) or "- None"
        active_skill_ids = retrieved_guidance.retrieved_skill_ids or []
        active_skill_ids_json = json.dumps(active_skill_ids)
        outline_json = outline.model_dump_json(indent=2)
        return f"""
Build a complete, source-grounded blog chapter package.

Topic: {config.topic}
Audience: {config.target_audience}
Target length: {config.min_word_count}-{config.max_word_count} words
Part: {part.part_number}
Title: {part.title}
Slug: {part.slug}
Purpose: {part.purpose}

Series outline JSON:
```json
{outline_json}
```

Active retrieved guidance, visible and auditable:
{guidance}

Active skill IDs to preserve in `manifest.json`:
```json
{active_skill_ids_json}
```

Available DeepAgents optimization primitives:
- Use `research_sources` first for each chapter/section research pass because it performs search, credibility ranking, bounded fetching, and image metadata capture in one call.
- Use `chapter_researcher` for chapter-level source gathering.
- Use `section_researcher` for each substantial section before drafting that section.
- Use `visual_planner` to choose source images, Mermaid diagrams, charts, and image-generation specs.
- Use `code_designer` for implementation-heavy examples.
- Use `reviewer` for a strict final package check before returning.

Required workflow:
1. Use the DeepAgents todo/planning flow.
2. Create `plan.md` before writing prose. Include section goals, source needs, visual needs, and code/example needs.
3. Use the chapter_researcher and section_researcher subagents when research tools are available.
4. Research the chapter and each substantial section before drafting.
5. Preserve exact clickable source URLs from research in the relevant section.
6. Write the draft section-by-section. Each substantial section must include:
   - at least one source-backed explanation,
   - `#### Sources for This Section` with clickable links,
   - one useful Markdown image from a source when available, with `_Image credit: [name](url)_`,
   - otherwise a concrete Mermaid diagram or asset spec, not a vague placeholder,
   - code/config when implementation detail matters.
7. Run the reviewer subagent/checklist before the final response and fix the files if the package fails grounding, visuals, code, continuity, or skill-adherence checks.
8. Do not leave `[Image: A graph or diagram...]`, `example.com`, or "No explicit sources were captured" in the draft.
9. Keep approval history and memory concepts separate; only use the retrieved guidance shown above.

Write exactly these files at the workspace root:
- `research.md`: chapter and section research notes with source URLs and image URLs.
- `plan.md`: table of contents and per-section plan.
- `draft.md`: Medium-ready Markdown chapter.
- `assets.md`: image/diagram plan with source image credits and generation specs.
- `manifest.json`: JSON with keys `source_urls`, `image_urls`, `sections`, `active_skill_ids`, and `missing_evidence`.

The final answer should only summarize which files were written.
""".strip()

    @staticmethod
    def _last_message_text(result: Any) -> str:
        messages = result.get("messages", []) if isinstance(result, dict) else []
        for message in reversed(messages):
            content = getattr(message, "content", None)
            if content:
                return str(content)
        return str(result) if result is not None else ""

    @staticmethod
    def _read_expected_files(workspace: Path, *, fallback: str) -> dict[str, str]:
        files: dict[str, str] = {}
        for filename in ("research.md", "plan.md", "draft.md", "assets.md"):
            path = workspace / filename
            files[filename] = path.read_text(encoding="utf-8") if path.exists() else ""
        if not files["draft.md"].strip():
            files["draft.md"] = fallback
        if not files["research.md"].strip():
            files["research.md"] = "# Research Notes\n\nDeepAgents did not write research.md."
        if not files["plan.md"].strip():
            files["plan.md"] = "# Chapter Plan\n\nDeepAgents did not write plan.md."
        if not files["assets.md"].strip():
            files["assets.md"] = "# Asset Plan\n\nDeepAgents did not write assets.md."
        return files

    @staticmethod
    def _read_manifest(workspace: Path) -> dict[str, Any]:
        path = workspace / "manifest.json"
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"raw": path.read_text(encoding="utf-8")}


def deepagent_artifact_filename(part: BlogSeriesPart, *, suffix: str) -> str:
    """Return the canonical filename for DeepAgents sidecar artifacts."""

    return to_part_filename(part.part_number, part.slug, suffix=suffix)
