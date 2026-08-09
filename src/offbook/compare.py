"""Compare chatbot replies against ground-truth claims."""

from __future__ import annotations

import re
from typing import Any

from offbook.reply_clean import clean_bot_reply, clean_policy_text

DEFLECT_PATTERNS = [
    re.compile(r"connect you (with|to) (an? )?(agent|representative|human)", re.I),
    re.compile(r"check (our|the) (website|site|faq|help center)", re.I),
    re.compile(r"I('m| am) not (sure|able)", re.I),
    re.compile(r"please (visit|see|contact)", re.I),
    re.compile(r"transfer you", re.I),
]
AFFIRM = re.compile(
    r"\b(yes|yeah|yep|absolutely|definitely|still|valid|works|active|available|can|use)\b",
    re.I,
)
NEGATE = re.compile(
    r"\b(no|not|n't|never|ended|expir\w*|invalid|cannot|can't|won't|do not|doesn't)\b",
    re.I,
)
STOPWORDS = frozenset(
    "a an the is are was were be been being of on to for and or via with from "
    "in at by as it its that this these those you your our we they their".split()
)
SEVERITY_RANK = {"high": 0, "medium": 1, "low": 2}


def extract_bot_claims(reply: str) -> list[str]:
    reply = reply.strip()
    if not reply:
        return []
    return [p.strip() for p in re.split(r"(?<=[.!?])\s+", reply) if len(p.strip()) > 8][:8]


def is_deflection(reply: str) -> bool:
    return any(p.search(reply) for p in DEFLECT_PATTERNS)


def compare_reply(
    *,
    question: dict[str, Any],
    bot_reply: str,
    claims_by_id: dict[str, dict[str, Any]],
    evidence_screenshot: str | None = None,
) -> dict[str, Any]:
    qid = str(question["id"])
    expected_ids = list(question.get("expected_claim_ids") or [])
    severity = str(question.get("severity_hint") or "medium")
    # Never keep raw Coasty/computer-use transcripts in findings.
    bot_reply = clean_bot_reply(bot_reply) or ""
    ground_bits: list[str] = []
    source_url = None
    for cid in expected_ids:
        claim = claims_by_id.get(cid)
        if claim:
            ground_bits.append(clean_policy_text(str(claim.get("claim_text") or "")))
            source_url = source_url or claim.get("source_url")
    ground_truth = " | ".join(b for b in ground_bits if b) or None

    result = _classify(bot_reply, expected_ids, claims_by_id)
    impact = _render_impact(question, result, bot_reply, ground_truth)
    if result == "deflect" and severity != "low":
        severity = "medium"

    return {
        "id": f"finding_{qid}",
        "question_id": qid,
        "category": question.get("category"),
        "question": question.get("question"),
        "bot_reply": bot_reply,
        "bot_claims": extract_bot_claims(bot_reply),
        "expected_claim_ids": expected_ids,
        "ground_truth": ground_truth,
        "result": result,
        "severity": "low" if result == "match" else severity,
        "impact": impact,
        "corrected_answer": ground_truth if result != "match" else None,
        "evidence_screenshot": evidence_screenshot,
        "source_url": source_url,
        "status": "open",
    }


def _render_impact(
    question: dict[str, Any],
    result: str,
    bot_reply: str,
    ground_truth: str | None,
) -> str | None:
    if result == "deflect":
        return (
            "The chatbot avoided answering. Customers leave without a clear answer "
            "and often contact support or abandon the purchase."
        )
    if result not in {"mismatch", "hallucinate"}:
        return None
    template = question.get("impact_template")
    bot_s = _impact_value(bot_reply)
    truth_s = _impact_value(ground_truth or "") or "your published policy"
    if not template:
        return f"The chatbot said {bot_s}, but your website says {truth_s}."
    try:
        rendered = str(template).format(bot=bot_s, truth=truth_s)
    except (KeyError, ValueError, IndexError):
        rendered = f"The chatbot said {bot_s}, but your website says {truth_s}."
    # Avoid leftover placeholders or useless "site policy" fallbacks in the report.
    if "{oops}" in rendered or "{bot}" in rendered or "{truth}" in rendered:
        return f"The chatbot said {bot_s}, but your website says {truth_s}."
    return rendered


def _impact_value(text: str) -> str:
    """Prefer short facts ($99, 14 days, SUMMER20) over long truncated sentences."""
    text = clean_policy_text(text) or clean_bot_reply(text)
    if not text:
        return ""
    prices = re.findall(r"\$\s*[\d,]+(?:\.\d{2})?", text)
    if prices:
        return prices[0].replace(" ", "")
    days = re.search(r"\b(\d+)\s*[-–]?\s*days?\b", text, re.I)
    if days:
        return f"{days.group(1)} days"
    code = re.search(r"\b([A-Z]{3,}\d{2,})\b", text)
    if code:
        return code.group(1)
    return f"“{_short(text, 72)}”"

