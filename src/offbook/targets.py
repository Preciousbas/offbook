"""Load targets and question bank."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

from offbook.config import QUESTIONS_PATH, TARGETS_PATH

# Sensible defaults for ad-hoc --url audits (failed fetches are skipped in ground_truth).
DEFAULT_ADHOC_PAGES = {
    "pricing": "/collections/all",
    "returns": "/pages/returns",
    "shipping": "/pages/shipping",
    "promotions": "/pages/sale",
}


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}")
    return data


def load_targets(path: Path = TARGETS_PATH) -> list[dict[str, Any]]:
    data = load_yaml(path)
    targets = data.get("targets") or []
    if not isinstance(targets, list):
        raise ValueError("targets.yaml must contain a targets list")
    return targets


def get_target(target_id: str, path: Path = TARGETS_PATH) -> dict[str, Any]:
    for target in load_targets(path):
        if target.get("id") == target_id:
            return target
    known = ", ".join(t.get("id", "?") for t in load_targets(path))
    raise KeyError(f"Unknown target {target_id!r}. Known: {known}")


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")
    return slug or "site"


def normalize_base_url(url: str) -> str:
    raw = url.strip()
    if not raw.startswith(("http://", "https://")):
        raw = "https://" + raw
    parsed = urlparse(raw)
    if not parsed.netloc:
        raise ValueError(f"Invalid URL: {url!r}")
    return f"{parsed.scheme}://{parsed.netloc}"


def make_public_target(
    *,
    url: str,
    company: str | None = None,
    returns: str | None = None,
    shipping: str | None = None,
    pricing: str | None = None,
    promotions: str | None = None,
) -> dict[str, Any]:
    """
    Build an ephemeral public_audit target from a company name + site URL.

    Always role=public_audit — Offbook is audit-only; KB edits stay manual.
    """
    base_url = normalize_base_url(url)
    host = urlparse(base_url).netloc
    name = (company or host).strip() or host
    pages = dict(DEFAULT_ADHOC_PAGES)
    overrides = {
        "returns": returns,
        "shipping": shipping,
        "pricing": pricing,
        "promotions": promotions,
    }
    for key, value in overrides.items():
        if value:
            pages[key] = value

    return {
        "id": f"adhoc_{slugify(name)}",
        "name": name,
        "role": "public_audit",
        "base_url": base_url,
        "pages": pages,
        "status": "adhoc",
        "spike_widget": "pending",
        "widget_notes": "Ad-hoc target from --company/--url (audit-only)",
    }


def resolve_audit_target(
    *,
    target_id: str | None = None,
    company: str | None = None,
    url: str | None = None,
    returns: str | None = None,
    shipping: str | None = None,
    pricing: str | None = None,
    promotions: str | None = None,
) -> dict[str, Any]:
    """Prefer --url ad-hoc target; otherwise load --target from targets.yaml."""
    if url:
        return make_public_target(
            url=url,
            company=company,
            returns=returns,
            shipping=shipping,
            pricing=pricing,
            promotions=promotions,
        )
    if company and not url:
        raise ValueError(
            "--company requires --url "
            "(e.g. --company 'Jumia Nigeria' --url https://www.jumia.com.ng)"
        )
    if not target_id:
        raise ValueError("Provide --target <id> or --url <site> (with optional --company)")
    return get_target(target_id)


def load_questions(path: Path | None = None) -> list[dict[str, Any]]:
    """Load a question bank YAML. Defaults to questions/ecommerce.yaml."""
    questions_path = Path(path) if path is not None else QUESTIONS_PATH
    if not questions_path.is_file():
        raise FileNotFoundError(f"Questions file not found: {questions_path}")
    data = load_yaml(questions_path)
    questions = data.get("questions") or []
    if not isinstance(questions, list):
        raise ValueError(f"{questions_path} must contain a questions list")
    for i, q in enumerate(questions):
        if not isinstance(q, dict):
            raise ValueError(f"Question #{i} in {questions_path} must be a mapping")
        for key in ("id", "question"):
            if not q.get(key):
                raise ValueError(
                    f"Question #{i} in {questions_path} missing required field {key!r}"
                )
    return questions
