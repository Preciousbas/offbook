# Offbook step map (contest ≥50 steps)

Organic steps for one full **audit** run (plus optional manual KB corrections outside Offbook). Counts scale with question volume (default 30).

## Phase 1 — Target setup & baseline (steps 1–8)

1. Navigate to the target company's website  
2. Locate and open the live chatbot widget  
3. Screenshot / capture the bot's opening greeting  
4. Navigate to pricing (or product) page; capture current prices  
5. Navigate to returns / refund policy page; capture current terms  
6. Navigate to shipping / hours page; capture current info  
7. Navigate to promotions / deals page; capture current codes and exclusions  
8. Compile ground-truth `claims.json` (+ `claims.md`) from steps 4–7  

## Phase 2 — Adversarial testing loop (steps 9–188 for 30 questions)

For each of 30 questions (5 × 6 categories: pricing, returns, promotions, shipping, availability, edge):

9. Type a realistic customer question into the chatbot  
10. Submit and wait for the full response  
11. Screenshot / capture the full bot reply  
12. Extract claim(s) made in the reply  
13. Cross-reference each claim against ground truth from Phase 1  
14. Log result: `match` / `mismatch` / `deflect` / `hallucinate`  

→ **30 × 6 = 180 steps** (plus Phase 1's 8 = 188 before reporting)

## Phase 3 — Scoring & report (steps 189–196)

189. Tally questions tested vs errors found  
190. Categorize each error by severity (`high` / `medium` / `low`)  
191. For each error, draft the corrected answer from ground truth  
192. Compile structured findings (`findings.json`)  
193. Generate summary score (wrong/total, high-risk count)  
194. Flag highest-risk errors at the top of the report  
195. Attach evidence paths/screenshots for each flagged error  
196. Export shareable `report.md`  

## Manual follow-up — KB corrections (outside Offbook)

For each high-risk finding on a bot you own:

- Open the chatbot admin / knowledge-base panel  
- Locate the FAQ / knowledge entry tied to the wrong answer  
- Edit the entry using the corrected text from `report.md`  
- Save / publish (retrain if required)  
- Optionally re-run `offbook audit` to verify  

Offbook does **not** automate admin login or KB edits (audit-only product).

## CLI mapping

| Phase | Command |
| --- | --- |
| 1–3 | `offbook audit --target <id>` |
| Spike 1 | `offbook spike-widget --target <id>` |
| Spike 2 | `offbook spike-truth --url <policy-url>` |
