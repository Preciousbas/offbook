"""Unit tests for claim comparison (no Coasty required)."""

from __future__ import annotations

from offbook.compare import _claim_verdict, compare_reply, is_deflection
from offbook.ground_truth import _default_demo_claims


def _claims():
    return {c["id"]: c for c in _default_demo_claims()}


def test_returns_window_mismatch():
    q = {
        "id": "returns_01",
        "category": "returns",
        "question": "How many days?",
        "expected_claim_ids": ["returns_window_days"],
        "severity_hint": "high",
        "impact_template": "Bot '{bot}' vs '{truth}'",
    }
    finding = compare_reply(
        question=q,
        bot_reply="You have 14 days from delivery to return unused items for a full refund.",
        claims_by_id=_claims(),
    )
    assert finding["result"] == "mismatch"
    assert finding["severity"] == "high"


def test_competing_numbers_are_conflict_not_match():
    claim = _claims()["returns_window_days"]
    assert _claim_verdict("We offer both 14 and 30 day returns.", claim) == "conflict"


def test_avail_notify_me_is_match():
    claim = _claims()["stock_restock_notify"]
    assert (
        _claim_verdict(
            "Yes — use Notify Me on the product page for restock emails.",
            claim,
        )
        == "match"
    )


def test_summer20_stale_promo():
    q = {
        "id": "promo_01",
        "category": "promotions",
        "question": "SUMMER20?",
        "expected_claim_ids": ["promo_summer20_status"],
        "severity_hint": "high",
        "impact_template": "impact",
    }
    finding = compare_reply(
        question=q,
        bot_reply="Yes! You can still use SUMMER20 for 20% off your order.",
        claims_by_id=_claims(),
    )
    assert finding["result"] == "mismatch"


def test_impact_unknown_placeholder_does_not_crash():
    q = {
        "id": "price_01",
        "category": "pricing",
        "question": "price?",
        "expected_claim_ids": ["price_bestseller"],
        "severity_hint": "high",
        "impact_template": "Bot {bot} site {truth} and {oops}",
    }
    finding = compare_reply(
        question=q,
        bot_reply="Our bestseller is $99 right now.",
        claims_by_id=_claims(),
    )
    assert finding["result"] == "mismatch"
    assert finding["impact"]
    assert "{oops}" not in (finding["impact"] or "")


def test_deflection_detected():
    assert is_deflection("Please check our website FAQ for details.")


def test_holiday_sale_false_affirmation_is_mismatch():
    q = {
        "id": "edge_01",
        "category": "edge",
        "question": "holiday?",
        "expected_claim_ids": ["promo_holiday_live"],
        "severity_hint": "high",
        "impact_template": "x",
    }
    finding = compare_reply(
        question=q,
        bot_reply="Yes, the holiday sale is still running — enjoy the savings!",
        claims_by_id=_claims(),
    )
    assert finding["result"] == "mismatch"


def test_bool_true_not_treated_as_integer_one():
    """Regression: isinstance(True, int) is True in Python."""
    claim = _claims()["stock_bestseller"]
    assert (
        _claim_verdict(
            "Yes — the Trail Runner bestseller is in stock for sizes 8–12 and ships within 1 business day.",
            claim,
        )
        == "match"
    )


def test_no_restock_policy_is_match_not_denial():
    claim = _claims()["stock_clearance_limited"]
    assert (
        _claim_verdict(
            "Clearance is limited to stock on hand with no restock.",
            claim,
        )
        == "match"
    )
