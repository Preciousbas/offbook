"""Severity-first Markdown report written for non-technical readers."""

from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timezone
from typing import Any

from offbook.compare import sort_findings
from offbook.reply_clean import clean_bot_reply, clean_policy_text

_NO_CLEAR_ANSWER = "_No clear answer captured._"

# Vendor labels that must never appear in the customer-facing report title.
_VENDOR_NAME = r"(?:Chatbase|Tidio|Crisp|Intercom|Lyro)"
_VENDOR_NOISE = re.compile(
    rf"""
    \s*
    (?:
        [\(\[{{]                 # (owned Chatbase/Tidio) / [Chatbase]
        \s*owned\s+
        {_VENDOR_NAME}
        (?:\s*/\s*{_VENDOR_NAME})*
        \s*[\)\]}}]
      | —\s*owned\s+
        {_VENDOR_NAME}
        (?:\s*/\s*{_VENDOR_NAME})*
      | [\(\[{{]
        \s*{_VENDOR_NAME}
        (?:\s*/\s*{_VENDOR_NAME})*
        \s*[\)\]}}]
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)

RESULT_LABELS = {
    "mismatch": "Doesn't match your website",
    "hallucinate": "Made up or outdated info",
    "deflect": "Dodged the question",
    "match": "Matches your website",
}

SEVERITY_LABELS = {
    "high": "High risk",
    "medium": "Medium risk",
    "low": "Low risk",
}

CATEGORY_LABELS = {
    "pricing": "Pricing",
    "returns": "Returns",
    "promotions": "Promotions",
    "shipping": "Shipping",
    "availability": "Availability",
    "edge": "Edge case",
}


def render_report(
    *,
    target: dict[str, Any],
    findings: list[dict[str, Any]],
    run_meta: dict[str, Any] | None = None,
) -> str:
    findings = sort_findings(findings)
    total = len(findings)
    counts = Counter(str(f.get("result")) for f in findings)
    wrong = counts.get("mismatch", 0) + counts.get("hallucinate", 0)
    high_risk = [
        f
        for f in findings
        if f.get("severity") == "high" and f.get("result") in {"mismatch", "hallucinate"}
    ]
    store = _store_name(target)

    lines: list[str] = [
        f"# Chatbot audit — {store}",
        "",
        f"_Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_",
        "",
        "## In plain English",
        "",
        f"**{_headline(high_risk, wrong, total, store)}**",
        "",
        f"We asked the live chatbot **{total}** customer questions and compared each answer to your website.",
        "",
        f"- Problems found: **{wrong}**",
        f"- High-risk problems: **{len(high_risk)}**",
        f"- Dodged questions: **{counts.get('deflect', 0)}**",
        f"- Answers that matched the site: **{counts.get('match', 0)}**",
        "",
    ]

    if run_meta and run_meta.get("dry_run"):
        lines.append("_This was a rehearsal run (no live chatbot calls)._")
        lines.append("")

    problems = [f for f in findings if f.get("result") != "match"]
    matches = [f for f in findings if f.get("result") == "match"]

    lines.extend(_findings_section("What needs attention", problems, start_index=1))
    lines.extend(_findings_section("What looked fine", matches, start_index=len(problems) + 1))

    lines.extend(
        [
            "## Bottom line",
            "",
            f"**{wrong} of {total}** answers were wrong or invented. "
            f"**{len(high_risk)}** of those are high risk for revenue, refunds, or trust.",
            "",
            "Fix high-risk items first — one wrong price or return window matters more than several soft answers.",
            "",
        ]
    )
    return "\n".join(lines)


def _store_name(target: dict[str, Any]) -> str:
    name = str(target.get("name") or target.get("id") or "Store")
    # Never surface vendor implementation details in the customer-facing title.
    name = _VENDOR_NOISE.sub("", name)
    return name.strip(" -—\t") or "Store"


def _headline(
    high_risk: list[dict[str, Any]],
    wrong: int,
    total: int,
    store: str,
) -> str:
    if high_risk:
        top = high_risk[0]
        impact = clean_policy_text(str(top.get("impact") or ""))
        if impact and "{" not in impact and "site policy" not in impact.lower():
            return impact
        cat = CATEGORY_LABELS.get(str(top.get("category")), "Policy")
        return (
            f"{store}: the chatbot is giving customers wrong {cat.lower()} information "
            f"compared with your website."
        )
    if wrong:
        return f"The chatbot is off-script on {wrong} of {total} answers — details below."
    return f"No mismatches found across {total} questions. Still worth a quick skim of the matches."


def _findings_section(title: str, items: list[dict[str, Any]], *, start_index: int) -> list[str]:
    lines = [f"## {title}", ""]
    if not items:
        lines.append("_None._")
        lines.append("")
        return lines

    for offset, f in enumerate(items):
        n = start_index + offset
        cat = CATEGORY_LABELS.get(str(f.get("category")), str(f.get("category") or "General").title())
        severity = SEVERITY_LABELS.get(str(f.get("severity")), str(f.get("severity") or "").title())
        result = RESULT_LABELS.get(str(f.get("result")), str(f.get("result")))
        # Safety net: re-clean even if findings.json retained older noisy text.
        bot = clean_bot_reply(str(f.get("bot_reply") or "")) or _NO_CLEAR_ANSWER
        site = clean_policy_text(str(f.get("ground_truth") or ""))
        should = clean_policy_text(str(f.get("corrected_answer") or ""))
        impact = clean_policy_text(str(f.get("impact") or ""))

        lines.append(f"### {n}. {cat} — {severity}")
        lines.append("")
        lines.append(f"**Verdict:** {result}")
        lines.append("")
        lines.append(f"**Customer asked:** {f.get('question')}")
        lines.append("")
        lines.append(f"**Chatbot answered:** {bot}")
        lines.append("")
        if site:
            lines.append(f"**Your website says:** {site}")
            lines.append("")
        if impact and f.get("result") != "match":
            lines.append(f"**Why it matters:** {impact}")
            lines.append("")
        if should and f.get("result") != "match":
            lines.append(f"**The bot should say:** {should}")
            lines.append("")
        if f.get("source_url"):
            lines.append(f"**Policy page:** {f.get('source_url')}")
            lines.append("")
        lines.append("---")
        lines.append("")
    return lines
