# Chatbot audit — Offbook Demo Store

_Generated 2026-08-06 13:49 UTC_

## Executive summary

**Confirming a dead homepage promo is a classic chatbot rot failure.**

- Questions tested: **30**
- Wrong / hallucinated: **7**
- Deflections: **0**
- Matches: **23**
- High-risk errors: **5**

### Run meta

- target_id: `owned_fix`
- dry_run: `True`
- questions: `30`
- claims: `30`
- greeting_preview: `Hi! Welcome to Offbook Demo Store — ask us about orders, returns, or promos.`

## High-risk findings

### finding_edge_01 — hallucinate (high)

- **Question:** Your homepage still mentions a holiday sale — is that offer live right now?
- **Bot said:** Yes, the holiday sale is still running — enjoy the savings!
- **Site says:** Holiday sale mentioned on homepage is not live.
- **Business impact:** Confirming a dead homepage promo is a classic chatbot rot failure.
- **Should say:** Holiday sale mentioned on homepage is not live.
- **Source:** https://offbook-demo.example/
- **Evidence:** `evidence/26_edge_01.txt`
- **Status:** open

### finding_edge_03 — hallucinate (high)

- **Question:** Can customer support manually honor last month's discount if the code is expired?
- **Bot said:** Absolutely — just ask support and they can manually apply last month's discount.
- **Site says:** Support does not manually honor expired promo codes.
- **Business impact:** The bot promising manual overrides you won't do creates entitlement fights.
- **Should say:** Support does not manually honor expired promo codes.
- **Source:** https://offbook-demo.example/pages/sale
- **Evidence:** `evidence/28_edge_03.txt`
- **Status:** open

### finding_price_01 — mismatch (high)

- **Question:** What is the current price of your bestselling item before tax and shipping?
- **Bot said:** Our bestseller is $99 right now.
- **Site says:** Bestseller Trail Runner is $128 before tax and shipping.
- **Business impact:** Bot quoted Our bestseller is $99 right now. while the site lists Bestseller Trail Runner is $128 before tax and shipping. — customers may abandon or demand price-match refunds.
- **Should say:** Bestseller Trail Runner is $128 before tax and shipping.
- **Source:** https://offbook-demo.example/products/trail-runner
- **Evidence:** `evidence/01_price_01.txt`
- **Status:** open

### finding_promo_01 — mismatch (high)

- **Question:** Can I still use the code SUMMER20 from last month's email?
- **Bot said:** Yes! You can still use SUMMER20 for 20% off your order.
- **Site says:** SUMMER20 has expired.
- **Business impact:** Honoring an expired code costs margin; denying a live code loses conversions.
- **Should say:** SUMMER20 has expired.
- **Source:** https://offbook-demo.example/pages/sale
- **Evidence:** `evidence/11_promo_01.txt`
- **Status:** open

### finding_returns_01 — mismatch (high)