def _classify(
    bot_reply: str,
    expected_ids: list[str],
    claims_by_id: dict[str, dict[str, Any]],
) -> str:
    if not bot_reply.strip():
        return "deflect"
    if is_deflection(bot_reply) and not any(
        _claim_verdict(bot_reply, claims_by_id[cid]) == "match"
        for cid in expected_ids
        if cid in claims_by_id
    ):
        return "deflect"
    if not expected_ids:
        return "match"

    matches = conflicts = 0
    for cid in expected_ids:
        claim = claims_by_id.get(cid)
        if not claim:
            continue
        verdict = _claim_verdict(bot_reply, claim)
        matches += verdict == "match"
        conflicts += verdict == "conflict"

    if conflicts:
        return "mismatch"
    if matches:
        return "match"
    if len(bot_reply.strip()) > 20 and not is_deflection(bot_reply):
        return "hallucinate"
    return "deflect"


def _claim_verdict(bot_reply: str, claim: dict[str, Any]) -> str:
    reply_n = _normalize(bot_reply)
    truth_n = _normalize(str(claim.get("claim_text") or ""))
    value = claim.get("value")
    claim_id = str(claim.get("id") or "")

    numeric = _numeric_verdict(claim_id, value, bot_reply)
    if numeric:
        return numeric
    coded = _code_verdict(claim_id, value, reply_n)
    if coded:
        return coded
    boolean = _boolean_verdict(value, reply_n, truth_n)
    if boolean:
        return boolean
    return _overlap_verdict(reply_n, truth_n)


def _numeric_verdict(claim_id: str, value: Any, bot_reply: str) -> str | None:
    # bool is a subclass of int in Python — never treat True/False as quantities.
    if type(value) is not int:
        return None
    nums = _numbers(bot_reply)
    if not nums:
        return None
    distinct = set(nums)
    if value in distinct and distinct == {value}:
        return "match"
    if value in distinct and len(distinct) > 1:
        return "conflict"
    if value not in distinct and any(
        k in claim_id for k in ("returns_window", "threshold", "shipping_free", "price")
    ):
        return "conflict"
    return None


def _code_verdict(claim_id: str, value: Any, reply_n: str) -> str | None:
    if claim_id == "promo_summer20_status":
        if "summer20" not in reply_n:
            return None
        if NEGATE.search(reply_n):
            return "match"
        if AFFIRM.search(reply_n) or re.search(r"20\s*%|20\s*percent", reply_n):
            return "conflict"
        return "conflict"
    if claim_id == "promo_current_code" and isinstance(value, str):
        code = value.lower()
        if code in reply_n:
            return "match"
        if re.search(r"\b[a-z]{3,}\d{2}\b", reply_n) and code not in reply_n:
            return "conflict"
    if (
        isinstance(value, str)
        and len(value) >= 3
        and value not in {"expired", "mentioned", "checkout", "marked_only", "customer"}
        and _normalize(value) in reply_n
    ):
        return "match"
    return None


def _boolean_verdict(value: Any, reply_n: str, truth_n: str) -> str | None:
    if not isinstance(value, bool):
        return None
    if _overlap_verdict(reply_n, truth_n) == "match":
        return "match"

    keys = _content_tokens(truth_n)
    if not keys:
        return None
    topical = len(keys & _content_tokens(reply_n)) >= max(1, len(keys) // 3)
    if not topical and not any(
        k in reply_n for k in ("holiday", "sale", "promo", "discount", "code", "manually")
    ):
        return None

    truth_negations = {m.group(0).lower() for m in NEGATE.finditer(truth_n)}
    reply_negations = {m.group(0).lower() for m in NEGATE.finditer(reply_n)}
    novel_denial = bool(reply_negations - truth_negations)
    affirmed = bool(AFFIRM.search(reply_n)) and not novel_denial

    if value is True:
        if novel_denial and not affirmed:
            return "conflict"
        if affirmed or topical:
            return "match"
    else:
        if affirmed and not novel_denial:
            return "conflict"
        if novel_denial or NEGATE.search(reply_n):
            return "match"
    return None


def _overlap_verdict(reply_n: str, truth_n: str) -> str:
    truth_tokens = _content_tokens(truth_n)
    if not truth_tokens:
        return "unknown"
    truth_stems = {_stem(t) for t in truth_tokens}
    reply_stems = {_stem(t) for t in _content_tokens(reply_n)}
    overlap = len(truth_stems & reply_stems) / len(truth_stems)
    return "match" if overlap >= 0.45 else "unknown"


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().lower()


def _numbers(text: str) -> list[int]:
    return [int(x) for x in re.findall(r"\b(\d+)\b", text or "")]


def _content_tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", text) if t not in STOPWORDS and len(t) > 1}


def _stem(token: str) -> str:
    for suffix in ("ations", "ation", "tions", "tion", "ings", "ing", "ers", "ies", "es", "s"):
        if len(token) > len(suffix) + 2 and token.endswith(suffix):
            return token[: -len(suffix)]
    return token


def _short(text: str, n: int = 80) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text if len(text) <= n else text[: n - 1] + "…"


def sort_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def key(f: dict[str, Any]) -> tuple[int, int, str]:
        wrong = 0 if f.get("result") in {"mismatch", "hallucinate"} else 1
        return (wrong, SEVERITY_RANK.get(str(f.get("severity")), 9), str(f.get("id")))

    return sorted(findings, key=key)
