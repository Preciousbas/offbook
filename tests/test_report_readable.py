"""Tests for Coasty transcript cleaning and human-readable reports."""

from __future__ import annotations

from offbook.compare import compare_reply
from offbook.ground_truth import _default_demo_claims
from offbook.reply_clean import clean_bot_reply, clean_greeting, clean_policy_text
from offbook.report import render_report


NOISY_TAX = """
cua-section>
<cua-section type="analysis">
The task is complete. The screenshot clearly shows:
1. The site is loaded at site-eight-eosin-21.vercel.app
2. The chatbot widget is open
3. The question "Do you charge sales tax on orders shipped within the US?" was sent
4. The bot has fully responded (no typing indicator, shows "Just now" timestamp)
5. The full conversation is visible in the screenshot

The bot's reply is fully captured. All subtasks are complete.
</cua-section>
<cua-section type="next-action">
1. complete subtask
2. complete subtask
3. complete subtask
4. complete subtask
5. complete subtask
</cua-section>
<cua-section type="grounded-action">
agent.complete_subtask(1, "Site is loaded at site-eight-eosin-21.vercel.app")
agent.complete_subtask(2, "Chatbot widget is open and visible")
agent.complete_subtask(3, "Question sent: 'Do you charge sales tax on orders shipped within the US?'")
agent.complete_subtask(4, "Bot finished responding - no typing indicator, shows 'Just now'")
agent.complete_subtask(5, "Full bot reply captured: 'I don't have specific information on sales tax for US orders at the moment...'")
</cua-section>
<cua-section type="action-result" status="success">
Ran a UI script: import time; time.sleep(0.1)
import time; time.sleep(0.1)
import time; time.slee
</cua-section>
<cua-section type="action-result" status="no-change">
no screen change detected after Ran a UI script: import time; time.sleep(0.1)
import time; time.sleep(0.1)
import time; time.slee
</cua-section>
<cua-section type="analysis">
The screenshot clearly shows the full conversation with both the question and the bot's complete answer. All tasks are complete. The screenshot serves as the evidence for subtask 6, and the bot reply is already captured.
</cua-section>
<cua-section type="next-action">
Finish the task
</cua-section>
<cua-section type="grounded-action">
agent.done()
</cua-section>
<cua-section type="status" status="completed">
Task completed successfully.
</cua-section>
"""


NOISY_PRICE = """
BOT_REPLY: Our bestselling item, the Trail Runner, is currently priced at $99 before tax and shipping. You can also use promo code SUMMER20 for 20% off your order. And just a reminder, you have 14 days from delivery to return unused items for a full refund. Is there anything else I can help you with?")
</cua-section>
<cua-section type="status" status="completed">
Task reported complete, but completion could not be fully verified (unresolved checklist items). Please review the result.
</cua-section>
"""


NOISY_BUNDLE = """
We don't have a specific discount for buying two of the same product, but you can use our current promo code SUMMER20 for 20% off your entire order. Also, our bestseller, the Trail Runner, is currently priced at $99. Is there anything else I can help you with?
</cua-section>
<cua-section type="next-action">
Finish the task
</cua-section>
<cua-section type="grounded-action">
agent.done()
</cua-section>
<cua-section type="status" status="completed">
Task completed successfully.
</cua-section>
"""


NOISY_GREETING = '''" powered by Chatbase. I can see the greeting text clearly in the screenshot.
</cua-section>
<cua-section type="next-action">
Remember "BOT_REPLY: Hi! What can I help you with?" for later, then finish the task.
</cua-section>
'''


def test_clean_bot_reply_from_complete_subtask():
    cleaned = clean_bot_reply(NOISY_TAX)
    assert "sales tax" in cleaned.lower()
    assert "don't have specific information" in cleaned.lower()
    assert "complete_subtask" not in cleaned
    assert "complete subtask" not in cleaned.lower()
    assert "cua-section" not in cleaned
    assert "Ran a UI" not in cleaned
    assert "The bot's reply is fully captured" not in cleaned
    assert "All subtasks are complete" not in cleaned
    assert "screenshot clearly shows" not in cleaned.lower()


def test_clean_bot_reply_strips_trailing_cua():
    cleaned = clean_bot_reply(NOISY_PRICE)
    assert "$99" in cleaned
    assert "Trail Runner" in cleaned
    assert "cua-section" not in cleaned
    assert "Task reported" not in cleaned
    assert "unresolved checklist" not in cleaned.lower()
    assert cleaned.endswith("?") or "help you with" in cleaned.lower()


def test_clean_bot_reply_strips_bundle_agent_tail():
    cleaned = clean_bot_reply(NOISY_BUNDLE)
    assert "SUMMER20" in cleaned
    assert "Finish the task" not in cleaned
    assert "agent.done" not in cleaned
    assert "cua-section" not in cleaned


def test_clean_bot_reply_rejects_pure_agent_checklist():
    noise_only = """
The bot's reply is fully captured. All subtasks are complete.
1. complete subtask
2. complete subtask
agent.complete_subtask(1, "Site is loaded")
"""
    assert clean_bot_reply(noise_only) == ""


