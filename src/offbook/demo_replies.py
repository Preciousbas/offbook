"""Dry-run demo replies for the owned Offbook store (audit rehearsal)."""

from __future__ import annotations

# Intentionally stale answers planted in the owned demo bot.
STALE_REPLIES: dict[str, str] = {
    "returns_01": "You have 14 days from delivery to return unused items for a full refund.",
    "promo_01": "Yes! You can still use SUMMER20 for 20% off your order.",
    "edge_01": "Yes, the holiday sale is still running — enjoy the savings!",
    "edge_03": "Absolutely — just ask support and they can manually apply last month's discount.",
    "price_01": "Our bestseller is $99 right now.",
    "promo_04": "The current homepage code is SUMMER20.",
}

# Correct baseline answers for non-stale dry-run questions.
TRUTHFUL_REPLIES: dict[str, str] = {
    "price_02": "US sales tax is calculated at checkout based on your shipping destination.",
    "price_03": "There is no automatic multi-buy discount unless a product page explicitly marks a bundle deal.",
    "price_04": "Listed prices exclude tax and shipping — those are added at checkout.",
    "price_05": "We don't have a separate member price list; email subscribers just get occasional promo codes.",
    "returns_02": "Yes — opened but unused items can be returned within the 30-day window if they're in original condition.",
    "returns_03": "For change-of-mind returns, customers are responsible for return shipping.",
    "returns_04": "Final-sale and clearance items are non-refundable.",
    "returns_05": "Refunds usually post within 5–10 business days after we receive the return.",
    "promo_02": "Free shipping over $75 applies to full-price merchandise only — not sale items.",
    "promo_03": "Promo codes cannot be stacked with sitewide sales.",
    "promo_04": "The current active code is FALL15 for 15% off full-price items.",
    "promo_05": "The welcome discount excludes already-reduced / sale items.",
    "ship_01": "Standard shipping usually takes 3–7 business days once an order ships.",
    "ship_02": "Free standard shipping starts on orders over $75.",
    "ship_03": "We currently ship to the United States and Canada only.",
    "ship_04": "Orders placed before 12 PM local warehouse time on business days ship the same day.",
    "ship_05": "Standard domestic is USPS; expedited upgrades use UPS.",
    "avail_01": "Yes — the Trail Runner bestseller is in stock for sizes 8–12 and ships within 1 business day.",
    "avail_02": "Backordered items typically ship in 2–4 weeks.",
    "avail_03": "Preorders are only available on products marked Preorder.",
    "avail_04": "Yes — use Notify Me on the product page for restock emails.",
    "avail_05": "Clearance is limited to stock on hand with no restock.",
    "edge_02": "Gift cards do not expire, so a two-year-old balance is still valid.",
    "edge_04": "The price shown at checkout is binding; chatbot quotes are informational only.",
    "edge_05": "Yes — gifts can be returned with the packing slip even without the original order number (merchandise credit).",
}


def dry_run_reply(target_id: str, role: str | None, question_id: str) -> str:
    owned = role == "owned_fix" or target_id == "owned_fix"
    if owned and question_id in STALE_REPLIES:
        return STALE_REPLIES[question_id]
    if question_id in TRUTHFUL_REPLIES:
        # Public audit dry-run: keep a few stale gotchas visible
        if not owned and question_id in {"returns_01", "promo_01", "edge_01", "price_01"}:
            return STALE_REPLIES.get(question_id, TRUTHFUL_REPLIES[question_id])
        return TRUTHFUL_REPLIES[question_id]
    if not owned and (question_id.startswith("ship_") or question_id.startswith("avail_")):
        return "Please check our website FAQ for the latest details on that."
    return "Thanks for asking — that matches our published store policy pages."
