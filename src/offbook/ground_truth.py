"""Extract checkable ground-truth claims from ecommerce policy/pricing pages."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from offbook.coasty_client import CoastyClient
from offbook.config import PROMPTS_DIR
from offbook.reply_clean import clean_policy_text

CLAIM_ID_HINTS: list[tuple[str, str, re.Pattern[str]]] = [
    # Returns — tolerate "unused items" / "of delivery" between the verb and the number.
    ("returns_window_days", "returns", re.compile(
        r"(?:return|returns)\s+(?:unused\s+items\s+)?within\s+(\d+)\s*days?", re.I
    )),
    ("returns_window_days", "returns", re.compile(
        r"unused\s+items\s+within\s+(\d+)\s*days?", re.I
    )),
    ("returns_window_days", "returns", re.compile(
        r"within\s+(\d+)\s*days?\s+of\s+delivery", re.I
    )),
    ("returns_window_days", "returns", re.compile(
        r"(\d+)\s*[-–]?\s*day[s]?\s+(?:return|refund)", re.I
    )),
    ("returns_window_days", "returns", re.compile(
        r"return(?:s|ed)?\s+within\s+(\d+)\s*days?", re.I
    )),
    # Pricing — bestseller / product price (owned demo: Trail Runner $128).
    ("price_bestseller", "pricing", re.compile(
        r"(?:Trail\s+Runner|bestseller|best[- ]selling)[^\n$]{0,80}\$\s*(\d+(?:\.\d{2})?)",
        re.I,
    )),
    ("price_bestseller", "pricing", re.compile(
        r"\$\s*(\d+(?:\.\d{2})?)\s*(?:before\s+tax|before tax and shipping)",
        re.I,
    )),
    ("shipping_free_threshold", "shipping", re.compile(
        r"free\s+(?:standard\s+)?shipping\s+(?:on\s+)?(?:orders\s+)?(?:over|above)\s+\$?\s*(\d+)",
        re.I,
    )),
    ("shipping_standard_days", "shipping", re.compile(
        r"(?:standard\s+shipping|ships?(?:\s+within)?)\s*.{0,40}?(\d+)\s*[-–]\s*(\d+)\s*business\s+days",
        re.I,
    )),
    ("shipping_standard_days", "shipping", re.compile(
        r"(\d+)\s*[-–]\s*(\d+)\s*business\s+days", re.I
    )),
    # Promotions — prefer "Use/Apply/Current code: FALL15"; keep SUMMER20 separate.
    ("promo_current_code", "promotions", re.compile(
        r"(?:current\s+)?code[:\s]+([A-Z][A-Z0-9]{3,15})\b", re.I
    )),
    ("promo_current_code", "promotions", re.compile(
        r"\b(?:Use|Apply)\s+([A-Z][A-Z0-9]{3,15})\b", re.I
    )),
    ("promo_current_code", "promotions", re.compile(r"\b(FALL15)\b")),
    ("promo_summer20_status", "promotions", re.compile(r"\bSUMMER20\b")),
    ("promo_summer20_status", "promotions", re.compile(r"summer\s+promo\s+ended", re.I)),
    ("tax_policy", "pricing", re.compile(r"sales\s+tax|VAT|tax\s+calculated", re.I)),
    ("returns_shipping_payer", "returns", re.compile(
        r"(customer|buyer|you)\s+(?:are\s+)?responsible\s+for\s+return\s+shipping", re.I
    )),
    ("returns_final_sale", "returns", re.compile(r"final\s+sale|non[- ]?refundable", re.I)),
    ("returns_refund_timing", "returns", re.compile(
        r"refund[s]?\s+(?:appear\s+in|within|in)\s+(\d+)\s*(?:[-–]\s*\d+\s*)?(?:business\s+)?days?",
        re.I,
    )),
    ("shipping_international", "shipping", re.compile(
        r"international\s+shipping|we\s+(?:currently\s+)?ship\s+(?:worldwide|to)|US\s*&\s*Canada",
        re.I,
    )),
    ("gift_card_expiry", "edge", re.compile(r"gift\s+cards?\s+(?:do\s+not\s+expire|expir)", re.I)),
]

# When a page has a category hint, skip other categories so refund "5–10 business days"
# does not become a shipping claim on the returns page.
_CROSS_CATEGORY_OK = frozenset({"tax_policy", "gift_card_expiry"})


def fetch_page_text(url: str, timeout: float = 30.0) -> tuple[str, str]:
    """Return (final_url, visible_text)."""
    with httpx.Client(follow_redirects=True, timeout=timeout, headers={"User-Agent": "offbook/0.1"}) as client:
        resp = client.get(url)
        resp.raise_for_status()
        html = resp.text
        final = str(resp.url)
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    text = re.sub(r"\n{3,}", "\n\n", soup.get_text("\n", strip=True))
    return final, text


def extract_claims_heuristic(
    *,
    page_url: str,
    page_text: str,
    category_hint: str | None = None,
) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc).isoformat()
    claims: list[dict[str, Any]] = []
    seen: set[str] = set()

    for claim_id, category, pattern in CLAIM_ID_HINTS:
        if (
            category_hint
            and category != category_hint
            and claim_id not in _CROSS_CATEGORY_OK
        ):
            continue
        match = pattern.search(page_text)
        if not match:
            continue
        if claim_id in seen:
            continue
        quote = _quote_around(page_text, match.start(), match.end())
        value: Any
        unit: str | None = None
        if claim_id == "returns_window_days" and match.lastindex:
            value = int(match.group(1))
            unit = "days"
            claim_text = f"Returns accepted within {value} days."
        elif claim_id == "price_bestseller" and match.lastindex:
            raw = match.group(1)
            value = float(raw) if "." in raw else int(raw)
            unit = "USD"
            claim_text = f"Bestseller (Trail Runner) is ${raw} before tax and shipping."
        elif claim_id == "shipping_free_threshold" and match.lastindex:
            value = int(match.group(1))
            claim_text = f"Free shipping on orders over ${value}."
        elif claim_id == "shipping_standard_days" and match.lastindex and match.lastindex >= 2:
            # Skip refund-timing ranges when they land on a shipping-hinted page without
            # shipping language (category filter usually prevents this on returns pages).
            if re.search(r"refund", quote, re.I) and not re.search(r"ship", quote, re.I):
                continue
            value = {"min_days": int(match.group(1)), "max_days": int(match.group(2))}
            claim_text = f"Standard shipping takes {match.group(1)}-{match.group(2)} business days."
        elif claim_id == "promo_current_code":
            value = str(match.group(1)).upper()
            if value == "SUMMER20":
                # Expired/legacy code — handled by promo_summer20_status.
                continue
            claim_text = f"Current promo code is {value}."
        elif claim_id == "promo_summer20_status":
            expired = bool(
                re.search(r"expir|ended|invalid|no longer", quote, re.I)
                or re.search(r"summer\s+promo\s+ended", match.group(0), re.I)
            )
            value = "expired" if expired else "mentioned"
            claim_text = (
                "SUMMER20 has expired."
                if expired
                else "Page mentions SUMMER20."
            )
        elif claim_id == "tax_policy":
            value = "checkout"
            claim_text = "Applicable sales tax is calculated at checkout."
        elif claim_id == "returns_shipping_payer":
            value = "customer"
            claim_text = "Customer pays return shipping on change-of-mind returns."
        elif claim_id == "returns_final_sale":
            value = False
            claim_text = "Final-sale and clearance items are non-refundable."
        elif claim_id == "returns_refund_timing" and match.lastindex:
            value = int(match.group(1))
            claim_text = f"Refunds post within about {value} business days after receipt."
        elif claim_id == "shipping_international":
            value = ["US", "CA"] if re.search(r"canada|united states|\bUS\b", quote, re.I) else "mentioned"
            claim_text = clean_policy_text(quote)[:200] or "Shipping destinations are listed on the shipping policy page."
        elif claim_id == "gift_card_expiry":
            value = False
            claim_text = "Gift cards never expire." if re.search(r"never expire|do not expire", quote, re.I) else clean_policy_text(quote)[:200]
        else:
            value = match.group(0)
            claim_text = clean_policy_text(quote)[:200] or match.group(0)

        claims.append(
            {
                "id": claim_id,
                "category": category,
                "claim_text": claim_text,
                "value": value,
                "unit": unit,
                "source_url": page_url,
                "source_quote": clean_policy_text(quote)[:280],
                "checked_at": now,
            }
        )
        seen.add(claim_id)

    return claims


def merge_claims_prefer_heuristic(
    heuristic: list[dict[str, Any]],
    coasty: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Keep heuristic IDs (money shots); only fill gaps from Coasty."""
    by_id: dict[str, dict[str, Any]] = {str(c["id"]): c for c in heuristic if c.get("id")}
    for claim in coasty:
        cid = str(claim.get("id") or "")
        if cid and cid not in by_id:
            by_id[cid] = claim
    return list(by_id.values())


