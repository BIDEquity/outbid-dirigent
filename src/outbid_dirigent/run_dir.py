"""
RunDir — manages execution artifact storage in $HOME/.dirigent/runs/<run-id>/.

Each dirigent run gets an isolated directory under the user's home.
The target repo only stores a tiny manifest.json pointing to the run dir.
"""

import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from loguru import logger


# Where all runs live. Dirigent runs as a standalone process (not inside claude),
# so we use a fixed home-dir location. Skills find the exact run via $DIRIGENT_RUN_DIR
# which we set in the subprocess environment.
def _get_runs_root() -> Path:
    return Path.home() / ".dirigent" / "runs"

# Subdirectories created inside each run dir
_SUBDIRS = ["summaries", "reviews", "contracts", "logs", "hooks"]


def _short_hash(content: str, length: int = 8) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:length]


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _get_commit_sha(repo_path: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_path, capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def _ensure_gitignore(repo_path: Path) -> None:
    """Ensure .dirigent/ is in .gitignore."""
    gitignore = repo_path / ".gitignore"
    marker = ".dirigent/"

    if gitignore.exists():
        content = gitignore.read_text(encoding="utf-8")
        if marker in content:
            return
        # Append
        if not content.endswith("\n"):
            content += "\n"
        content += f"\n# Dirigent run manifest\n{marker}\n"
        gitignore.write_text(content, encoding="utf-8")
    else:
        gitignore.write_text(f"# Dirigent run manifest\n{marker}\n", encoding="utf-8")

    logger.info(f"Added {marker} to .gitignore")


class RunDir:
    """Manages a single run's artifact directory.

    Lifecycle:
        run_dir = RunDir.create(repo_path, spec_content)  # new run
        run_dir = RunDir.load(repo_path)                   # resume existing run

    Access:
        run_dir.path          # ~/.dirigent/runs/<id>/
        run_dir.path / "PLAN.json"
        run_dir.run_id
    """

    def __init__(self, run_id: str, path: Path, repo_path: Path, manifest_path: Path):
        self.run_id = run_id
        self.path = path
        self.repo_path = repo_path
        self.manifest_path = manifest_path

        # Set env var so subprocess skills can find the run dir
        os.environ["DIRIGENT_RUN_DIR"] = str(self.path)

    @classmethod
    def create(cls, repo_path: Path, spec_content: str) -> "RunDir":
        """Create a new run directory and write the manifest."""
        repo_path = repo_path.resolve()
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        content_hash = _short_hash(spec_content)
        run_id = f"{timestamp}-{content_hash}"

        run_path = _get_runs_root() / run_id
        run_path.mkdir(parents=True, exist_ok=True)

        for subdir in _SUBDIRS:
            (run_path / subdir).mkdir(exist_ok=True)

        # Write manifest in repo
        manifest_dir = repo_path / ".dirigent"
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = manifest_dir / "manifest.json"

        manifest = {
            "run_id": run_id,
            "run_dir": str(run_path),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "commit_sha": _get_commit_sha(repo_path),
            "repo_path": str(repo_path),
            "files": {},
        }
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        _ensure_gitignore(repo_path)

        logger.info(f"Created run dir: {run_path}")
        return cls(run_id, run_path, repo_path, manifest_path)

    @classmethod
    def load(cls, repo_path: Path) -> Optional["RunDir"]:
        """Load an existing run from the repo's manifest.json."""
        repo_path = repo_path.resolve()
        manifest_path = repo_path / ".dirigent" / "manifest.json"

        if not manifest_path.exists():
            return None

        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to read manifest.json: {e}")
            return None

        run_id = manifest.get("run_id", "")

        if not run_id:
            logger.error("manifest.json missing run_id")
            return None

        # Reconstruct from current home — never trust stored absolute paths
        # (manifest may have been written on a different machine)
        run_path = _get_runs_root() / run_id
        if not run_path.exists():
            logger.warning(f"Run dir {run_path} does not exist — creating fresh")
            run_path.mkdir(parents=True, exist_ok=True)
            for subdir in _SUBDIRS:
                (run_path / subdir).mkdir(exist_ok=True)

        return cls(run_id, run_path, repo_path, manifest_path)

    def update_manifest_hashes(self) -> None:
        """Scan all files in the run dir and update content hashes in manifest."""
        manifest = self._read_manifest()
        files = {}

        for f in sorted(self.path.rglob("*")):
            if f.is_file():
                rel = str(f.relative_to(self.path))
                files[rel] = {
                    "sha256": _file_sha256(f),
                    "updated_at": datetime.fromtimestamp(
                        f.stat().st_mtime, tz=timezone.utc
                    ).isoformat(),
                }

        manifest["files"] = files
        self._write_manifest(manifest)

    def track_file(self, relative_path: str) -> None:
        """Update hash for a single file in the manifest."""
        full_path = self.path / relative_path
        if not full_path.exists():
            return

        manifest = self._read_manifest()
        manifest.setdefault("files", {})[relative_path] = {
            "sha256": _file_sha256(full_path),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self._write_manifest(manifest)

    def _read_manifest(self) -> dict:
        try:
            return json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except Exception:
            return {"run_id": self.run_id, "run_dir": str(self.path), "files": {}}

    def _write_manifest(self, manifest: dict) -> None:
        self.manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
