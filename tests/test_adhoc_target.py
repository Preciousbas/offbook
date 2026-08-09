"""Tests for ad-hoc --company/--url targets."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from offbook.ground_truth import build_ground_truth_for_target
from offbook.targets import make_public_target, normalize_base_url, resolve_audit_target, slugify


def test_slugify():
    assert slugify("Jumia Nigeria") == "jumia_nigeria"


def test_normalize_base_url_adds_https():
    assert normalize_base_url("www.jumia.com.ng") == "https://www.jumia.com.ng"
    assert normalize_base_url("https://www.jumia.com.ng/foo") == "https://www.jumia.com.ng"


def test_make_public_target_is_audit_only():
    target = make_public_target(company="Jumia Nigeria", url="https://www.jumia.com.ng")
    assert target["role"] == "public_audit"
    assert target["base_url"] == "https://www.jumia.com.ng"
    assert target["name"] == "Jumia Nigeria"
    assert target["id"] == "adhoc_jumia_nigeria"
    assert target["pages"]["returns"]


def test_make_public_target_page_overrides():
    target = make_public_target(
        company="Jumia Nigeria",
        url="https://www.jumia.com.ng",
        returns="https://www.jumia.com.ng/sp-returns",
        shipping="/delivery",
    )
    assert target["pages"]["returns"] == "https://www.jumia.com.ng/sp-returns"
    assert target["pages"]["shipping"] == "/delivery"


def test_resolve_requires_url_with_company():
    with pytest.raises(ValueError, match="requires --url"):
        resolve_audit_target(company="Jumia Nigeria")


def test_resolve_url_without_company_uses_host():
    target = resolve_audit_target(url="https://www.jumia.com.ng")
    assert target["name"] == "www.jumia.com.ng"
    assert target["role"] == "public_audit"


def test_adhoc_refuses_silent_sample_fallback():
    """Ad-hoc audits must not score against Offbook Demo Store sample claims."""
    target = make_public_target(company="Jumia Nigeria", url="https://www.jumia.com.ng")
    assert target["status"] == "adhoc"

    def boom(*_args, **_kwargs):
        raise ConnectionError("unreachable")

    with patch("offbook.ground_truth.fetch_page_text", side_effect=boom):
        with pytest.raises(ConnectionError):
            build_ground_truth_for_target(
                target,
                dry_run=True,
                use_sample_fallback=False,
            )