def extract_claims_with_coasty(
    *,
    page_url: str,
    page_text: str,
    client: CoastyClient,
    dry_run: bool = False,
    category_hint: str | None = None,
) -> list[dict[str, Any]]:
    """Heuristics first; Coasty only fills missing claim IDs (never overwrites)."""
    heuristic = extract_claims_heuristic(
        page_url=page_url,
        page_text=page_text,
        category_hint=category_hint,
    )
    if dry_run or not client.available:
        return heuristic

    prompt_path = PROMPTS_DIR / "extract_claims.txt"
    template = prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else (
        "Extract checkable ecommerce facts as JSON array of claims."
    )
    task = template.format(page_url=page_url, page_text=page_text[:12000])

    result = client.run_task(
        task,
        dry_run=False,
        max_steps=25,
        instructions="Return ONLY a JSON array of claim objects. No markdown.",
        metadata={"offbook": "extract_claims"},
    )
    parsed = _parse_claims_json(result.result_text or "")
    if not parsed:
        return heuristic

    now = datetime.now(timezone.utc).isoformat()
    cleaned: list[dict[str, Any]] = []
    for claim in parsed:
        claim.setdefault("source_url", page_url)
        claim.setdefault("checked_at", now)
        claim["claim_text"] = clean_policy_text(str(claim.get("claim_text") or ""))
        quote = clean_policy_text(str(claim.get("source_quote") or claim.get("claim_text") or ""))
        claim["source_quote"] = quote[:280]
        if claim.get("id") == "tax_policy" and "tax" in (claim.get("claim_text") or "").lower():
            claim["claim_text"] = "Applicable sales tax is calculated at checkout."
        if claim.get("claim_text"):
            cleaned.append(claim)
    if not cleaned:
        return heuristic
    return merge_claims_prefer_heuristic(heuristic, cleaned)