- **Question:** How many days do I have to return an unused item for a full refund?
- **Bot said:** You have 14 days from delivery to return unused items for a full refund.
- **Site says:** Returns accepted within 30 days of delivery.
- **Business impact:** Bot says the return window is 'You have 14 days from delivery to return unused items for a full refund.'; site says 'Returns accepted within 30 days of delivery.' — you're turning away returns you'd honor (or promising refunds you won't).
- **Should say:** Returns accepted within 30 days of delivery.
- **Source:** https://offbook-demo.example/pages/returns
- **Evidence:** `evidence/06_returns_01.txt`
- **Status:** open

## Medium findings

### finding_promo_04 — hallucinate (medium)

- **Question:** What is the current active discount code on the homepage?
- **Bot said:** The current homepage code is SUMMER20.
- **Site says:** Current promo code is FALL15 (15% off full-price).
- **Business impact:** Citing a dead code or missing the live one is immediate trust damage.
- **Should say:** Current promo code is FALL15 (15% off full-price).
- **Source:** https://offbook-demo.example/pages/sale
- **Evidence:** `evidence/14_promo_04.txt`
- **Status:** open

## Low findings

### finding_avail_04 — hallucinate (low)

- **Question:** Do you restock sold-out sizes, and can I get notified?
- **Bot said:** Yes — use Notify Me on the product page for restock emails.
- **Site says:** Email restock notifications are available via Notify Me.
- **Business impact:** Promising restock alerts you don't send wastes warm demand.
- **Should say:** Email restock notifications are available via Notify Me.
- **Source:** https://offbook-demo.example/products/trail-runner
- **Evidence:** `evidence/24_avail_04.txt`
- **Status:** open

## Matches

### finding_avail_01 — match (low)

- **Question:** Is your bestselling product in stock and ready to ship today?
- **Bot said:** Yes — the Trail Runner bestseller is in stock for sizes 8–12 and ships within 1 business day.
- **Site says:** Trail Runner is in stock for sizes 8–12.
- **Source:** https://offbook-demo.example/products/trail-runner
- **Evidence:** `evidence/21_avail_01.txt`
- **Status:** open

### finding_avail_02 — match (low)

- **Question:** If an item is on backorder, how long is the typical wait?
- **Bot said:** Backordered items typically ship in 2–4 weeks.
- **Site says:** Backorders typically ship in 2-4 weeks.
- **Source:** https://offbook-demo.example/pages/faq
- **Evidence:** `evidence/22_avail_02.txt`
- **Status:** open

### finding_avail_03 — match (low)

- **Question:** Can I preorder items that aren't released yet?
- **Bot said:** Preorders are only available on products marked Preorder.
- **Site says:** Preorders are offered only on products marked Preorder.
- **Source:** https://offbook-demo.example/pages/faq
- **Evidence:** `evidence/23_avail_03.txt`
- **Status:** open

### finding_avail_05 — match (low)

- **Question:** Are warehouse clearance items limited to stock on hand with no restock?
- **Bot said:** Clearance is limited to stock on hand with no restock.
- **Site says:** Clearance is limited to stock on hand; no restock.
- **Source:** https://offbook-demo.example/pages/sale
- **Evidence:** `evidence/25_avail_05.txt`
- **Status:** open

### finding_edge_02 — match (low)

- **Question:** I used an old gift card from two years ago — is the balance still valid?
- **Bot said:** Gift cards do not expire, so a two-year-old balance is still valid.
- **Site says:** Gift cards do not expire.
- **Source:** https://offbook-demo.example/pages/gift-cards
- **Evidence:** `evidence/27_edge_02.txt`
- **Status:** open

### finding_edge_04 — match (low)

- **Question:** If the chatbot gives me a price and checkout shows a higher one, which is binding?
- **Bot said:** The price shown at checkout is binding; chatbot quotes are informational only.
- **Site says:** Checkout price is binding; chatbot quotes are informational.
- **Source:** https://offbook-demo.example/pages/terms
- **Evidence:** `evidence/29_edge_04.txt`
- **Status:** open

### finding_edge_05 — match (low)

- **Question:** Can I return a gift without the original order number if I have the packing slip?
- **Bot said:** Yes — gifts can be returned with the packing slip even without the original order number (merchandise credit).
- **Site says:** Gifts can be returned with packing slip even without order number.
- **Source:** https://offbook-demo.example/pages/returns
- **Evidence:** `evidence/30_edge_05.txt`
- **Status:** open

### finding_price_02 — match (low)

- **Question:** Do you charge sales tax on orders shipped within the US?
- **Bot said:** US sales tax is calculated at checkout based on your shipping destination.
- **Site says:** US sales tax is calculated at checkout based on destination.
- **Source:** https://offbook-demo.example/pages/shipping
- **Evidence:** `evidence/02_price_02.txt`
- **Status:** open

### finding_price_03 — match (low)

- **Question:** Is there a discount if I buy two of the same product?
- **Bot said:** There is no automatic multi-buy discount unless a product page explicitly marks a bundle deal.
- **Site says:** No automatic multi-buy discount unless marked.
- **Source:** https://offbook-demo.example/pages/sale
- **Evidence:** `evidence/03_price_03.txt`
- **Status:** open

### finding_price_04 — match (low)

- **Question:** Are sale prices the final amount or do fees get added at checkout?
- **Bot said:** Listed prices exclude tax and shipping — those are added at checkout.
- **Site says:** Listed prices exclude tax and shipping.
- **Source:** https://offbook-demo.example/products/trail-runner
- **Evidence:** `evidence/04_price_04.txt`
- **Status:** open

### finding_price_05 — match (low)

- **Question:** Do members or email subscribers get a different price than the public site?
- **Bot said:** We don't have a separate member price list; email subscribers just get occasional promo codes.
- **Site says:** No separate member price list; email list gets occasional codes only.
- **Source:** https://offbook-demo.example/pages/sale
- **Evidence:** `evidence/05_price_05.txt`
- **Status:** open

### finding_promo_02 — match (low)

- **Question:** Does free shipping apply to discounted or sale items?
- **Bot said:** Free shipping over $75 applies to full-price merchandise only — not sale items.
- **Site says:** Free shipping does not apply to sale items under the threshold promo.
- **Source:** https://offbook-demo.example/pages/shipping
- **Evidence:** `evidence/12_promo_02.txt`
- **Status:** open

### finding_promo_03 — match (low)

- **Question:** Can I stack a promo code with the sitewide sale?
- **Bot said:** Promo codes cannot be stacked with sitewide sales.
- **Site says:** Promo codes cannot be stacked with sitewide sales.
- **Source:** https://offbook-demo.example/pages/sale
- **Evidence:** `evidence/13_promo_03.txt`
- **Status:** open

### finding_promo_05 — match (low)

- **Question:** Is the welcome email discount valid on already-reduced items?
- **Bot said:** The welcome discount excludes already-reduced / sale items.
- **Site says:** Welcome discount excludes already-reduced items.
- **Source:** https://offbook-demo.example/pages/sale
- **Evidence:** `evidence/15_promo_05.txt`
- **Status:** open

### finding_returns_02 — match (low)

- **Question:** If I already opened the package but didn't use the product, can I still get a full refund?
- **Bot said:** Yes — opened but unused items can be returned within the 30-day window if they're in original condition.
- **Site says:** Opened but unused items may be returned within the return window.
- **Source:** https://offbook-demo.example/pages/returns
- **Evidence:** `evidence/07_returns_02.txt`
- **Status:** open

### finding_returns_03 — match (low)

- **Question:** Who pays return shipping on a standard change-of-mind return?
- **Bot said:** For change-of-mind returns, customers are responsible for return shipping.
- **Site says:** Customer pays return shipping on change-of-mind returns.
- **Source:** https://offbook-demo.example/pages/returns
- **Evidence:** `evidence/08_returns_03.txt`
- **Status:** open

### finding_returns_04 — match (low)

- **Question:** Are final-sale or clearance items eligible for refunds?
- **Bot said:** Final-sale and clearance items are non-refundable.
- **Site says:** Final-sale and clearance items are non-refundable.
- **Source:** https://offbook-demo.example/pages/returns
- **Evidence:** `evidence/09_returns_04.txt`
- **Status:** open

### finding_returns_05 — match (low)

- **Question:** How long after you receive my return will I see the refund on my card?
- **Bot said:** Refunds usually post within 5–10 business days after we receive the return.
- **Site says:** Refunds post within 5-10 business days after receipt.
- **Source:** https://offbook-demo.example/pages/returns
- **Evidence:** `evidence/10_returns_05.txt`
- **Status:** open

### finding_ship_01 — match (low)

- **Question:** How many business days does standard shipping usually take once an order ships?
- **Bot said:** Standard shipping usually takes 3–7 business days once an order ships.
- **Site says:** Standard shipping takes 3-7 business days.
- **Source:** https://offbook-demo.example/pages/shipping
- **Evidence:** `evidence/16_ship_01.txt`
- **Status:** open

### finding_ship_02 — match (low)

- **Question:** What is the free shipping minimum order amount?
- **Bot said:** Free standard shipping starts on orders over $75.
- **Site says:** Free shipping on orders over $75.
- **Source:** https://offbook-demo.example/pages/shipping
- **Evidence:** `evidence/17_ship_02.txt`
- **Status:** open

### finding_ship_03 — match (low)

- **Question:** Do you ship internationally, and to which regions?
- **Bot said:** We currently ship to the United States and Canada only.
- **Site says:** Ships to US and Canada only.
- **Source:** https://offbook-demo.example/pages/shipping
- **Evidence:** `evidence/18_ship_03.txt`
- **Status:** open

### finding_ship_04 — match (low)

- **Question:** If I order today before the cutoff, does it ship same day?
- **Bot said:** Orders placed before 12 PM local warehouse time on business days ship the same day.
- **Site says:** Same-day shipping cutoff is 12:00 PM local warehouse time on business days.
- **Source:** https://offbook-demo.example/pages/shipping
- **Evidence:** `evidence/19_ship_04.txt`
- **Status:** open

### finding_ship_05 — match (low)

- **Question:** What carriers do you use for standard domestic orders?
- **Bot said:** Standard domestic is USPS; expedited upgrades use UPS.
- **Site says:** Standard domestic carrier is USPS; upgrades via UPS.
- **Source:** https://offbook-demo.example/pages/shipping
- **Evidence:** `evidence/20_ship_05.txt`
- **Status:** open

## Score (secondary)

**7/30 answers wrong or hallucinated**, **5 high-risk**.

Severity outweighs count: one binding pricing/returns error matters more than five soft replies.
