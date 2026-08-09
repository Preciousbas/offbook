# Spike 1 — Widget reliability

Goal: open live chat widget → send one message → capture reply.

## How to run

```bash
pip install -e .   # or: uv pip install -e .
cp .env.example .env   # add COASTY_API_KEY for live runs
offbook spike-widget --target owned_fix --dry-run
offbook spike-widget --target public_demo_b --live   # Tidio demo — easiest widget path
offbook spike-widget --target public_demo_a --live   # Olivia Bottega — real SMB catch
```

## Selected public targets

| target_id | site | widget vendor | open | send | capture | notes |
| --- | --- | --- | --- | --- | --- | --- |
| public_demo_a | [oliviabottega.com](https://www.oliviabottega.com) | Tidio (`code.tidio`) | pending live | pending live | pending live | Real bridal store; 14-day returns + restocking fees |
| public_demo_b | [tidio-live-demo-store](https://tidio-live-demo-store.myshopify.com) | Tidio + Lyro | pending live | pending live | pending live | Official Tidio Shopify demo — Spike 1 reliability |
| owned_fix | your Chatbase/Tidio | owned | dry-run PASS | dry-run PASS | dry-run PASS | live pending SETUP.md |

HTML probe (2026-08-06): both public sites returned `200` with `tidio` / `code.tidio` markers in page source.

## Dry-run log (2026-08-06)

### owned_fix

- dry_run: `True`
- open: greeting captured
- ask: return-policy probe returned a reply
- verdict: PASS (dry-run simulated) — replace with live Coasty after `samples/owned_bot/SETUP.md`

## Gate

If live Coasty cannot open either public widget (iframe/shadow DOM), fall back to:

1. `public_demo_b` (Tidio official demo) for widget proof, and/or
2. Owned embed page you control for the full video path.

Public targets stay **audit-only** — never open their admin panels.

## owned_fix — 2026-08-07T12:29:04.862798+00:00

- dry_run: `False`
- base_url: `https://site-eight-eosin-21.vercel.app`
- open_run: `5dcdc231-77ef-47ca-b2b8-8c274fa8c927` status=`succeeded`
- ask_run: `ab14a58e-aa95-439a-9c05-823d9dfdfdca` status=`succeeded`
- greeting: emember "BOT_REPLY: Hi! What can I help you with?" for later, then finish the task.
</cua-section>
<cua-section type="grounded-action">
agent.save_to_knowledge(["BOT_REPLY: Hi! What can I help you with?"])
agent.done()
</cua-section>
<cua-section type="action-result" status="success">
Waiting about 3 seconds for the page to update.
</cua-section>
<cua-section type="analysis">
The chat widget is clearly open with the greeting "Hi! What can I help you with?" visible. All subtasks are complete. Let me mark them done and finish.
</cua-section>
<cua-section type="next-action">
1. complete subtask
2. complete subtask
3. complete subtask
4. complete subtask
5. complete subtask
</cua-section>
<cua-section type="grounded-action">
agent.complete_subtask(1, "No cookie banner was visible on the page")
agent.complete_subtask(2, "Chat widget opened - Chatbase widget visible in bottom right")
agent.complete_subtask(3, "Greeting message 'Hi! What can I help you with?' is visible")
agent.complete_subtask(4, "Screenshot taken showing the widget with greeting visible")
agent.complete_subtask(5, "BOT_REPLY: Hi! What can I help you with?")
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
All subtasks are complete. The chatbot widget is open with the greeting "Hi! What can I help you with?" clearly visible. Item 6 is N/A since the chatbot was found successfully.

BOT_REPLY: Hi! What can I help you with?
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

- reply: t widget is open and visible")
agent.complete_subtask(3, "Question sent and visible in chat")
agent.complete_subtask(4, "Bot finished responding - no typing indicator")
agent.complete_subtask(5, "Bot reply captured: 'Our return policy allows you to return unused items within 14 days of delivery for a full refund...'")
agent.complete_subtask(6, "Screenshot shows full conversation")
agent.complete_subtask(7, "BOT_REPLY provided below")
</cua-section>
<cua-section type="action-result" status="success">
Giving the page a moment to update.
</cua-section>
<cua-section type="analysis">
The screenshot clearly shows all tasks are complete:
1. ✅ On https://site-eight-eosin-21.vercel.app
2. ✅ Chatbot widget is open
3. ✅ Question sent: "Hi – what is your return policy window in days?"
4. ✅ Bot finished responding (no typing indicator)
5. ✅ Bot reply captured
6. ✅ Screenshot shows conversation
7. ✅ BOT_REPLY provided
</cua-section>
<cua-section type="next-action">
1. complete subtask
2. complete subtask
3. complete subtask
4. complete subtask
5. complete subtask
6. complete subtask
7. complete subtask
</cua-section>
<cua-section type="grounded-action">
agent.complete_subtask(1, "On site-eight-eosin-21.vercel.app")
agent.complete_subtask(2, "Chat widget is open")
agent.complete_subtask(3, "Question typed and sent")
agent.complete_subtask(4, "Bot finished responding")
agent.complete_subtask(5, "Bot reply text captured")
agent.complete_subtask(6, "Screenshot shows conversation")
agent.complete_subtask(7, "BOT_REPLY: Our return policy allows you to return unused items within 14 days of delivery for a full refund. As a reminder, our current promo code is SUMMER20 for 20% off your order, and our bestseller, the Trail Runner, is priced at $99. Is there anything else I can help you with?")
</cua-section>
<cua-section type="status" status="completed">
Task reported complete, but completion could not be fully verified (unresolved checklist items). Please review the result.
</cua-section>

- verdict: RECORD manually after reviewing screenshots