def build_ground_truth_for_target(
    target: dict[str, Any],
    *,
    client: CoastyClient | None = None,
    dry_run: bool = True,
    use_sample_fallback: bool = True,
) -> list[dict[str, Any]]:
    """Fetch configured pages and merge claims."""
    base = str(target.get("base_url") or "").rstrip("/")
    pages = target.get("pages") or {}
    client = client or CoastyClient()
    all_claims: dict[str, dict[str, Any]] = {}

    for key, path in pages.items():
        if not path:
            continue
        url = path if str(path).startswith("http") else urljoin(base + "/", str(path).lstrip("/"))
        category_hint = {
            "pricing": "pricing",
            "returns": "returns",
            "shipping": "shipping",
            "promotions": "promotions",
        }.get(str(key), None)
        try:
            final_url, text = fetch_page_text(url)
            claims = extract_claims_with_coasty(
                page_url=final_url,
                page_text=text,
                client=client,
                dry_run=dry_run,
                category_hint=category_hint,
            )
            if category_hint:
                for c in claims:
                    if not c.get("category"):
                        c["category"] = category_hint
            for c in claims:
                all_claims[c["id"]] = c
        except Exception as exc:  # noqa: BLE001 — continue other pages
            if not use_sample_fallback:
                raise
            # Placeholder / unreachable URLs are expected until Spike 1 picks real targets
            _ = exc

    if not all_claims and use_sample_fallback:
        sample = _load_sample_claims()
        return sample

    if not all_claims and not use_sample_fallback:
        raise RuntimeError(
            "No claims extracted from configured policy/pricing pages. "
            "Pass --returns/--shipping/--pricing/--promotions with real URLs, "
            "or fix the target pages. Refusing sample-claim fallback for this target."
        )

    return list(all_claims.values())


