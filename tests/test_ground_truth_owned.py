"""Owned-demo money-shot ground truth must extract without Coasty."""

from __future__ import annotations

from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from offbook.config import ROOT
from offbook.ground_truth import (
    extract_claims_heuristic,
    merge_claims_prefer_heuristic,
)
from offbook.targets import load_questions

SITE = ROOT / "samples" / "owned_bot" / "site"


def _visible_text(html_path: Path) -> str:
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "lxml")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    return soup.get_text("\n", strip=True)


def _by_id(claims: list[dict]) -> dict[str, dict]:
    return {c["id"]: c for c in claims}


def test_returns_page_extracts_30_day_window():
    text = _visible_text(SITE / "pages" / "returns" / "index.html")
    claims = _by_id(
        extract_claims_heuristic(
            page_url="https://site-eight-eosin-21.vercel.app/pages/returns",
            page_text=text,
            category_hint="returns",
        )
    )
    assert "returns_window_days" in claims
    assert claims["returns_window_days"]["value"] == 30
    assert "shipping_standard_days" not in claims  # refund 5–10 days must not leak


def test_product_page_extracts_bestseller_price():
    text = _visible_text(SITE / "products" / "trail-runner" / "index.html")
    claims = _by_id(
        extract_claims_heuristic(
            page_url="https://site-eight-eosin-21.vercel.app/products/trail-runner",
            page_text=text,
            category_hint="pricing",
        )
    )
    assert "price_bestseller" in claims
    assert claims["price_bestseller"]["value"] in {128, 128.0}


def test_sale_page_extracts_fall15_and_expired_summer():
    text = _visible_text(SITE / "pages" / "sale" / "index.html")
    claims = _by_id(
        extract_claims_heuristic(
            page_url="https://site-eight-eosin-21.vercel.app/pages/sale",
            page_text=text,
            category_hint="promotions",
        )
    )
    assert claims["promo_current_code"]["value"] == "FALL15"
    assert claims["promo_summer20_status"]["value"] == "expired"
    assert "expired" in claims["promo_summer20_status"]["claim_text"].lower()


def test_homepage_summer20_expired_and_fall15():
    text = _visible_text(SITE / "index.html")
    claims = _by_id(
        extract_claims_heuristic(
            page_url="https://site-eight-eosin-21.vercel.app/",
            page_text=text,
            category_hint=None,
        )
    )
    assert claims["promo_current_code"]["value"] == "FALL15"
    assert claims["promo_summer20_status"]["value"] == "expired"
    assert claims["price_bestseller"]["value"] in {128, 128.0}
    assert claims["returns_window_days"]["value"] == 30


def test_merge_prefers_heuristic_over_thin_coasty():
    heuristic = [
        {
            "id": "price_bestseller",
            "claim_text": "Bestseller is $128.",
            "value": 128,
        }
    ]
    coasty = [
        {
            "id": "price_bestseller",
            "claim_text": "some price exists",
            "value": "unknown",
        },
        {
            "id": "tax_policy",
            "claim_text": "Applicable sales tax is calculated at checkout.",
            "value": "checkout",
        },
    ]
    merged = _by_id(merge_claims_prefer_heuristic(heuristic, coasty))
    assert merged["price_bestseller"]["value"] == 128
    assert "tax_policy" in merged


def test_demo_money_shots_bank_loads():
    path = ROOT / "questions" / "demo_money_shots.yaml"
    questions = load_questions(path)
    assert len(questions) == 5
    ids = {q["id"] for q in questions}
    assert {"price_01", "returns_01", "promo_01", "promo_04"}.issubset(ids)