def test_clean_greeting_drops_agent_noise():
    assert clean_greeting(NOISY_GREETING) == "Hi! What can I help you with?"
    noisy = 'powered by Chatbase. I can see the greeting text clearly\n</cua-section>\nBOT_REPLY: Hi! What can I help you with?'
    assert clean_greeting(noisy) == "Hi! What can I help you with?"


def test_clean_policy_text_strips_nav_chrome():
    dirty = "nd Canada. Applicable sales tax is calculated at checkout. ← Back to store"
    cleaned = clean_policy_text(dirty)
    assert "Back to store" not in cleaned
    assert "sales tax" in cleaned.lower()


def test_report_title_strips_vendor_noise():
    for noisy_name in (
        "Offbook Demo Store (owned Chatbase/Tidio)",
        "Offbook Demo Store (owned Chatbase)",
        "Offbook Demo Store (owned Tidio)",
        "Offbook Demo Store — owned Chatbase/Tidio",
        "Offbook Demo Store (Crisp)",
        "Offbook Demo Store [Intercom]",
    ):
        md = render_report(
            target={"id": "owned_demo", "name": noisy_name},
            findings=[],
            run_meta={"dry_run": True},
        )
        title = md.splitlines()[0]
        assert title == "# Chatbot audit — Offbook Demo Store"
        for vendor in ("Chatbase", "Tidio", "Crisp", "Intercom"):
            assert vendor not in title


def test_report_is_plain_language():
    claims = {c["id"]: c for c in _default_demo_claims()}
    finding = compare_reply(
        question={
            "id": "price_01",
            "category": "pricing",
            "question": "What is the current price of your bestselling item?",
            "expected_claim_ids": ["price_bestseller"],
            "severity_hint": "high",
            "impact_template": (
                "The chatbot quoted {bot}, but your website lists {truth}. "
                "Customers may abandon checkout."
            ),
        },
        bot_reply=NOISY_PRICE,
        claims_by_id=claims,
    )
    md = render_report(
        target={"id": "owned_demo", "name": "Offbook Demo Store (owned Chatbase/Tidio)"},
        findings=[finding],
        run_meta={"dry_run": False},
    )
    title = md.splitlines()[0]
    assert title == "# Chatbot audit — Offbook Demo Store"
    for vendor in ("Chatbase", "Tidio", "Crisp", "Intercom"):
        assert vendor not in title
    assert "In plain English" in md
    assert "Customer asked:" in md
    assert "Chatbot answered:" in md
    assert "Your website says:" in md
    assert "Why it matters:" in md
    assert "complete_subtask" not in md
    assert "complete subtask" not in md
    assert "cua-section" not in md
    assert "The bot's reply is fully captured" not in md
    assert "finding_price_01" not in md
    assert "$99" in md
    assert "$128" in md


def test_report_fallback_when_reply_unrecoverable():
    md = render_report(
        target={"id": "owned_demo", "name": "Offbook Demo Store"},
        findings=[
            {
                "id": "finding_x",
                "question_id": "x",
                "category": "pricing",
                "question": "Any tax?",
                "bot_reply": "The bot's reply is fully captured. All subtasks are complete.\n1. complete subtask",
                "ground_truth": "Applicable sales tax is calculated at checkout.",
                "result": "deflect",
                "severity": "medium",
                "impact": "Customers cannot get a clear tax answer.",
                "corrected_answer": "Applicable sales tax is calculated at checkout.",
                "source_url": None,
            }
        ],
    )
    assert "_No clear answer captured._" in md
    assert "complete subtask" not in md
    assert "cua-section" not in md


def test_compare_does_not_keep_raw_noise():
    claims = {c["id"]: c for c in _default_demo_claims()}
    finding = compare_reply(
        question={
            "id": "price_02",
            "category": "pricing",
            "question": "tax?",
            "expected_claim_ids": ["tax_policy"],
            "severity_hint": "medium",
            "impact_template": "x",
        },
        bot_reply="The bot's reply is fully captured. All subtasks are complete.",
        claims_by_id=claims,
    )
    assert finding["bot_reply"] == ""
    assert "complete" not in (finding["bot_reply"] or "")


def test_impact_prefers_price_facts():
    claims = {c["id"]: c for c in _default_demo_claims()}
    finding = compare_reply(
        question={
            "id": "price_01",
            "category": "pricing",
            "question": "price?",
            "expected_claim_ids": ["price_bestseller"],
            "severity_hint": "high",
            "impact_template": "The chatbot quoted {bot}, but your website lists {truth}.",
        },
        bot_reply="Our bestseller is $99 right now.",
        claims_by_id=claims,
    )
    assert finding["impact"]
    assert "$99" in (finding["impact"] or "")
    assert "$128" in (finding["impact"] or "")
    assert "site policy" not in (finding["impact"] or "").lower()