def claims_to_markdown(claims: list[dict[str, Any]]) -> str:
    lines = ["# Ground truth claims", ""]
    by_cat: dict[str, list[dict[str, Any]]] = {}
    for c in claims:
        by_cat.setdefault(str(c.get("category") or "other"), []).append(c)
    for cat in sorted(by_cat):
        lines.append(f"## {cat}")
        lines.append("")
        for c in by_cat[cat]:
            lines.append(f"- **{c['id']}**: {c.get('claim_text')}")
            lines.append(f"  - source: {c.get('source_url')}")
            quote = (c.get("source_quote") or "").replace("\n", " ")
            lines.append(f"  - quote: {quote[:200]}")
        lines.append("")
    return "\n".join(lines)


def _quote_around(text: str, start: int, end: int, radius: int = 120) -> str:
    lo = max(0, start - radius)
    hi = min(len(text), end + radius)
    return re.sub(r"\s+", " ", text[lo:hi]).strip()


def _parse_claims_json(text: str) -> list[dict[str, Any]]:
    text = text.strip()
    if not text:
        return []
    # Strip markdown fences if present
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Try to find first array
        match = re.search(r"\[[\s\S]*\]", text)
        if not match:
            return []
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return []
    if isinstance(data, dict) and "claims" in data:
        data = data["claims"]
    if not isinstance(data, list):
        return []
    out: list[dict[str, Any]] = []
    for item in data:
        if isinstance(item, dict) and item.get("id") and item.get("claim_text"):
            out.append(item)
    return out


def _load_sample_claims() -> list[dict[str, Any]]:
    from offbook.config import SAMPLES_DIR

    path = SAMPLES_DIR / "claims" / "demo_store_claims.json"
    if not path.exists():
        return _default_demo_claims()
    return json.loads(path.read_text(encoding="utf-8"))


