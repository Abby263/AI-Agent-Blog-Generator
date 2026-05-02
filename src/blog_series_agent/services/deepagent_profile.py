"""DeepAgents-style filesystem profile loading.

The DeepAgents content-builder example keeps agent behavior in filesystem
primitives: memory, skills, and subagent definitions. This service brings the
same operating model into the existing LangGraph pipeline without replacing
the graph orchestration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(slots=True)
class DeepAgentSkill:
    """A workflow skill loaded from skills/<name>/SKILL.md."""

    name: str
    description: str
    content: str
    path: Path
    stages: list[str] = field(default_factory=list)


@dataclass(slots=True)
class DeepAgentSubagent:
    """A subagent role declaration loaded from subagents.yaml."""

    name: str
    description: str
    system_prompt: str
    tools: list[str] = field(default_factory=list)
    model: str | None = None


@dataclass(slots=True)
class DeepAgentProfile:
    """Loaded DeepAgents-style profile for the blog-series pipeline."""

    root_dir: Path
    memory: str
    skills: list[DeepAgentSkill]
    subagents: dict[str, DeepAgentSubagent]

    def guidance_for(self, *, stage: str, subagent_name: str | None = None) -> str:
        """Render auditable guidance for a graph stage."""
        sections = ["## Agent Memory", self.memory.strip()]
        if subagent_name and subagent_name in self.subagents:
            subagent = self.subagents[subagent_name]
            sections.extend(
                [
                    f"## Subagent Role: {subagent.name}",
                    subagent.description.strip(),
                    subagent.system_prompt.strip(),
                ]
            )

        matching_skills = [
            skill for skill in self.skills if not skill.stages or stage in skill.stages
        ]
        if matching_skills:
            sections.append("## Loaded Skills")
            for skill in matching_skills:
                sections.append(f"### {skill.name}")
                if skill.description:
                    sections.append(skill.description.strip())
                sections.append(skill.content.strip())

        return "\n\n".join(section for section in sections if section.strip())


class DeepAgentProfileLoader:
    """Loads DeepAgents-style memory, skills, and subagent files from disk."""

    def __init__(self, root_dir: str | Path | None = None) -> None:
        if root_dir is None:
            root_dir = Path(__file__).resolve().parents[1] / "deepagent"
        self.root_dir = Path(root_dir)

    def load(self) -> DeepAgentProfile:
        """Load the profile from AGENTS.md, skills/*/SKILL.md, and subagents.yaml."""
        memory_path = self.root_dir / "AGENTS.md"
        memory = memory_path.read_text(encoding="utf-8") if memory_path.exists() else ""
        return DeepAgentProfile(
            root_dir=self.root_dir,
            memory=memory,
            skills=self._load_skills(),
            subagents=self._load_subagents(),
        )

    def _load_skills(self) -> list[DeepAgentSkill]:
        skills_dir = self.root_dir / "skills"
        if not skills_dir.exists():
            return []

        skills: list[DeepAgentSkill] = []
        for path in sorted(skills_dir.glob("*/SKILL.md")):
            raw = path.read_text(encoding="utf-8")
            metadata, content = _split_frontmatter(raw)
            skills.append(
                DeepAgentSkill(
                    name=str(metadata.get("name") or path.parent.name),
                    description=str(metadata.get("description") or ""),
                    content=content,
                    path=path,
                    stages=[str(stage) for stage in metadata.get("stages", [])],
                )
            )
        return skills

    def _load_subagents(self) -> dict[str, DeepAgentSubagent]:
        path = self.root_dir / "subagents.yaml"
        if not path.exists():
            return {}
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        subagents: dict[str, DeepAgentSubagent] = {}
        for name, spec in raw.items():
            subagents[str(name)] = DeepAgentSubagent(
                name=str(name),
                description=str(spec.get("description", "")),
                system_prompt=str(spec.get("system_prompt", "")),
                tools=[str(tool) for tool in spec.get("tools", [])],
                model=spec.get("model"),
            )
        return subagents


def _split_frontmatter(raw: str) -> tuple[dict[str, Any], str]:
    if not raw.startswith("---"):
        return {}, raw
    parts = raw.split("---", maxsplit=2)
    if len(parts) < 3:
        return {}, raw
    metadata = yaml.safe_load(parts[1]) or {}
    return metadata, parts[2].strip()
