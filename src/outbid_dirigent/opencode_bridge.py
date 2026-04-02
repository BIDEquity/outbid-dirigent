"""
OpenCode Bridge — converts .opencode skills/agents to Claude Code plugin format.

When a target repo contains .opencode/skills/, this bridge:
1. Copies skills to a machine-wide cache dir (not in the repo)
2. Creates a Claude Code plugin structure (.claude-plugin/plugin.json + skills/)
3. Returns the plugin dir path for use with --plugin-dir

This lets dirigent's coder instances load project-specific conventions
that were originally written for OpenCode.
"""

import json
import re
import shutil
import unicodedata
from pathlib import Path
from typing import Optional

from loguru import logger


def _slugify(text: str, max_length: int = 50) -> str:
    """Convert text to filesystem-safe slug."""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii").lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text).strip("-")
    if len(text) > max_length:
        text = text[:max_length].rsplit("-", 1)[0]
    return text or "repo"


class OpenCodeBridge:
    """Converts .opencode skills and agents to a Claude Code plugin."""

    CACHE_BASE = Path.home() / ".cache" / "outbid-dirigent" / "opencode-plugins"

    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.opencode_dir = repo_path / ".opencode"
        self.skills_dir = self.opencode_dir / "skills"
        self.agents_dir = self.opencode_dir / "agents"

        slug = _slugify(repo_path.name)
        self.plugin_dir = self.CACHE_BASE / slug
        self._catalog: list[dict] = []

    def available(self) -> bool:
        """Check if the target repo has .opencode skills."""
        return self.skills_dir.is_dir() and any(self.skills_dir.iterdir())

    def convert(self) -> Optional[Path]:
        """Convert .opencode skills/agents to Claude plugin format.

        Returns the plugin directory path, or None if nothing to convert.
        Skips files that haven't changed since last conversion (mtime check).
        """
        if not self.available():
            return None

        target_skills = self.plugin_dir / "skills"
        target_skills.mkdir(parents=True, exist_ok=True)

        converted = 0
        self._catalog = []

        # Convert skills: .opencode/skills/{name}/SKILL.md → skills/{name}/SKILL.md
        for skill_dir in sorted(self.skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            src = skill_dir / "SKILL.md"
            if not src.exists():
                continue

            name = skill_dir.name
            dst_dir = target_skills / name
            dst = dst_dir / "SKILL.md"

            if self._needs_update(src, dst):
                dst_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                converted += 1

            meta = self._extract_frontmatter(dst if dst.exists() else src)
            self._catalog.append({
                "name": meta.get("name", name),
                "description": meta.get("description", ""),
                "type": "skill",
            })

        # Convert agents: .opencode/agents/{name}.md → skills/agent-{name}/SKILL.md
        if self.agents_dir.is_dir():
            for agent_file in sorted(self.agents_dir.glob("*.md")):
                name = f"agent-{agent_file.stem}"
                src = agent_file
                dst_dir = target_skills / name
                dst = dst_dir / "SKILL.md"

                if self._needs_update(src, dst):
                    dst_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
                    converted += 1

                meta = self._extract_frontmatter(dst if dst.exists() else src)
                self._catalog.append({
                    "name": meta.get("name", agent_file.stem),
                    "description": meta.get("description", "").split("\n")[0][:200],
                    "type": "agent",
                })

        if not self._catalog:
            return None

        # Write plugin manifest
        plugin_name = f"opencode-{_slugify(self.repo_path.name)}"
        manifest_dir = self.plugin_dir / ".claude-plugin"
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest = {
            "name": plugin_name,
            "description": f"Project conventions imported from {self.repo_path.name}/.opencode",
            "version": "1.0.0",
        }
        (manifest_dir / "plugin.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )

        skill_count = sum(1 for c in self._catalog if c["type"] == "skill")
        agent_count = sum(1 for c in self._catalog if c["type"] == "agent")
        logger.info(
            f"OpenCode bridge: {skill_count} skills, {agent_count} agents "
            f"→ {self.plugin_dir} ({converted} updated)"
        )

        return self.plugin_dir

    def skill_catalog(self) -> list[dict]:
        """Return catalog of available skills [{name, description, type}].

        Must call convert() first.
        """
        return self._catalog

    def plugin_name(self) -> str:
        """Return the plugin name (used for skill invocation: /plugin-name:skill-name)."""
        return f"opencode-{_slugify(self.repo_path.name)}"

    @staticmethod
    def _needs_update(src: Path, dst: Path) -> bool:
        """Check if source is newer than destination."""
        if not dst.exists():
            return True
        return src.stat().st_mtime > dst.stat().st_mtime

    @staticmethod
    def _extract_frontmatter(path: Path) -> dict:
        """Extract YAML frontmatter fields from a markdown file."""
        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            return {}

        if not content.startswith("---"):
            return {}

        end = content.find("---", 3)
        if end == -1:
            return {}

        frontmatter = content[3:end].strip()
        result = {}
        for line in frontmatter.split("\n"):
            if ":" in line and not line.startswith(" ") and not line.startswith("\t"):
                key, _, value = line.partition(":")
                key = key.strip()
                value = value.strip().strip(">-").strip()
                if value:
                    result[key] = value
        return result
