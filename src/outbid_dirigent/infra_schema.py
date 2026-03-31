"""Pydantic schemas for tiered infrastructure detection."""
from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Optional
import json
from pydantic import BaseModel

class InfraTier(str, Enum):
    DEVBOX = "1_devbox"
    DOCKER_COMPOSE = "2_docker_compose"
    CI_EXTRACTED = "3_ci_extracted"
    MOCKED = "4_mocked"
    GENERATED_DEVBOX = "5_generated_devbox"
    GENERATED_COMPOSE = "6_generated_compose"
    NONE = "7_none"

class ServiceGap(BaseModel):
    service: str
    port: Optional[int] = None
    reason: str
    suggested_fix: str

class SeedInfo(BaseModel):
    command: str = ""
    detection_confidence: str = "none"  # high | medium | none — how reliably the seed command was detected
    ran: bool = False
    error: str = ""

class InfraContext(BaseModel):
    tier: InfraTier = InfraTier.NONE
    services_started: list[str] = []
    confidence: str = "static"  # e2e | integration | unit | mocked | static | none
    gaps: list[ServiceGap] = []
    seed: SeedInfo = SeedInfo()
    generated_files: list[str] = []
    tests_run: int = 0
    tests_skipped_infra: int = 0
    caveat: Optional[str] = None

    @classmethod
    def load(cls, path: Path) -> Optional["InfraContext"]:
        """Load and validate from JSON file. Returns None if missing or invalid."""
        try:
            if not path.exists():
                return None
            raw = json.loads(path.read_text(encoding="utf-8"))
            return cls.model_validate(raw)
        except Exception:
            return None

    def save(self, path: Path) -> None:
        """Serialize to JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            self.model_dump_json(indent=2),
            encoding="utf-8",
        )
