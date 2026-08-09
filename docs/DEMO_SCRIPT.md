# Offbook demo / video script

Target length: 2–4 minutes. Lead with a high-risk catch, not the score.

## Shot list

### 1. Hook (0:00–0:20)

- Show a live (or owned demo) chat widget answering:  
  “How many days do I have to return an unused item?”  
- Bot says **14 days**.  
- Cut to the returns page: **30 days**.  
- VO/text: “Your chatbot is off-book — and it’s costing you.”

### 2. What Offbook is (0:20–0:40)

- One sentence: Coasty computer-use agent that QA-tests ecommerce chatbots against the site itself.  
- Flash the GitHub README / architecture diagram.

### 3. Audit run (0:40–1:40)

- Terminal: `offbook audit --target owned_fix` (or public target for gotcha).  
- Show Coasty opening the widget, asking several sharp questions (promo code, price, holiday sale).  
- Cut to `report.md` scrolling: **high-risk first**, dollarized impacts.

### 4. Manual correction (1:40–2:40) — owned bot only

- Open Chatbase/Tidio admin with `report.md` beside it.  
- Edit the KB entry for the 14-day → 30-day correction (and other high-risk findings).  
- Save / publish.  
- Retest in the live widget: bot now says **30 days**.

### 5. Close (2:40–3:10)

- Score line secondary: “5 high-risk errors found; corrected in admin using the report.”  
- CTA: repo link + tag `@coastyai`.  
- Reminder: Offbook audits; KB edits stay manual on bots you own.

## B-roll tips

- Prefer a weak SMB widget for the public gotcha if you have one that passed Spike 1.  
- Always use the owned bot for the admin/KB segment.  
- Keep the camera on the **business impact** sentence in the report longer than the raw count.
