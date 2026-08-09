"""Shared paths and config helpers."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

TARGETS_PATH = ROOT / "targets.yaml"
QUESTIONS_PATH = ROOT / "questions" / "ecommerce.yaml"
ARTIFACTS_DIR = ROOT / "artifacts"
SPIKES_DIR = ROOT / "spikes"
SAMPLES_DIR = ROOT / "samples"
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


def dry_run_enabled(explicit: bool | None = None) -> bool:
    if explicit is not None:
        return explicit
    if os.getenv("OFFBOOK_DRY_RUN", "").strip() in {"1", "true", "yes"}:
        return True
    key = os.getenv("COASTY_API_KEY", "").strip()
    if not key or "replace-me" in key:
        return True
    return False


def coasty_api_key() -> str | None:
    key = os.getenv("COASTY_API_KEY", "").strip()
    if not key or "replace-me" in key:
        return None
    return key


def coasty_base_url() -> str:
    return os.getenv("COASTY_BASE_URL", "https://coasty.ai/v1").rstrip("/")