def _default_demo_claims() -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc).isoformat()
    base = "https://offbook-demo.example"
    return [
        {
            "id": "returns_window_days",
            "category": "returns",
            "claim_text": "Returns accepted within 30 days of delivery.",
            "value": 30,
            "unit": "days",
            "source_url": f"{base}/pages/returns",
            "source_quote": "You may return unused items within 30 days of delivery for a full refund.",
            "checked_at": now,
        },
        {
            "id": "returns_opened",
            "category": "returns",
            "claim_text": "Opened but unused items may be returned within the return window.",
            "value": True,
            "unit": None,
            "source_url": f"{base}/pages/returns",
            "source_quote": "Opened packaging is OK if the product is unused and in original condition.",
            "checked_at": now,
        },
        {
            "id": "returns_shipping_payer",
            "category": "returns",
            "claim_text": "Customer pays return shipping on change-of-mind returns.",
            "value": "customer",
            "unit": None,
            "source_url": f"{base}/pages/returns",
            "source_quote": "Customers are responsible for return shipping on change-of-mind returns.",
            "checked_at": now,
        },
        {
            "id": "returns_final_sale",
            "category": "returns",
            "claim_text": "Final-sale and clearance items are non-refundable.",
            "value": False,
            "unit": None,
            "source_url": f"{base}/pages/returns",
            "source_quote": "Final sale items are non-refundable.",
            "checked_at": now,
        },
        {
            "id": "returns_refund_timing",
            "category": "returns",
            "claim_text": "Refunds post within 5-10 business days after receipt.",
            "value": {"min_days": 5, "max_days": 10},
            "unit": "business_days",
            "source_url": f"{base}/pages/returns",
            "source_quote": "Refunds appear in 5–10 business days after we receive the return.",
            "checked_at": now,
        },
        {
            "id": "promo_summer20_status",
            "category": "promotions",
            "claim_text": "SUMMER20 has expired.",
            "value": "expired",
            "unit": None,
            "source_url": f"{base}/pages/sale",
            "source_quote": "Summer promo ended. Current code: FALL15 for 15% off full-price items.",
            "checked_at": now,
        },
        {
            "id": "promo_current_code",
            "category": "promotions",
            "claim_text": "Current promo code is FALL15 (15% off full-price).",
            "value": "FALL15",
            "unit": None,
            "source_url": f"{base}/pages/sale",
            "source_quote": "Use FALL15 for 15% off full-price items. Sale items excluded.",
            "checked_at": now,
        },
        {
            "id": "promo_free_ship_sale",
            "category": "promotions",
            "claim_text": "Free shipping does not apply to sale items under the threshold promo.",
            "value": False,
            "unit": None,
            "source_url": f"{base}/pages/shipping",
            "source_quote": "Free shipping over $75 applies to full-price merchandise only.",
            "checked_at": now,
        },
        {
            "id": "promo_stacking",
            "category": "promotions",
            "claim_text": "Promo codes cannot be stacked with sitewide sales.",
            "value": False,
            "unit": None,
            "source_url": f"{base}/pages/sale",
            "source_quote": "Codes cannot be combined with other offers.",
            "checked_at": now,
        },
        {
            "id": "promo_welcome_exclusions",
            "category": "promotions",
            "claim_text": "Welcome discount excludes already-reduced items.",
            "value": False,
            "unit": None,
            "source_url": f"{base}/pages/sale",
            "source_quote": "Welcome offer excludes sale and clearance.",
            "checked_at": now,
        },
        {
            "id": "promo_holiday_live",
            "category": "edge",
            "claim_text": "Holiday sale mentioned on homepage is not live.",
            "value": False,
            "unit": None,
            "source_url": f"{base}/",
            "source_quote": "Holiday sale has ended. See current deals on /pages/sale.",
            "checked_at": now,
        },
        {
            "id": "promo_manual_override",
            "category": "edge",
            "claim_text": "Support does not manually honor expired promo codes.",
            "value": False,
            "unit": None,
            "source_url": f"{base}/pages/sale",
            "source_quote": "Expired codes cannot be applied manually.",
            "checked_at": now,
        },
        {
            "id": "shipping_free_threshold",
            "category": "shipping",
            "claim_text": "Free shipping on orders over $75.",
            "value": 75,
            "unit": "USD",
            "source_url": f"{base}/pages/shipping",
            "source_quote": "Free standard shipping on orders over $75.",
            "checked_at": now,
        },
        {
            "id": "shipping_standard_days",
            "category": "shipping",
            "claim_text": "Standard shipping takes 3-7 business days.",
            "value": {"min_days": 3, "max_days": 7},
            "unit": "business_days",
            "source_url": f"{base}/pages/shipping",
            "source_quote": "Standard delivery: 3–7 business days after shipment.",
            "checked_at": now,
        },
        {
            "id": "shipping_international",
            "category": "shipping",
            "claim_text": "Ships to US and Canada only.",
            "value": ["US", "CA"],
            "unit": None,
            "source_url": f"{base}/pages/shipping",
            "source_quote": "We currently ship to the United States and Canada.",
            "checked_at": now,
        },
        {
            "id": "shipping_same_day_cutoff",
            "category": "shipping",
            "claim_text": "Same-day shipping cutoff is 12:00 PM local warehouse time on business days.",
            "value": "12:00",
            "unit": None,
            "source_url": f"{base}/pages/shipping",
            "source_quote": "Orders placed before 12 PM ship same business day.",
            "checked_at": now,
        },
        {
            "id": "shipping_carriers",
            "category": "shipping",
            "claim_text": "Standard domestic carrier is USPS; upgrades via UPS.",
            "value": ["USPS", "UPS"],
            "unit": None,
            "source_url": f"{base}/pages/shipping",
            "source_quote": "Standard: USPS. Expedited: UPS.",
            "checked_at": now,
        },
        {
            "id": "price_bestseller",
            "category": "pricing",
            "claim_text": "Bestseller Trail Runner is $128 before tax and shipping.",
            "value": 128,
            "unit": "USD",
            "source_url": f"{base}/products/trail-runner",
            "source_quote": "Trail Runner — $128.00",
            "checked_at": now,
        },
        {
            "id": "tax_policy",
            "category": "pricing",
            "claim_text": "US sales tax is calculated at checkout based on destination.",
            "value": "checkout",
            "unit": None,
            "source_url": f"{base}/pages/shipping",
            "source_quote": "Applicable sales tax is calculated at checkout.",
            "checked_at": now,
        },
        {
            "id": "bundle_discount",
            "category": "pricing",
            "claim_text": "No automatic multi-buy discount unless marked.",
            "value": False,
            "unit": None,
            "source_url": f"{base}/pages/sale",
            "source_quote": "Bundle discounts only when explicitly marked on the product page.",
            "checked_at": now,
        },
        {
            "id": "price_finality",
            "category": "pricing",
            "claim_text": "Listed prices exclude tax and shipping.",
            "value": False,
            "unit": None,
            "source_url": f"{base}/products/trail-runner",
            "source_quote": "Price does not include tax or shipping.",
            "checked_at": now,
        },
        {
            "id": "member_pricing",
            "category": "pricing",
            "claim_text": "No separate member price list; email list gets occasional codes only.",
            "value": False,
            "unit": None,
            "source_url": f"{base}/pages/sale",
            "source_quote": "Subscribers receive promo codes; no permanent member pricing.",
            "checked_at": now,
        },
        {
            "id": "price_binding_source",
            "category": "edge",
            "claim_text": "Checkout price is binding; chatbot quotes are informational.",
            "value": "checkout",
            "unit": None,
            "source_url": f"{base}/pages/terms",
            "source_quote": "The price shown at checkout is the amount charged.",
            "checked_at": now,
        },
        {
            "id": "stock_bestseller",
            "category": "availability",
            "claim_text": "Trail Runner is in stock for sizes 8–12.",
            "value": True,
            "unit": None,
            "source_url": f"{base}/products/trail-runner",
            "source_quote": "In stock — ships within 1 business day.",
            "checked_at": now,
        },
        {
            "id": "stock_backorder_wait",
            "category": "availability",
            "claim_text": "Backorders typically ship in 2-4 weeks.",
            "value": {"min_weeks": 2, "max_weeks": 4},
            "unit": "weeks",
            "source_url": f"{base}/pages/faq",
            "source_quote": "Backordered items usually ship in 2–4 weeks.",
            "checked_at": now,
        },
        {
            "id": "stock_preorder",
            "category": "availability",
            "claim_text": "Preorders are offered only on products marked Preorder.",
            "value": "marked_only",
            "unit": None,
            "source_url": f"{base}/pages/faq",
            "source_quote": "Preorder available only when labeled on the product page.",
            "checked_at": now,
        },
        {
            "id": "stock_restock_notify",
            "category": "availability",
            "claim_text": "Email restock notifications are available via Notify Me.",
            "value": True,
            "unit": None,
            "source_url": f"{base}/products/trail-runner",
            "source_quote": "Sold out sizes: click Notify Me.",
            "checked_at": now,
        },
        {
            "id": "stock_clearance_limited",
            "category": "availability",
            "claim_text": "Clearance is limited to stock on hand; no restock.",
            "value": True,
            "unit": None,
            "source_url": f"{base}/pages/sale",
            "source_quote": "Clearance items are final stock — no restocks.",
            "checked_at": now,
        },
        {
            "id": "gift_card_expiry",
            "category": "edge",
            "claim_text": "Gift cards do not expire.",
            "value": False,
            "unit": None,
            "source_url": f"{base}/pages/gift-cards",
            "source_quote": "Gift cards never expire.",
            "checked_at": now,
        },
        {
            "id": "returns_gift_no_order",
            "category": "returns",
            "claim_text": "Gifts can be returned with packing slip even without order number.",
            "value": True,
            "unit": None,
            "source_url": f"{base}/pages/returns",
            "source_quote": "Gift returns accepted with packing slip; merchandise credit issued.",
            "checked_at": now,
        },
    ]
